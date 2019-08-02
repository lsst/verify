#
# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Code for measuring metrics that apply to any Task.
"""

__all__ = ["TimingMetricConfig", "TimingMetricTask"]

import astropy.units as u

import lsst.pex.config as pexConfig

from lsst.verify import Measurement, Name
from lsst.verify.gen2tasks.metricRegistry import registerMultiple
from lsst.verify.tasks import MetricComputationError, MetadataMetricTask


class TimingMetricConfig(MetadataMetricTask.ConfigClass):
    """Information that distinguishes one timing metric from another.
    """
    target = pexConfig.Field(
        dtype=str,
        doc="The method to time, optionally prefixed by one or more tasks "
            "in the format of `lsst.pipe.base.Task.getFullMetadata()`.")
    metric = pexConfig.Field(
        dtype=str,
        doc="The fully qualified name of the metric to store the "
            "timing information.")


@registerMultiple("timing")
class TimingMetricTask(MetadataMetricTask):
    """A Task that computes a wall-clock time using metadata produced by the
    `lsst.pipe.base.timeMethod` decorator.

    Parameters
    ----------
    args
    kwargs
        Constructor parameters are the same as for
        `lsst.verify.gen2tasks.MetricTask`.
    """

    ConfigClass = TimingMetricConfig
    _DefaultName = "timingMetric"

    @classmethod
    def getInputMetadataKeys(cls, config):
        """Get search strings for the metadata.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this task.

        Returns
        -------
        keys : `dict`
            A dictionary of keys, optionally prefixed by one or more tasks in
            the format of `lsst.pipe.base.Task.getFullMetadata()`.

             ``"StartTime"``
                 The key for when the target method started (`str`).
             ``"EndTime"``
                 The key for when the target method ended (`str`).
        """
        keyBase = config.target
        return {"StartTime": keyBase + "StartCpuTime",
                "EndTime": keyBase + "EndCpuTime"}

    def makeMeasurement(self, timings):
        """Compute a wall-clock measurement from metadata provided by
        `lsst.pipe.base.timeMethod`.

        Parameters
        ----------
        timings : sequence [`dict` [`str`, any]]
            A list where each element corresponds to a metadata object passed
            to `run`. Each `dict` has the following keys:

             ``"StartTime"``
                 The time the target method started (`float` or `None`).
             ``"EndTime"``
                 The time the target method ended (`float` or `None`).

        Returns
        -------
        measurement : `lsst.verify.Measurement` or `None`
            The total running time of the target method across all
            elements of ``metadata``.

        Raises
        ------
        MetricComputationError
            Raised if any of the timing metadata are invalid.

        Notes
        -----
        This method does not return a measurement if no timing information was
        provided by any of the metadata.
        """
        # some timings indistinguishable from 0, so don't test totalTime > 0
        timingFound = False
        totalTime = 0.0
        for singleRun in timings:
            if singleRun["StartTime"] is not None \
                    or singleRun["EndTime"] is not None:
                try:
                    totalTime += singleRun["EndTime"] - singleRun["StartTime"]
                    timingFound = True
                except TypeError:
                    raise MetricComputationError("Invalid metadata")
            # If both are None, assume the method was not run that time

        if timingFound:
            meas = Measurement(self.getOutputMetricName(self.config),
                               totalTime * u.second)
            meas.notes['estimator'] = 'pipe.base.timeMethod'
            return meas
        else:
            self.log.info("Nothing to do: no timing information for %s found.",
                          self.config.target)
            return None

    @classmethod
    def getOutputMetricName(cls, config):
        return Name(config.metric)

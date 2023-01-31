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

__all__ = ["TimingMetricConfig", "TimingMetricTask",
           "CpuTimingMetricConfig", "CpuTimingMetricTask",
           "MemoryMetricConfig", "MemoryMetricTask",
           ]

from datetime import datetime
import resource
import sys

import astropy.units as u

import lsst.pex.config as pexConfig
from lsst.pipe.base import NoWorkFound

from lsst.verify import Measurement, Datum
from lsst.verify.tasks import MetricComputationError, MetadataMetricTask, \
    MetadataMetricConfig


class TimeMethodMetricConfig(MetadataMetricConfig):
    """Common config fields for metrics based on
    `~lsst.utils.timer.timeMethod`.

    These fields let metrics distinguish between different methods that have
    been decorated with `~lsst.utils.timer.timeMethod`.
    """
    target = pexConfig.Field(
        dtype=str,
        doc="The method to profile, optionally prefixed by one or more tasks "
            "in the format of `lsst.pipe.base.Task.getFullMetadata()`.")


# Expose TimingMetricConfig name because config-writers expect it
TimingMetricConfig = TimeMethodMetricConfig


class TimingMetricTask(MetadataMetricTask):
    """A Task that computes a wall-clock time using metadata produced by the
    `lsst.utils.timer.timeMethod` decorator.

    Parameters
    ----------
    args
    kwargs
        Constructor parameters are the same as for
        `lsst.verify.tasks.MetricTask`.
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

             ``"StartTimestamp"``
                 The key for an ISO 8601-compliant text string where the target
                 method started (`str`).
             ``"EndTimestamp"``
                 The key for an ISO 8601-compliant text string where the target
                 method ended (`str`).
        """
        keyBase = config.target
        return {"StartTimestamp": keyBase + "StartUtc",
                "EndTimestamp": keyBase + "EndUtc",
                }

    def makeMeasurement(self, timings):
        """Compute a wall-clock measurement from metadata provided by
        `lsst.utils.timer.timeMethod`.

        Parameters
        ----------
        timings : `dict` [`str`, any]
            A representation of the metadata passed to `run`. The `dict` has
            the following keys:

             ``"StartTimestamp"``
                 The time the target method started, in an ISO 8601-compliant
                 format (`str` or `None`).
             ``"EndTimestamp"``
                 The time the target method ended, in an ISO 8601-compliant
                 format (`str` or `None`).

        Returns
        -------
        measurement : `lsst.verify.Measurement`
            The running time of the target method.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if the timing metadata are invalid.
        lsst.pipe.base.NoWorkFound
            Raised if no matching timing metadata found.
        """
        # Use or, not and, so that unpaired keys raise MetricComputationError.
        if timings["StartTimestamp"] is not None or timings["EndTimestamp"] is not None:
            try:
                startTime = datetime.fromisoformat(timings["StartTimestamp"])
                endTime = datetime.fromisoformat(timings["EndTimestamp"])
            except (TypeError, ValueError):
                raise MetricComputationError("Invalid metadata")
            else:
                totalTime = (endTime - startTime).total_seconds()
                meas = Measurement(self.config.metricName,
                                   totalTime * u.second)
                meas.notes["estimator"] = "utils.timer.timeMethod"
                meas.extras["start"] = Datum(timings["StartTimestamp"])
                meas.extras["end"] = Datum(timings["EndTimestamp"])
                return meas
        else:
            raise NoWorkFound(f"Nothing to do: no timing information for {self.config.target} found.")


# Expose CpuTimingMetricConfig name because config-writers expect it
CpuTimingMetricConfig = TimeMethodMetricConfig


class CpuTimingMetricTask(MetadataMetricTask):
    """A Task that computes a CPU time using metadata produced by the
    `lsst.utils.timer.timeMethod` decorator.

    Parameters
    ----------
    args
    kwargs
        Constructor parameters are the same as for
        `lsst.verify.tasks.MetricTask`.
    """

    ConfigClass = CpuTimingMetricConfig
    _DefaultName = "cpuTimingMetric"

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
             ``"StartTimestamp"``
                 The key for an ISO 8601-compliant text string where the target
                 method started (`str`).
             ``"EndTimestamp"``
                 The key for an ISO 8601-compliant text string where the target
                 method ended (`str`).
        """
        keyBase = config.target
        return {"StartTime": keyBase + "StartCpuTime",
                "EndTime": keyBase + "EndCpuTime",
                "StartTimestamp": keyBase + "StartUtc",
                "EndTimestamp": keyBase + "EndUtc",
                }

    def makeMeasurement(self, timings):
        """Compute a wall-clock measurement from metadata provided by
        `lsst.utils.timer.timeMethod`.

        Parameters
        ----------
        timings : `dict` [`str`, any]
            A representation of the metadata passed to `run`. The `dict` has
            the following keys:

             ``"StartTime"``
                 The time the target method started (`float` or `None`).
             ``"EndTime"``
                 The time the target method ended (`float` or `None`).
             ``"StartTimestamp"``, ``"EndTimestamp"``
                 The start and end timestamps, in an ISO 8601-compliant format
                 (`str` or `None`).

        Returns
        -------
        measurement : `lsst.verify.Measurement`
            The running time of the target method.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if the timing metadata are invalid.
        lsst.pipe.base.NoWorkFound
            Raised if no matching timing metadata found.
        """
        # Use or, not and, so that unpaired keys raise MetricComputationError.
        if timings["StartTime"] is not None or timings["EndTime"] is not None:
            try:
                totalTime = timings["EndTime"] - timings["StartTime"]
            except TypeError:
                raise MetricComputationError("Invalid metadata")
            else:
                meas = Measurement(self.config.metricName,
                                   totalTime * u.second)
                meas.notes["estimator"] = "utils.timer.timeMethod"
                if timings["StartTimestamp"]:
                    meas.extras["start"] = Datum(timings["StartTimestamp"])
                if timings["EndTimestamp"]:
                    meas.extras["end"] = Datum(timings["EndTimestamp"])
                return meas
        else:
            raise NoWorkFound(f"Nothing to do: no timing information for {self.config.target} found.")


# Expose MemoryMetricConfig name because config-writers expect it
MemoryMetricConfig = TimeMethodMetricConfig


class MemoryMetricTask(MetadataMetricTask):
    """A Task that computes the maximum resident set size using metadata
    produced by the `lsst.utils.timer.timeMethod` decorator.

    Parameters
    ----------
    args
    kwargs
        Constructor parameters are the same as for
        `lsst.verify.tasks.MetricTask`.
    """

    ConfigClass = MemoryMetricConfig
    _DefaultName = "memoryMetric"

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

             ``"EndMemory"``
                 The key for the memory usage at the end of the method (`str`).
             ``"MetadataVersion"``
                 The key for the task-level metadata version.
        """
        keyBase = config.target
        # Parse keyBase to get just the task prefix, if any; needed to
        # guarantee that returned keys all point to unique entries.
        # The following line returns a "."-terminated string if keyBase has a
        # task prefix, and "" otherwise.
        taskPrefix = "".join(keyBase.rpartition(".")[0:2])

        return {"EndMemory": keyBase + "EndMaxResidentSetSize",
                "MetadataVersion": taskPrefix + "__version__",
                }

    def makeMeasurement(self, memory):
        """Compute a maximum resident set size measurement from metadata
        provided by `lsst.utils.timer.timeMethod`.

        Parameters
        ----------
        memory : `dict` [`str`, any]
            A representation of the metadata passed to `run`. Each `dict` has
            the following keys:

             ``"EndMemory"``
                 The memory usage at the end of the method (`int` or `None`).
             ``"MetadataVersion"``
                 The version of the task metadata in which the value was stored
                 (`int` or `None`). `None` is assumed to be version 0.

        Returns
        -------
        measurement : `lsst.verify.Measurement`
            The maximum memory usage of the target method.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if the memory metadata are invalid.
        lsst.pipe.base.NoWorkFound
            Raised if no matching memory metadata found.
        """
        if memory["EndMemory"] is not None:
            try:
                maxMemory = int(memory["EndMemory"])
                version = memory["MetadataVersion"] \
                    if memory["MetadataVersion"] else 0
            except (ValueError, TypeError) as e:
                raise MetricComputationError("Invalid metadata") from e
            else:
                meas = Measurement(self.config.metricName,
                                   self._addUnits(maxMemory, version))
                meas.notes['estimator'] = 'utils.timer.timeMethod'
                return meas
        else:
            raise NoWorkFound(f"Nothing to do: no memory information for {self.config.target} found.")

    def _addUnits(self, memory, version):
        """Represent memory usage in correct units.

        Parameters
        ----------
        memory : `int`
            The memory usage as returned by `resource.getrusage`, in
            platform-dependent units.
        version : `int`
            The metadata version. If ``0``, ``memory`` is in platform-dependent
            units. If ``1`` or greater, ``memory`` is in bytes.

        Returns
        -------
        memory : `astropy.units.Quantity`
            The memory usage in absolute units.
        """
        if version >= 1:
            return memory * u.byte
        elif sys.platform.startswith('darwin'):
            # MacOS uses bytes
            return memory * u.byte
        elif sys.platform.startswith('sunos') \
                or sys.platform.startswith('solaris'):
            # Solaris and SunOS use pages
            return memory * resource.getpagesize() * u.byte
        else:
            # Assume Linux, which uses kibibytes
            return memory * u.kibibyte

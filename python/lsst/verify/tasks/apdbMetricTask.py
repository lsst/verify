# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["ApdbMetricTask", "ApdbMetricConfig", "ApdbMetricConnections"]

import abc

from lsst.pex.config import Field
from lsst.pipe.base import NoWorkFound, Struct, connectionTypes
from lsst.dax.apdb import Apdb

from lsst.verify.tasks import MetricTask, MetricConfig, MetricConnections


class ApdbMetricConnections(
        MetricConnections,
        dimensions={"instrument"},
):
    """An abstract connections class defining a database input.

    Notes
    -----
    ``ApdbMetricConnections`` defines the following dataset templates:
        ``package``
            Name of the metric's namespace. By
            :ref:`verify_metrics <verify-metrics-package>` convention, this is
            the name of the package the metric is most closely
            associated with.
        ``metric``
            Name of the metric, excluding any namespace.
    """
    dbInfo = connectionTypes.Input(
        name="apdb_marker",
        doc="The dataset(s) indicating that AP processing has finished for a "
            "given data ID.",
        storageClass="Config",
        multiple=True,
        minimum=1,
        dimensions={"instrument", "visit", "detector"},
    )
    # Replaces MetricConnections.measurement, which is detector-level
    measurement = connectionTypes.Output(
        name="metricvalue_{package}_{metric}",
        doc="The metric value computed by this task.",
        storageClass="MetricValue",
        dimensions={"instrument"},
    )


class ApdbMetricConfig(MetricConfig,
                       pipelineConnections=ApdbMetricConnections):
    """A base class for APDB metric task configs.
    """
    apdb_config_url = Field(
        dtype=str,
        default=None,
        optional=False,
        doc="A config file specifying the APDB and its connection parameters, "
            "typically written by the apdb-cli command-line utility.",
    )


class ApdbMetricTask(MetricTask):
    """A base class for tasks that compute metrics from an alert production
    database.

    Parameters
    ----------
    **kwargs
        Constructor parameters are the same as for
        `lsst.pipe.base.PipelineTask`.

    Notes
    -----
    This class should be customized by overriding `makeMeasurement`. You
    should not need to override `run`.
    """
    ConfigClass = ApdbMetricConfig

    @abc.abstractmethod
    def makeMeasurement(self, dbHandle, outputDataId):
        """Compute the metric from database data.

        Parameters
        ----------
        dbHandle : `lsst.dax.apdb.Apdb`
            A database instance.
        outputDataId : any data ID type
            The subset of the database to which this measurement applies.
            May be empty to represent the entire dataset.

        Returns
        -------
        measurement : `lsst.verify.Measurement` or `None`
            The measurement corresponding to the input data.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if an algorithmic or system error prevents calculation of
            the metric. See `run` for expected behavior.
        lsst.pipe.base.NoWorkFound
            Raised if the metric is ill-defined or otherwise inapplicable to
            the database state. Typically this means that the pipeline step or
            option being measured was not run.
        """

    def run(self, dbInfo, outputDataId={}):
        """Compute a measurement from a database.

        Parameters
        ----------
        dbInfo : `list`
            The datasets (of the type indicated by the config) from
            which to load the database. If more than one dataset is provided
            (as may be the case if DB writes are fine-grained), all are
            assumed identical.
        outputDataId: any data ID type, optional
            The output data ID for the metric value. Defaults to the empty ID,
            representing a value that covers the entire dataset.

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            Result struct with component:

            ``measurement``
                the value of the metric (`lsst.verify.Measurement` or `None`)

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if an algorithmic or system error prevents calculation of
            the metric.
        lsst.pipe.base.NoWorkFound
            Raised if the metric is ill-defined or otherwise inapplicable to
            the database state. Typically this means that the pipeline step or
            option being measured was not run.

        Notes
        -----
        This implementation calls
        `~lsst.verify.tasks.ApdbMetricConfig.dbLoader` to acquire a database
        handle, then passes it and the value of
        ``outputDataId`` to `makeMeasurement`. The result of `makeMeasurement`
        is returned to the caller.
        """
        db = Apdb.from_uri(self.config.apdb_config_url)

        if db is not None:
            return Struct(measurement=self.makeMeasurement(db, outputDataId))
        else:
            raise NoWorkFound("No APDB to measure!")

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """Do Butler I/O to provide in-memory objects for run.

        This specialization of runQuantum passes the output data ID to `run`.
        """
        inputs = butlerQC.get(inputRefs)
        outputs = self.run(**inputs,
                           outputDataId=outputRefs.measurement.dataId)
        if outputs.measurement is not None:
            butlerQC.put(outputs, outputRefs)
        else:
            self.log.debug("Skipping measurement of %r on %s "
                           "as not applicable.", self, inputRefs)

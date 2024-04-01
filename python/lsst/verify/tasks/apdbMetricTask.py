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

__all__ = ["ApdbMetricTask", "ApdbMetricConfig", "ConfigApdbLoader",
           "DirectApdbLoader", "ApdbMetricConnections"]

import abc

from lsst.pex.config import Config, ConfigurableField, ConfigurableInstance, \
    ConfigDictField, ConfigChoiceField, FieldValidationError
from lsst.pipe.base import NoWorkFound, Task, Struct, connectionTypes
from lsst.dax.apdb import Apdb, ApdbConfig

from lsst.verify.tasks import MetricTask, MetricConfig, MetricConnections


class ConfigApdbLoader(Task):
    """A Task that takes a science task config and returns the corresponding
    Apdb object.

    Parameters
    ----------
    *args
    **kwargs
        Constructor parameters are the same as for `lsst.pipe.base.Task`.
    """
    _DefaultName = "configApdb"
    ConfigClass = Config

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _getApdb(self, config):
        """Extract an Apdb object from an arbitrary task config.

        Parameters
        ----------
        config : `lsst.pex.config.Config`
            A config that may contain a `lsst.dax.apdb.ApdbConfig`.
            Behavior is undefined if there is more than one such member.

        Returns
        -------
        apdb : `lsst.dax.apdb.Apdb`-like or `None`
            A `lsst.dax.apdb.Apdb` object or a drop-in replacement, or `None`
            if no `lsst.dax.apdb.ApdbConfig` is present in ``config``.
        """
        if isinstance(config, ApdbConfig):
            return Apdb.from_config(config)

        for field in config.values():
            if isinstance(field, ConfigurableInstance):
                result = self._getApdbFromConfigurableField(field)
                if result:
                    return result
            elif isinstance(field, ConfigChoiceField.instanceDictClass):
                try:
                    # can't test with hasattr because of non-standard getattr
                    field.names
                except FieldValidationError:
                    result = self._getApdb(field.active)
                else:
                    result = self._getApdbFromConfigIterable(field.active)
                if result:
                    return result
            elif isinstance(field, ConfigDictField.DictClass):
                result = self._getApdbFromConfigIterable(field.values())
                if result:
                    return result
            elif isinstance(field, Config):
                # Can't test for `ConfigField` more directly than this
                result = self._getApdb(field)
                if result:
                    return result
        return None

    def _getApdbFromConfigurableField(self, configurable):
        """Extract an Apdb object from a ConfigurableField.

        Parameters
        ----------
        configurable : `lsst.pex.config.ConfigurableInstance`
            A configurable that may contain a `lsst.dax.apdb.ApdbConfig`.

        Returns
        -------
        apdb : `lsst.dax.apdb.Apdb`-like or `None`
            A `lsst.dax.apdb.Apdb` object or a drop-in replacement, if a
            suitable config exists.
        """
        if issubclass(configurable.ConfigClass, ApdbConfig):
            return configurable.apply()
        else:
            return self._getApdb(configurable.value)

    def _getApdbFromConfigIterable(self, configDict):
        """Extract an Apdb object from an iterable of configs.

        Parameters
        ----------
        configDict: iterable of `lsst.pex.config.Config`
            A config iterable that may contain a `lsst.dax.apdb.ApdbConfig`.

        Returns
        -------
        apdb : `lsst.dax.apdb.Apdb`-like or `None`
            A `lsst.dax.apdb.Apdb` object or a drop-in replacement, if a
            suitable config exists.
        """
        for config in configDict:
            result = self._getApdb(config)
            if result:
                return result

    def run(self, config):
        """Create a database consistent with a science task config.

        Parameters
        ----------
        config : `lsst.pex.config.Config`
            A config that should contain a `lsst.dax.apdb.ApdbConfig`.
            Behavior is undefined if there is more than one such member.

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            Result struct with components:

            ``apdb``
                A database configured the same way as in ``config``, if one
                exists (`lsst.dax.apdb.Apdb` or `None`).
        """
        return Struct(apdb=self._getApdb(config))


class DirectApdbLoader(Task):
    """A Task that takes a Apdb config and returns the corresponding
    Apdb object.

    Parameters
    ----------
    *args
    **kwargs
        Constructor parameters are the same as for `lsst.pipe.base.Task`.
    """

    _DefaultName = "directApdb"
    ConfigClass = Config

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, config):
        """Create a database from a config.

        Parameters
        ----------
        config : `lsst.dax.apdb.ApdbConfig`
            A config for the database connection.

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            Result struct with components:

            ``apdb``
                A database configured the same way as in ``config``.
        """
        return Struct(apdb=(Apdb.from_config(config) if config else None))


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
        doc="The dataset from which an APDB instance can be constructed by "
            "`dbLoader`. By default this is assumed to be a marker produced "
            "by AP processing.",
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
    dbLoader = ConfigurableField(
        target=DirectApdbLoader,
        doc="Task for loading a database from `dbInfo`. Its run method must "
        "take one object of the dataset type indicated by `dbInfo` and return "
        "a Struct with an 'apdb' member."
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
    # Design note: makeMeasurement is an overrideable method rather than a
    # subtask to keep the configs for `MetricsControllerTask` as simple as
    # possible. This was judged more important than ensuring that no
    # implementation details of MetricTask can leak into
    # application-specific code.

    ConfigClass = ApdbMetricConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.makeSubtask("dbLoader")

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
        db = self.dbLoader.run(dbInfo[0]).apdb

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

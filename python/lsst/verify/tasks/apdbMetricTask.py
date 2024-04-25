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
import warnings

from deprecated.sphinx import deprecated

from lsst.pex.config import Config, ConfigurableField, Field, ConfigurableInstance, \
    ConfigDictField, ConfigChoiceField, FieldValidationError
from lsst.pipe.base import NoWorkFound, Task, Struct, connectionTypes
from lsst.dax.apdb import Apdb, ApdbConfig

from lsst.verify.tasks import MetricTask, MetricConfig, MetricConnections


@deprecated(reason="APDB loaders have been replaced by ``ApdbMetricConfig.apdb_config_url``. "
                   "Will be removed after v28.",
            version="v28.0", category=FutureWarning)
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


# TODO: remove on DM-43419
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
        doc="The dataset(s) indicating that AP processing has finished for a "
            "given data ID. If ``config.doReadMarker`` is set, the datasets "
            "are also used by ``dbLoader`` to construct an Apdb object.",
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
    dbLoader = ConfigurableField(  # TODO: remove on DM-43419
        target=DirectApdbLoader,
        doc="Task for loading a database from ``dbInfo``. Its run method must "
        "take one object of the dataset type indicated by ``dbInfo`` and return "
        "a Struct with an 'apdb' member. Ignored if ``doReadMarker`` is unset.",
        deprecated="This field has been replaced by ``apdb_config_url``; set "
                   "``doReadMarker=False`` to use it. Will be removed after v28.",
    )
    apdb_config_url = Field(
        dtype=str,
        default=None,
        optional=False,
        doc="A config file specifying the APDB and its connection parameters, "
            "typically written by the apdb-cli command-line utility.",
    )
    doReadMarker = Field(  # TODO: remove on DM-43419
        dtype=bool,
        default=True,
        doc="Use the ``dbInfo`` input to set up the APDB, instead of the new "
            "config (``apdb_config_url``). This field is provided for "
            "backward-compatibility ONLY and will be removed without notice "
            "after v28.",
    )

    # TODO: remove on DM-43419
    def validate(self):
        # Sidestep Config.validate to avoid validating uninitialized
        # fields we're not using.
        skip = {"apdb_config_url"} if self.doReadMarker else set()
        for name, field in self._fields.items():
            if name not in skip:
                field.validate(self)

        # Copied from MetricConfig.validate
        if "." in self.connections.package:
            raise ValueError(f"package name {self.connections.package} must "
                             "not contain periods")
        if "." in self.connections.metric:
            raise ValueError(f"metric name {self.connections.metric} must "
                             "not contain periods; use connections.package "
                             "instead")

        if self.doReadMarker:
            warnings.warn("The encoding of config information in apdbMarker is "
                          "deprecated, replaced by ``apdb_config_url``; set "
                          "``doReadMarker=False`` to use it. ``apdb_config_url`` "
                          "will be required after v28.",
                          FutureWarning)


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

        if self.config.doReadMarker:
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
        if self.config.doReadMarker:
            db = self.dbLoader.run(dbInfo[0]).apdb
        else:
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

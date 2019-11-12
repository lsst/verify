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

__all__ = ["ApdbMetricTask", "ApdbMetricConfig", "ConfigApdbLoader"]

import abc

from lsst.pex.config import Config, ConfigurableField, ConfigurableInstance, \
    ConfigDictField, ConfigChoiceField, FieldValidationError
from lsst.pipe.base import Task, Struct, PipelineTaskConnections, \
    connectionTypes
from lsst.dax.apdb import Apdb, ApdbConfig

from lsst.verify.tasks import MetricTask


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
        """Extract a Apdb object from an arbitrary task config.

        Parameters
        ----------
        config : `lsst.pex.config.Config` or `None`
            A config that may contain a `lsst.dax.apdb.ApdbConfig`.
            Behavior is undefined if there is more than one such member.

        Returns
        -------
        apdb : `lsst.dax.apdb.Apdb`-like or `None`
            A `lsst.dax.apdb.Apdb` object or a drop-in replacement, or `None`
            if no `lsst.dax.apdb.ApdbConfig` is present in ``config``.
        """
        if config is None:
            return None
        if isinstance(config, ApdbConfig):
            return Apdb(config)

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
        """Extract a Apdb object from a ConfigurableField.

        Parameters
        ----------
        configurable : `lsst.pex.config.ConfigurableInstance` or `None`
            A configurable that may contain a `lsst.dax.apdb.ApdbConfig`.

        Returns
        -------
        apdb : `lsst.dax.apdb.Apdb`-like or `None`
            A `lsst.dax.apdb.Apdb` object or a drop-in replacement, if a
            suitable config exists.
        """
        if configurable is None:
            return None

        if configurable.ConfigClass == ApdbConfig:
            return configurable.apply()
        else:
            return self._getApdb(configurable.value)

    def _getApdbFromConfigIterable(self, configDict):
        """Extract a Apdb object from an iterable of configs.

        Parameters
        ----------
        configDict: iterable of `lsst.pex.config.Config` or `None`
            A config iterable that may contain a `lsst.dax.apdb.ApdbConfig`.

        Returns
        -------
        apdb : `lsst.dax.apdb.Apdb`-like or `None`
            A `lsst.dax.apdb.Apdb` object or a drop-in replacement, if a
            suitable config exists.
        """
        if configDict:
            for config in configDict:
                result = self._getApdb(config)
                if result:
                    return result
        return None

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


class ApdbMetricConnections(
        PipelineTaskConnections,
        dimensions=set(),
        defaultTemplates={"taskName": ""}):
    dbInfo = connectionTypes.Input(
        name="{taskName}_config",
        doc="The dataset from which a APDB instance can be constructed by "
            "`dbLoader`. By default this is assumed to be a top-level "
            "config, such as 'processCcd_config'.",
        storageClass="Config",
        # One config for entire CmdLineTask run
        multiple=False,
        dimensions=set(),
    )


class ApdbMetricConfig(MetricTask.ConfigClass,
                       pipelineConnections=ApdbMetricConnections):
    """A base class for APDB metric task configs.
    """
    dbLoader = ConfigurableField(
        target=ConfigApdbLoader,
        doc="Task for loading a database from `dbInfo`. Its run method must "
        "take the dataset provided by `dbInfo` and return a Struct with a "
        "'apdb' member."
    )


class ApdbMetricTask(MetricTask):
    """A base class for tasks that compute metrics from a alert production
    database.

    Parameters
    ----------
    **kwargs
        Constructor parameters are the same as for
        `lsst.pipe.base.PipelineTask`.

    Notes
    -----
    This class should be customized by overriding `makeMeasurement` and
    `getOutputMetricName`. You should not need to override `run`.
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
        MetricComputationError
            Raised if an algorithmic or system error prevents calculation of
            the metric. See `run` for expected behavior.
        """

    def run(self, dbInfo, outputDataId={}):
        """Compute a measurement from a database.

        Parameters
        ----------
        dbInfo
            The dataset (of the type indicated by the config) from
            which to load the database.
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
        MetricComputationError
            Raised if an algorithmic or system error prevents calculation of
            the metric.

        Notes
        -----
        This implementation calls
        `~lsst.verify.tasks.ApdbMetricConfig.dbLoader` to acquire a database
        handle, then passes it and the value of ``outputDataId`` to
        `makeMeasurement`. The result of `makeMeasurement` is returned to
        the caller.
        """
        db = self.dbLoader.run(dbInfo).apdb

        if db is not None:
            measurement = self.makeMeasurement(db, outputDataId)
        else:
            measurement = None

        return Struct(measurement=measurement)

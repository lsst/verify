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

__all__ = ["PpdbMetricTask", "PpdbMetricConfig", "ConfigPpdbLoader"]

import abc

from lsst.pex.config import Config, ConfigurableField, ConfigurableInstance, \
    ConfigDictField, ConfigChoiceField, FieldValidationError
from lsst.pipe.base import Task, Struct, PipelineTaskConnections, \
    connectionTypes
from lsst.dax.ppdb import Ppdb, PpdbConfig

from lsst.verify.gen2tasks import MetricTask


class ConfigPpdbLoader(Task):
    """A Task that takes a science task config and returns the corresponding
    Ppdb object.

    Parameters
    ----------
    *args
    **kwargs
        Constructor parameters are the same as for `lsst.pipe.base.Task`.
    """
    _DefaultName = "configPpdb"
    ConfigClass = Config

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _getPpdb(self, config):
        """Extract a Ppdb object from an arbitrary task config.

        Parameters
        ----------
        config : `lsst.pex.config.Config` or `None`
            A config that may contain a `lsst.dax.ppdb.PpdbConfig`.
            Behavior is undefined if there is more than one such member.

        Returns
        -------
        ppdb : `lsst.dax.ppdb.Ppdb`-like or `None`
            A `lsst.dax.ppdb.Ppdb` object or a drop-in replacement, or `None`
            if no `lsst.dax.ppdb.PpdbConfig` is present in ``config``.
        """
        if config is None:
            return None
        if isinstance(config, PpdbConfig):
            return Ppdb(config)

        for field in config.values():
            if isinstance(field, ConfigurableInstance):
                result = self._getPpdbFromConfigurableField(field)
                if result:
                    return result
            elif isinstance(field, ConfigChoiceField.instanceDictClass):
                try:
                    # can't test with hasattr because of non-standard getattr
                    field.names
                except FieldValidationError:
                    result = self._getPpdb(field.active)
                else:
                    result = self._getPpdbFromConfigIterable(field.active)
                if result:
                    return result
            elif isinstance(field, ConfigDictField.DictClass):
                result = self._getPpdbFromConfigIterable(field.values())
                if result:
                    return result
            elif isinstance(field, Config):
                # Can't test for `ConfigField` more directly than this
                result = self._getPpdb(field)
                if result:
                    return result
        return None

    def _getPpdbFromConfigurableField(self, configurable):
        """Extract a Ppdb object from a ConfigurableField.

        Parameters
        ----------
        configurable : `lsst.pex.config.ConfigurableInstance` or `None`
            A configurable that may contain a `lsst.dax.ppdb.PpdbConfig`.

        Returns
        -------
        ppdb : `lsst.dax.ppdb.Ppdb`-like or `None`
            A `lsst.dax.ppdb.Ppdb` object or a drop-in replacement, if a
            suitable config exists.
        """
        if configurable is None:
            return None

        if configurable.ConfigClass == PpdbConfig:
            return configurable.apply()
        else:
            return self._getPpdb(configurable.value)

    def _getPpdbFromConfigIterable(self, configDict):
        """Extract a Ppdb object from an iterable of configs.

        Parameters
        ----------
        configDict: iterable of `lsst.pex.config.Config` or `None`
            A config iterable that may contain a `lsst.dax.ppdb.PpdbConfig`.

        Returns
        -------
        ppdb : `lsst.dax.ppdb.Ppdb`-like or `None`
            A `lsst.dax.ppdb.Ppdb` object or a drop-in replacement, if a
            suitable config exists.
        """
        if configDict:
            for config in configDict:
                result = self._getPpdb(config)
                if result:
                    return result
        return None

    def run(self, config):
        """Create a database consistent with a science task config.

        Parameters
        ----------
        config : `lsst.pex.config.Config`
            A config that should contain a `lsst.dax.ppdb.PpdbConfig`.
            Behavior is undefined if there is more than one such member.

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            Result struct with components:

            ``ppdb``
                A database configured the same way as in ``config``, if one
                exists (`lsst.dax.ppdb.Ppdb` or `None`).
        """
        return Struct(ppdb=self._getPpdb(config))


class PpdbMetricConnections(
        PipelineTaskConnections,
        dimensions=set(),
        defaultTemplates={"taskName": ""}):
    dbInfo = connectionTypes.Input(
        name="{taskName}_config",
        doc="The dataset from which a PPDB instance can be constructed by "
            "`dbLoader`. By default this is assumed to be a top-level "
            "config, such as 'processCcd_config'.",
        storageClass="Config",
        # One config for entire CmdLineTask run
        multiple=False,
        dimensions=set(),
    )


class PpdbMetricConfig(MetricTask.ConfigClass,
                       pipelineConnections=PpdbMetricConnections):
    """A base class for PPDB metric task configs.
    """
    dbLoader = ConfigurableField(
        target=ConfigPpdbLoader,
        doc="Task for loading a database from `dbInfo`. Its run method must "
        "take the dataset provided by `dbInfo` and return a Struct with a "
        "'ppdb' member."
    )


class PpdbMetricTask(MetricTask):
    """A base class for tasks that compute metrics from a prompt products
    database.

    Parameters
    ----------
    **kwargs
        Constructor parameters are the same as for
        `lsst.pipe.base.PipelineTask`.

    Notes
    -----
    This class should be customized by overriding `makeMeasurement` and
    `getOutputMetricName`. You should not need to override `run` or
    `adaptArgsAndRun`.
    """
    # Design note: makeMeasurement is an overrideable method rather than a
    # subtask to keep the configs for `MetricsControllerTask` as simple as
    # possible. This was judged more important than ensuring that no
    # implementation details of MetricTask can leak into
    # application-specific code.

    ConfigClass = PpdbMetricConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.makeSubtask("dbLoader")

    @abc.abstractmethod
    def makeMeasurement(self, dbHandle, outputDataId):
        """Compute the metric from database data.

        Parameters
        ----------
        dbHandle : `lsst.dax.ppdb.Ppdb`
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
            the metric. See `adaptArgsAndRun` for expected behavior.
        """

    def run(self, dbInfo, outputDataId={}):
        """Compute a measurement from a database.

        Parameters
        ----------
        dbInfo
            The dataset (of the type indicated by `getInputDatasetTypes`) from
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
        `~lsst.verify.tasks.PpdbMetricConfig.dbLoader` to acquire a database
        handle, then passes it and the value of ``outputDataId`` to
        `makeMeasurement`. The result of `makeMeasurement` is returned to
        the caller.
        """
        db = self.dbLoader.run(dbInfo).ppdb

        if db is not None:
            measurement = self.makeMeasurement(db, outputDataId)
        else:
            measurement = None

        return Struct(measurement=measurement)

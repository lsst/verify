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

__all__ = ["MetricTask"]

import abc

import lsst.pipe.base as pipeBase


class MetricTask(pipeBase.Task, metaclass=abc.ABCMeta):
    """A base class for tasks that compute one metric from input datasets.

    Parameters
    ----------
    *args
    **kwargs
        Constructor parameters are the same as for
        `lsst.pipe.base.PipelineTask`.

    Notes
    -----
    In general, both the ``MetricTask``'s metric and its input data are
    configurable. Metrics may be associated with a data ID at any level of
    granularity, including repository-wide.

    Like `lsst.pipe.base.PipelineTask`, this class should be customized by
    overriding one of `run` or `adaptArgsAndRun` and by providing an
    `~lsst.pipe.base.InputDatasetField` for each parameter of `run`. For
    requirements on these methods that are specific to ``MetricTask``, see
    `adaptArgsAndRun`.

    .. note::
        The API is designed to make it easy to convert all ``MetricTasks`` to
        `~lsst.pipe.base.PipelineTask` later, but this class is *not* a
        `~lsst.pipe.base.PipelineTask` and does not work with activators,
        quanta, or `lsst.daf.butler`.
    """

    # TODO: create a specialized MetricTaskConfig once metrics have
    # Butler datasets
    ConfigClass = pipeBase.PipelineTaskConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def adaptArgsAndRun(self, inputData, inputDataIds, outputDataId):
        """Compute a metric from in-memory data.

        Parameters
        ----------
        inputData : `dict` from `str` to any
            Dictionary whose keys are the names of input parameters and values
            are Python-domain data objects (or lists of objects) retrieved
            from data butler. Input objects may be `None` to represent
            missing data.
        inputDataIds : `dict` from `str` to `list` of dataId
            Dictionary whose keys are the names of input parameters and values
            are data IDs (or lists of data IDs) that the task consumes for
            corresponding dataset type. Data IDs are guaranteed to match data
            objects in ``inputData``.
        outputDataId : `dict` from `str` to dataId
            Dictionary containing a single key, ``"measurement"``, which maps
            to a single data ID for the measurement. The data ID must have the
            same granularity as the metric.

        Returns
        -------
        struct : `lsst.pipe.base.Struct`
            A `~lsst.pipe.base.Struct` containing at least the
            following component:

            - ``measurement``: the value of the metric identified by
              `getOutputMetricName`, computed from ``inputData``
              (`lsst.verify.Measurement` or `None`). The measurement is
              guaranteed to contain not only the value of the metric, but also
              any mandatory supplementary information.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if an algorithmic or system error prevents calculation
            of the metric. Examples include corrupted input data or
            unavoidable exceptions raised by analysis code. The
            `~lsst.verify.tasks.MetricComputationError` should be chained to a
            more specific exception describing the root cause.

            Not having enough data for a metric to be applicable is not an
            error, and should not trigger this exception.

        Notes
        -----
        This implementation calls `run` on the contents of ``inputData``,
        followed by calling `addStandardMetadata` on the result before
        returning it. Any subclass that overrides this method must also call
        `addStandardMetadata` on its measurement before returning it.

        All input data must be treated as optional. This maximizes the
        ``MetricTask``'s usefulness for incomplete pipeline runs or runs with
        optional processing steps. If a metric cannot be calculated because
        the necessary inputs are missing, the ``MetricTask`` must return `None`
        in place of the measurement.

        Examples
        --------
        Consider a metric that characterizes PSF variations across the entire
        field of view, given processed images. Then, if `run` has the
        signature ``run(images)``:

        .. code-block:: py

            inputData = {'images': [image1, image2, ...]}
            inputDataIds = {'images': [{'visit': 42, 'ccd': 1},
                                       {'visit': 42, 'ccd': 2},
                                       ...]}
            outputDataId = {'measurement': {'visit': 42}}
            result = task.adaptArgsAndRun(
                inputData, inputDataIds, outputDataId)
        """
        result = self.run(**inputData)
        if result.measurement is not None:
            self.addStandardMetadata(result.measurement,
                                     outputDataId["measurement"])
        return result

    @classmethod
    def getInputDatasetTypes(cls, config):
        """Return input dataset types for this task.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this task.

        Returns
        -------
        datasets : `dict` from `str` to `str`
            Dictionary where the key is the name of the input dataset (must
            match a parameter to `run`) and the value is the name of its
            Butler dataset type.

        Notes
        -----
        The default implementation extracts a
        `~lsst.pipe.base.PipelineTaskConnections` object from ``config``.
        """
        # Get connections from config for backward-compatibility
        connections = config.connections.ConnectionsClass(config=config)
        return {name: getattr(connections, name).name
                for name in connections.inputs}

    @classmethod
    def areInputDatasetsScalar(cls, config):
        """Return input dataset multiplicity.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this task.

        Returns
        -------
        datasets : `Dict` [`str`, `bool`]
            Dictionary where the key is the name of the input dataset (must
            match a parameter to `run`) and the value is `True` if `run` takes
            only one object and `False` if it takes a list.

        Notes
        -----
        The default implementation extracts a
        `~lsst.pipe.base.PipelineTaskConnections` object from ``config``.
        """
        connections = config.connections.ConnectionsClass(config=config)
        return {name: not getattr(connections, name).multiple
                for name in connections.inputs}

    @classmethod
    @abc.abstractmethod
    def getOutputMetricName(cls, config):
        """Identify the metric calculated by this ``MetricTask``.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this ``MetricTask``.

        Returns
        -------
        metric : `lsst.verify.Name`
            The name of the metric computed by objects of this class when
            configured with ``config``.
        """

    def addStandardMetadata(self, measurement, outputDataId):
        """Add data ID-specific metadata required for all metrics.

        This method currently does not add any metadata, but may do so
        in the future.

        Parameters
        ----------
        measurement : `lsst.verify.Measurement`
            The `~lsst.verify.Measurement` that the metadata are added to.
        outputDataId : ``dataId``
            The data ID to which the measurement applies, at the appropriate
            level of granularity.

        Notes
        -----
        This method must be called by any subclass that overrides
        `adaptArgsAndRun`, but should be ignored otherwise. It should not be
        overridden by subclasses.

        This method is not responsible for shared metadata like the execution
        environment (which should be added by this ``MetricTask``'s caller),
        nor for metadata specific to a particular metric (which should be
        added when the metric is calculated).

        .. warning::
            This method's signature will change whenever additional data needs
            to be provided. This is a deliberate restriction to ensure that all
            subclasses pass in the new data as well.
        """
        pass

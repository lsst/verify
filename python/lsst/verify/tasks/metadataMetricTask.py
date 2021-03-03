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

__all__ = ["MetadataMetricTask", "MetadataMetricConfig",
           "SingleMetadataMetricConnections"]

import abc

import lsst.pex.config

from lsst.pipe.base import Struct, connectionTypes
from lsst.verify.tasks import MetricTask, MetricConfig, MetricConnections, \
    MetricComputationError


class SingleMetadataMetricConnections(
        MetricConnections,
        dimensions={"instrument", "visit", "detector"},
        defaultTemplates={"labelName": "", "package": None, "metric": None}):
    """An abstract connections class defining a metadata input.

    Notes
    -----
    ``SingleMetadataMetricConnections`` defines the following dataset
    templates:

        ``package``
            Name of the metric's namespace. By
            :ref:`verify_metrics <verify-metrics-package>` convention, this is
            the name of the package the metric is most closely
            associated with.
        ``metric``
            Name of the metric, excluding any namespace.
        ``labelName``
            Pipeline label of the `~lsst.pipe.base.PipelineTask` or name of
            the `~lsst.pipe.base.CmdLineTask` whose metadata are being read.
    """
    metadata = connectionTypes.Input(
        name="{labelName}_metadata",
        doc="The target top-level task's metadata. The name must be set to "
            "the metadata's butler type, such as 'processCcd_metadata'.",
        storageClass="PropertySet",
        dimensions={"instrument", "visit", "detector"},
        multiple=False,
    )

    def __init__(self, *, config=None):
        """Customize the connections for a specific MetricTask instance.

        Parameters
        ----------
        config : `MetadataMetricConfig`
            A config for `MetadataMetricTask` or one of its subclasses.
        """
        super().__init__(config=config)
        if config and config.metadataDimensions != self.metadata.dimensions:
            # Hack, but only way to get a connection without fixed dimensions
            newMetadata = connectionTypes.Input(
                name=self.metadata.name,
                doc=self.metadata.doc,
                storageClass=self.metadata.storageClass,
                dimensions=config.metadataDimensions,
                multiple=self.metadata.multiple,
            )
            self.metadata = newMetadata
            # Registry must match actual connections
            self.allConnections['metadata'] = self.metadata
            # Task requires that quantum dimensions match input dimensions
            self.dimensions = config.metadataDimensions


class MetadataMetricConfig(
        MetricConfig,
        pipelineConnections=SingleMetadataMetricConnections):
    """A base class for metadata metric task configs.
    """
    metadataDimensions = lsst.pex.config.ListField(
        # Sort to ensure default order is consistent between runs
        default=sorted(SingleMetadataMetricConnections.dimensions),
        dtype=str,
        doc="Override for the dimensions of the 'metadata' input, when "
            "instrumenting Tasks that don't produce one metadata object "
            "per visit.",
    )


class _AbstractMetadataMetricTask(MetricTask):
    """A base class for tasks that compute metrics from metadata values.

    This class contains code that is agnostic to whether the input is one
    metadata object or many.

    Parameters
    ----------
    *args
    **kwargs
        Constructor parameters are the same as for
        `lsst.pipe.base.PipelineTask`.

    Notes
    -----
    This class should be customized by overriding `getInputMetadataKeys`
    and `makeMeasurement`. You should not need to override `run`.

    This class makes no assumptions about how to handle missing data;
    `makeMeasurement` may be called with `None` values, and is responsible
    for deciding how to deal with them.
    """
    # Design note: getInputMetadataKeys and makeMeasurement are overrideable
    # methods rather than subtask(s) to keep the configs for
    # `MetricsControllerTask` as simple as possible. This was judged more
    # important than ensuring that no implementation details of MetricTask
    # can leak into application-specific code.

    @classmethod
    @abc.abstractmethod
    def getInputMetadataKeys(cls, config):
        """Return the metadata keys read by this task.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this task.

        Returns
        -------
        keys : `dict` [`str`, `str`]
            The keys are the (arbitrary) names of values needed by
            `makeMeasurement`, the values are the metadata keys to be looked
            up. Metadata keys are assumed to include task prefixes in the
            format of `lsst.pipe.base.Task.getFullMetadata()`. This method may
            return a substring of the desired (full) key, but multiple matches
            for any key will cause an error.
        """

    @staticmethod
    def _searchKeys(metadata, keyFragment):
        """Search the metadata for all keys matching a substring.

        Parameters
        ----------
        metadata : `lsst.daf.base.PropertySet`
            A metadata object with task-qualified keys as returned by
            `lsst.pipe.base.Task.getFullMetadata()`.
        keyFragment : `str`
            A substring for a full metadata key.

        Returns
        -------
        keys : `set` of `str`
            All keys in ``metadata`` that have ``keyFragment`` as a substring.
        """
        keys = metadata.paramNames(topLevelOnly=False)
        return {key for key in keys if keyFragment in key}

    @staticmethod
    def _extractMetadata(metadata, metadataKeys):
        """Read multiple keys from a metadata object.

        Parameters
        ----------
        metadata : `lsst.daf.base.PropertySet`
            A metadata object, assumed not `None`.
        metadataKeys : `dict` [`str`, `str`]
            Keys are arbitrary labels, values are metadata keys (or their
            substrings) in the format of
            `lsst.pipe.base.Task.getFullMetadata()`.

        Returns
        -------
        metadataValues : `dict` [`str`, any]
            Keys are the same as for ``metadataKeys``, values are the value of
            each metadata key, or `None` if no matching key was found.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if any metadata key string has more than one match
            in ``metadata``.
        """
        data = {}
        for dataName, keyFragment in metadataKeys.items():
            matchingKeys = MetadataMetricTask._searchKeys(
                metadata, keyFragment)
            if len(matchingKeys) == 1:
                key, = matchingKeys
                data[dataName] = metadata.getScalar(key)
            elif not matchingKeys:
                data[dataName] = None
            else:
                error = "String %s matches multiple metadata keys: %s" \
                    % (keyFragment, matchingKeys)
                raise MetricComputationError(error)
        return data


class MetadataMetricTask(_AbstractMetadataMetricTask):
    """A base class for tasks that compute metrics from single metadata objects.

    Parameters
    ----------
    *args
    **kwargs
        Constructor parameters are the same as for
        `lsst.pipe.base.PipelineTask`.

    Notes
    -----
    This class should be customized by overriding `getInputMetadataKeys`
    and `makeMeasurement`. You should not need to override `run`.

    This class makes no assumptions about how to handle missing data;
    `makeMeasurement` may be called with `None` values, and is responsible
    for deciding how to deal with them.
    """
    # Design note: getInputMetadataKeys and makeMeasurement are overrideable
    # methods rather than subtask(s) to keep the configs for
    # `MetricsControllerTask` as simple as possible. This was judged more
    # important than ensuring that no implementation details of MetricTask
    # can leak into application-specific code.

    ConfigClass = MetadataMetricConfig

    @abc.abstractmethod
    def makeMeasurement(self, values):
        """Compute the metric given the values of the metadata.

        Parameters
        ----------
        values : `dict` [`str`, any]
            A `dict` representation of the metadata passed to `run`. It has the
            same keys as returned by `getInputMetadataKeys`, and maps them to
            the values extracted from the metadata. Any value may be `None` to
            represent missing data.

        Returns
        -------
        measurement : `lsst.verify.Measurement` or `None`
            The measurement corresponding to the input data.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if an algorithmic or system error prevents calculation of
            the metric. See `run` for expected behavior.
        """

    def run(self, metadata):
        """Compute a measurement from science task metadata.

        Parameters
        ----------
        metadata : `lsst.daf.base.PropertySet` or `None`
            A metadata object for the unit of science processing to use for
            this metric, or a collection of such objects if this task combines
            many units of processing into a single metric.

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            A `~lsst.pipe.base.Struct` containing the following component:

            - ``measurement``: the value of the metric
              (`lsst.verify.Measurement` or `None`)

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if the strings returned by `getInputMetadataKeys` match
            more than one key in any metadata object.

        Notes
        -----
        This implementation calls `getInputMetadataKeys`, then searches for
        matching keys in each metadata. It then passes the values of these
        keys (or `None` if no match) to `makeMeasurement`, and returns its
        result to the caller.
        """
        metadataKeys = self.getInputMetadataKeys(self.config)

        if metadata is not None:
            data = self._extractMetadata(metadata, metadataKeys)
        else:
            data = {dataName: None for dataName in metadataKeys}

        return Struct(measurement=self.makeMeasurement(data))

#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
from __future__ import print_function, division

__all__ = ['MetricSet']

import os
import glob

from astropy.table import Table

import lsst.pex.exceptions
from lsst.utils import getPackageDir
from .jsonmixin import JsonSerializationMixin
from .metric import Metric
from .naming import Name
from .yamlutils import load_ordered_yaml


class MetricSet(JsonSerializationMixin):
    r"""A collection of `Metric`\ s.

    Parameters
    ----------
    metrics : sequence of `Metric` instances, optional
        `Metric`\ s to be contained within the ``MetricSet``.
    """

    def __init__(self, metrics=None):
        # Internal dict of Metrics. The MetricSet manages access through its
        # own mapping API.
        self._metrics = {}

        if metrics is not None:
            for metric in metrics:
                if not isinstance(metric, Metric):
                    message = '{0!r} is not a Metric-type'.format(metric)
                    raise TypeError(message)
                self._metrics[metric.name] = metric

    @classmethod
    def load_metrics_package(cls, package_name_or_path='verify_metrics',
                             subset=None):
        """Create a MetricSet from a Verification Framework metrics package.

        Parameters
        ----------
        package_name_or_path : `str`, optional
            Name of an EUPS package that hosts metric and specification
            definition YAML files **or** the file path to a metrics package.
            ``'verify_metrics'`` is the default package, and is where metrics
            and specifications are defined for most packages.
        subset : `str`, optional
            If set, only metrics for this package are loaded. For example, if
            ``subset='validate_drp'``, only ``validate_drp`` metrics are
            included in the `MetricSet`. This argument is equivalent to the
            `MetricSet.subset` method. Default is `None`.

        Returns
        -------
        metric_set : `MetricSet`
            A `MetricSet` containing `Metric` instances.

        See also
        --------
        lsst.verify.MetricSet.load_single_package

        Notes
        -----
        EUPS packages that host metrics and specification definitions for the
        Verification Framework have top-level directories named ``'metrics'``
        and ``'specs'``. The metrics package chosen with the
        ``package_name_or_path`` argument. The default metric package for
        LSST Science Pipelines is ``verify_metrics``.

        To make a `MetricSet` from a single package's YAML metric definition
        file that **is not** contained in a metrics package,
        use `load_single_package` instead.
        """
        try:
            # Try an EUPS package name
            package_dir = getPackageDir(package_name_or_path)
        except lsst.pex.exceptions.NotFoundError:
            # Try as a filesystem path instead
            package_dir = package_name_or_path
        finally:
            package_dir = os.path.abspath(package_dir)

        metrics_dirname = os.path.join(package_dir, 'metrics')
        if not os.path.isdir(metrics_dirname):
            message = 'Metrics directory {0} not found'
            raise OSError(message.format(metrics_dirname))

        metrics = []

        if subset is not None:
            # Load only a single package's YAML file
            metrics_yaml_paths = [os.path.join(metrics_dirname,
                                               '{0}.yaml'.format(subset))]
        else:
            # Load all package's YAML files
            metrics_yaml_paths = glob.glob(os.path.join(metrics_dirname,
                                                        '*.yaml'))

        for metrics_yaml_path in metrics_yaml_paths:
            new_metrics = MetricSet._load_metrics_yaml(metrics_yaml_path)
            metrics.extend(new_metrics)

        return cls(metrics)

    @classmethod
    def load_single_package(cls, metrics_yaml_path):
        """Create a MetricSet from a single YAML file containing metric
        definitions for a single package.

        Returns
        -------
        metric_set : `MetricSet`
            A `MetricSet` containing `Metric` instances found in the YAML
            file.

        See also
        --------
        lsst.verify.MetricSet.load_metrics_package

        Notes
        -----
        The YAML file's name, without extension, is taken as the package
        name for all metrics.

        For example, ``validate_drp.yaml`` contains metrics that are
        identified as belonging to the ``validate_drp`` package.
        """
        metrics = MetricSet._load_metrics_yaml(metrics_yaml_path)
        return cls(metrics)

    @staticmethod
    def _load_metrics_yaml(metrics_yaml_path):
        # package name is inferred from YAML file name (by definition)
        metrics_yaml_path = os.path.abspath(metrics_yaml_path)
        package_name = os.path.splitext(os.path.basename(metrics_yaml_path))[0]

        metrics = []
        with open(metrics_yaml_path) as f:
            yaml_doc = load_ordered_yaml(f)
            for metric_name, metric_doc in yaml_doc.items():
                name = Name(package=package_name, metric=metric_name)
                # throw away a 'name' field if there happens to be one
                metric_doc.pop('name', None)
                # Create metric instance
                metric = Metric.deserialize(name=name, **metric_doc)
                metrics.append(metric)
        return metrics

    @classmethod
    def deserialize(cls, metrics=None):
        """Deserialize metric JSON objects into a MetricSet instance.

        Parameters
        ----------
        metrics : `list`
            List of metric JSON serializations (typically created by
            `MetricSet.json`).

        Returns
        -------
        metric_set : `MetricSet`
            `MetricSet` instance.
        """
        instance = cls()
        for metric_doc in metrics:
            metric = Metric.deserialize(**metric_doc)
            instance.insert(metric)
        return instance

    @property
    def json(self):
        """A JSON-serializable object (`list`)."""
        doc = JsonSerializationMixin._jsonify_list(
            [metric for name, metric in self.items()]
        )
        return doc

    def __getitem__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)
        return self._metrics[key]

    def __setitem__(self, key, value):
        if not isinstance(key, Name):
            key = Name(metric=key)

        # Key name must be for a metric
        if not key.is_metric:
            message = 'Key {0!r} is not a metric name'.format(key)
            raise KeyError(message)

        # value must be a metric type
        if not isinstance(value, Metric):
            message = 'Expected {0!s}={1!r} to be a Metric-type'.format(
                key, value)
            raise TypeError(message)

        # Metric name and key name must be consistent
        if value.name != key:
            message = 'Key {0!s} inconsistent with Metric {0!s}'
            raise KeyError(message.format(key, value))

        self._metrics[key] = value

    def __delitem__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)
        del self._metrics[key]

    def __len__(self):
        return len(self._metrics)

    def __contains__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)
        return key in self._metrics

    def __iter__(self):
        for key in self._metrics:
            yield key

    def __str__(self):
        count = len(self)
        if count == 0:
            count_str = 'empty'
        elif count == 1:
            count_str = '1 Metric'
        else:
            count_str = '{count:d} Metrics'.format(count=count)
        return '<MetricSet: {0}>'.format(count_str)

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for name, metric in self.items():
            try:
                if metric != other[name]:
                    return False
            except KeyError:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iadd__(self, other):
        """Merge another `MetricSet` into this one.

        Parameters
        ---------
        other : `MetricSet`
            Another `MetricSet`. Metrics in ``other`` that do exist in this
            set are added to this one. Metrics in ``other`` replace metrics of
            the same name in this one.

        Returns
        -------
        self : `MetricSet`
            This `MetricSet`.

        Notes
        -----
        Equivalent to `update`.
        """
        self.update(other)
        return self

    def insert(self, metric):
        """Insert a `Metric` into the set.

        Any pre-existing metric with the same name is replaced

        Parameters
        ----------
        metric : `Metric`
            A metric.
        """
        self[metric.name] = metric

    def keys(self):
        r"""Get a list of metric names included in the set

        Returns
        -------
        keys : `list` of `Name`
            List of `Name`\ s included in the set.
        """
        return self._metrics.keys()

    def items(self):
        """Iterate over ``(name, metric)`` pairs in the set.

        Yields
        ------
        item : tuple
            Tuple containing:

            - `Name` of the `Metric`
            - `Metric` instance
        """
        for item in self._metrics.items():
            yield item

    def subset(self, package=None, tags=None):
        """Create a new `MetricSet` with metrics belonging to a single
        package and/or tag.

        Parameters
        ----------
        package : `str` or `lsst.verify.Name`, optional
            Name of the package to subset metrics by. If the package name
            is ``'pkg_a'``, then metric ``'pkg_a.metric_1'`` would be
            **included** in the subset, while ``'pkg_b.metric_2'`` would be
            **excluded**.
        tags : sequence of `str`, optional
            Tags to select metrics by. These tags must be a subset (``<=``)
            of the `Metric.tags` for the metric to be selected.

        Returns
        -------
        metric_subset : `MetricSet`
            Subset of this metric set containing only metrics belonging
            to the specified package and/or tag.

        Notes
        -----
        If both ``package`` and ``tag`` are provided then the resulting
        `MetricSet` contains the **intersection** of the package-based and
        tag-based selections. That is, metrics will belong to ``package``
        and posess the tag ``tag``.
        """
        if package is not None and not isinstance(package, Name):
            package = Name(package=package)

        if tags is not None:
            tags = set(tags)

        if package is not None and tags is None:
            metrics = [metric for metric_name, metric in self._metrics.items()
                       if metric_name in package]

        elif package is not None and tags is not None:
            metrics = [metric for metric_name, metric in self._metrics.items()
                       if metric_name in package
                       if tags <= metric.tags]

        elif package is None and tags is not None:
            metrics = [metric for metric_name, metric in self._metrics.items()
                       if tags <= metric.tags]

        else:
            metrics = []

        return MetricSet(metrics)

    def update(self, other):
        """Merge another `MetricSet` into this one.

        Parameters
        ----------
        other : `MetricSet`
            Another `MetricSet`. Metrics in ``other`` that do exist in this
            set are added to this one. Metrics in ``other`` replace metrics of
            the same name in this one.
        """
        for _, metric in other.items():
            self.insert(metric)

    def _repr_html_(self):
        """Make an HTML representation of metrics for Jupyter notebooks.
        """
        name_col = []
        tags_col = []
        units_col = []
        description_col = []
        reference_col = []

        metric_names = list(self.keys())
        metric_names.sort()

        for metric_name in metric_names:
            metric = self[metric_name]

            name_col.append(str(metric_name))

            tags = list(metric.tags)
            tags.sort()
            tags_col.append(', '.join(tags))

            units_col.append("{0:latex}".format(metric.unit))

            description_col.append(metric.description)

            reference_col.append(metric.reference)

        table = Table([name_col, description_col, units_col, reference_col,
                       tags_col],
                      names=['Name', 'Description', 'Units', 'Reference',
                             'Tags'])
        return table._repr_html_()

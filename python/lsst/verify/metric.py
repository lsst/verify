# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from past.builtins import basestring

import os
import glob

import astropy.units as u

import lsst.pex.exceptions
from lsst.utils import getPackageDir
from .jsonmixin import JsonSerializationMixin
from .naming import Name
from .yamlutils import load_ordered_yaml

__all__ = ['Metric', 'MetricSet']


class MetricSet(JsonSerializationMixin):
    """A collection of `Metric`\ s.

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
    def load_metrics_package(cls, package_name_or_path='verify_metrics'):
        """Create a MetricSet from a Verification Framework metrics package.

        Parameters
        ----------
        package_name_or_path : `str`, optional
            Name of an EUPS package that hosts metric and specification
            definition YAML files **or** the file path to a metrics package.
            ``verify_metrics`` is the default package, and is where metrics
            and specifications are defined for most packages.

        Returns
        -------
        metric_set : `MetricSet`
            A `MetricSet` containing `Metric` instances.

        See also
        --------
        `MetricSet.load_single_package`

        Notes
        -----
        EUPS packages that host metrics and specification definitions for the
        Verification Framework have top-level directories named ``'metrics'``
        and ``'specs'``.

        Within ``'metrics/'``, YAML files are named after *packages* that
        have defined metrics.

        To make a `MetricSet` from a single package's metric definitions,
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

        metrics_yaml_paths = glob.glob(os.path.join(metrics_dirname, '*.yaml'))
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
        `MetricSet.load_metrics_package`

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

    def insert(self, metric):
        """Insert a `Metric` into the set.

        Any pre-existing metric with the same name is replaced

        Parameters
        ----------
        metric : `Metric`
            A metric.
        """
        self[metric.name] = metric

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

    def subset(self, package=None, tag=None):
        """Create a new `MetricSet` with metrics belonging to a single
        package and/or tag.

        Parameters
        ----------
        package : `str` or `lsst.verify.Name`, optional
            Name of the package to subset metrics by. If the package name
            is ``'pkg_a'``, then metric ``'pkg_a.metric_1'`` would be
            **included** in the subset, while ``'pkg_b.metric_2'`` would be
            **excluded**.
        tag : `str`, optional
            Tag to select metrics by.

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

        if package is not None and tag is None:
            metrics = [metric for metric_name, metric in self._metrics.items()
                       if metric_name in package]

        elif package is not None and tag is not None:
            metrics = [metric for metric_name, metric in self._metrics.items()
                       if metric_name in package
                       if tag in metric.tags]

        elif package is None and tag is not None:
            metrics = [metric for metric_name, metric in self._metrics.items()
                       if tag in metric.tags]

        else:
            metrics = []

        return MetricSet(metrics)


class Metric(JsonSerializationMixin):
    """Container for the definition of a metric.

    Metrics can either be instantiated programatically, or from a :ref:`metric
    YAML file <verify-metric-yaml>` with the `from_yaml` class method.

    .. seealso::

       See the :ref:`verify-using-metrics` page for usage details.

    Parameters
    ----------
    name : `str`
        Name of the metric (e.g., ``'PA1'``).
    description : `str`
        Short description about the metric.
    unit : `str` or `astropy.units.Unit`
        Units of the metric. `Measurements` of this metric must be in an
        equivalent (i.e. convertable) unit. Argument can either be a
        `~astropy.unit.Unit` instance, or a an astropy.unit.Unit-compatible
        string representation. Use an empty string, ``''``, or
        ``astropy.units.dimensionless_unscaled`` for a unitless quantity.
    tags : `list` of `str`
        Tags associated with this metric. Tags are user-submitted string
        tokens that are used to group metrics.
    reference_doc : `str`, optional
        The document handle that originally defined the metric
        (e.g., ``'LPM-17'``).
    reference_url : `str`, optional
        The document's URL.
    reference_page : `str`, optional
        Page where metric in defined in the reference document.
    """

    description = None
    """Short description of the metric (`str`)."""

    tags = None
    """Tag labels to group the metric (`list` of `str`)."""

    reference_doc = None
    """Name of the document that specifies this metric (`str`)."""

    reference_url = None
    """URL of the document that specifies this metric (`str`)."""

    reference_page = None
    """Page number in the document that specifies this metric (`int`)."""

    def __init__(self, name, description, unit, tags=None,
                 reference_doc=None, reference_url=None, reference_page=None):
        self.name = name
        self.description = description
        self.unit = u.Unit(unit)
        if tags is None:
            self.tags = []
        elif isinstance(tags, basestring):
            self.tags = [tags]
        else:
            # FIXME DM-8477 Need type checking that tags are actually strings
            # and are a set.
            self.tags = tags
        self.reference_doc = reference_doc
        self.reference_url = reference_url
        self.reference_page = reference_page

    @classmethod
    def deserialize(cls, name=None, description=None, unit=None,
                    tags=None, reference=None):
        """Create a Metric instance from a parsed YAML/JSON document.

        Parameters
        ----------
        kwargs : `dict`
            Keyword arguments that match fields from the `Metric.json`
            serialization.

        Returns
        -------
        metric : `Metric`
            A Metric instance.
        """
        # keyword args for Metric __init__
        args = {
            'unit': unit,
            'tags': tags,
            # Remove trailing newline from folded block description field.
            # This isn't necessary if the field is trimmed with `>-` in YAML,
            # but won't hurt either.
            'description': description.rstrip('\n')
        }

        if reference is not None:
            args['reference_doc'] = reference.get('doc', None)
            args['reference_page'] = reference.get('page', None)
            args['reference_url'] = reference.get('url', None)

        return cls(name, **args)

    @classmethod
    def from_json(cls, json_data):
        """Construct a Metric from a JSON dataset.

        Parameters
        ----------
        json_data : `dict`
            Metric JSON object.

        Returns
        -------
        metric : `Metric`
            Metric from JSON.
        """
        return cls.deserialize(**json_data)

    def __eq__(self, other):
        return ((self.name == other.name) and
                (self.unit == other.unit) and
                (self.tags == other.tags) and
                (self.description == other.description) and
                (self.reference == other.reference))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        # self.unit_str provides the astropy.unit.Unit's string representation
        # that can be used to create a new Unit. But for readability,
        # we use 'dimensionless_unscaled' (an member of astropy.unit) rather
        # than an empty string for the Metric's string representation.
        if self.unit_str == '':
            unit_str = 'dimensionless_unscaled'
        else:
            unit_str = self.unit_str
        return '{self.name!s} ({unit_str}): {self.description}'.format(
            self=self, unit_str=unit_str)

    @property
    def name(self):
        """Metric's name (`Name`)."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = Name(metric=value)

    @property
    def unit(self):
        """The metric's unit (`astropy.units.Unit`)."""
        return self._unit

    @unit.setter
    def unit(self, value):
        if not isinstance(value, (u.UnitBase, u.FunctionUnitBase)):
            message = ('unit attribute must be an astropy.units.Unit-type. '
                       ' Currently type {0!s}.'.format(type(value)))
            if isinstance(value, basestring):
                message += (' Set the `unit_str` attribute instead for '
                            'assigning the unit as a string')
            raise ValueError(message)
        self._unit = value

    @property
    def unit_str(self):
        """The string representation of the metric's unit
        (`~astropy.unit.Unit`-compatible `str`).
        """
        return str(self.unit)

    @unit_str.setter
    def unit_str(self, value):
        self.unit = u.Unit(value)

    @property
    def reference(self):
        """Documentation reference as human-readable text (`str`, read-only).

        Uses `reference_doc`, `reference_page`, and `reference_url`, as
        available.
        """
        ref_str = ''
        if self.reference_doc and self.reference_page:
            ref_str = '{doc}, p. {page:d}'.format(doc=self.reference_doc,
                                                  page=self.reference_page)
        elif self.reference_doc:
            ref_str = self.reference_doc

        if self.reference_url and self.reference_doc:
            ref_str += ', {url}'.format(url=self.reference_url)
        elif self.reference_url:
            ref_str = self.reference_url

        return ref_str

    @property
    def json(self):
        """`dict` that can be serialized as semantic JSON, compatible with
        the SQUASH metric service.
        """
        ref_doc = {
            'doc': self.reference_doc,
            'page': self.reference_page,
            'url': self.reference_url}
        return JsonSerializationMixin.jsonify_dict({
            'name': str(self.name),
            'description': self.description,
            'unit': self.unit_str,
            'tags': self.tags,
            'reference': ref_doc})

    def check_unit(self, quantity):
        """Check that a `~astropy.units.Quantity` has equivalent units to
        this metric.

        Parameters
        ----------
        quantity : `astropy.units.Quantity`
            Quantity to be tested.

        Returns
        -------
        is_equivalent : `bool`
            `True` if the units are equivalent, meaning that the quantity
            can be presented in the units of this metric. `False` if not.
        """
        if not quantity.unit.is_equivalent(self.unit):
            return False
        else:
            return True

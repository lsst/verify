# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import os
import glob
from collections import OrderedDict
import yaml

import astropy.units as u

from .jsonmixin import JsonSerializationMixin

__all__ = ['Metric', 'MetricSet', 'MetricRepo', 'load_metrics']


class MetricRepo(object):
    """A collection of MetricSets, each identified by name.

    Parameters
    ----------
    path : `str`
        Path to the directory defining this MetricRepo.
    metric_sets : `dict`
        Dictionary of ``name: MetricSet`` key-value pairs.
    """
    path = None
    """Path of the directory defining this MetricRepo (`str`)."""

    metric_sets = None
    """`dict` of all the MetricSets defined in this repo, identified by name.
    """

    def __init__(self, path, metric_sets):
        self.path = path
        self.metric_sets = metric_sets

    @classmethod
    def from_metrics_dir(cls, path):
        metric_sets = {}
        for path in glob.glob(os.path.join(path, '*.yaml')):
            name = os.path.splitext(os.path.basename(path))[0]
            with open(path) as f:
                metric_sets[name] = MetricSet.from_yaml(name, yaml.load(f))
        return cls(path, metric_sets)

    def __getitem__(self, key):
        return self.metric_sets[key]

    def __len__(self):
        return len(self.metric_sets)

    def __contains__(self, key):
        return key in self.metric_sets

    def __str__(self):
        items = ",\n".join(str(self.metric_sets[k])
                           for k in sorted(self.metric_sets))
        return "{0.path}: {{\n{1}}}".format(self, items)


class MetricSet(object):
    """A collection of metrics, each identified by name.

    Parameters
    ----------
    name : `str`
        The name of this metric set, usually the name of an LSST package
    metrics : `dict` of `str`: `Metric`
        A `dict` of names and their associated `Metric`\ s.
    """

    name = None
    """Name of the MetricSet, usually the name of a package (`str`)."""

    metrics = None
    """``{name: metric}`` dict of the `Metric` instances"""

    def __init__(self, package_name, metric_list=None, metric_dict=None):
        self.name = package_name
        if metric_dict is None:
            self.metrics = {}
            for metric in metric_list:
                self.metrics[metric.name] = metric
        else:
            self.metrics = metric_dict

    @classmethod
    def from_yaml(cls, name, yaml):
        metrics = {}
        for subname in yaml:
            metric_name = "{}.{}".format(name, subname)
            m = Metric.from_yaml(subname, yaml_doc=yaml)
            metrics[metric_name] = m
        return cls(name, metric_dict=metrics)

    def __getitem__(self, key):
        return self.metrics[key]

    def __len__(self):
        return len(self.metrics)

    def __contains__(self, key):
        return key in self.metrics

    def __str__(self):
        items = ",\n".join(str(self.metrics[k]) for k in sorted(self.metrics))
        return "{0.name}: {{\n{1}\n}}".format(self, items)


class Metric(JsonSerializationMixin):
    """Container for the definition of a metric.

    Metrics can either be instantiated programatically, or from a :ref:`metric
    YAML file <validate-base-metric-yaml>` with the `from_yaml` class method.

    .. seealso::

       See the :ref:`validate-base-using-metrics` page for usage details.

    Parameters
    ----------
    name : `str`
        Name of the metric (e.g., ``'PA1'``).
    description : `str`
        Short description about the metric.
    unit : astropy.units.Unit
        Units of the metric. `Measurements` of this metric must be in an
        equivalent (i.e. convertable) unit.
        Use `dimensionless_unscaled` for a unitless quantity.
    tags : `list` of `str`
        Tags asssociated with this metric, to group it with similar metrics.
    reference_doc : `str`, optional
        The document handle that originally defined the metric
        (e.g., ``'LPM-17'``).
    reference_url : `str`, optional
        The document's URL.
    reference_page : `str`, optional
        Page where metric in defined in the reference document.
    """

    name = None
    """Name of the metric (`str`)."""

    description = None
    """Short description of the metric (`str`)."""

    unit = None
    """Units of the metric (`Astropy.Quantity.Unit`)."""

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
        self.unit = unit
        if tags is None:
            self.tags = []
        else:
            self.tags = tags
        self.reference_doc = reference_doc
        self.reference_url = reference_url
        self.reference_page = reference_page

    @classmethod
    def from_yaml(cls, metric_name, yaml_doc=None, yaml_path=None,
                  resolve_dependencies=True):
        """Create a `Metric` instance from a YAML document that defines
        metrics.

        .. seealso::

           See :ref:`validate-base-metric-yaml` for details on the metric YAML
           schema.

        Parameters
        ----------
        metric_name : `str`
            Name of the metric (e.g., ``'PA1'``).
        yaml_doc : `dict`, optional
            A full metric YAML document loaded as a `dict`. Use this option
            to increase performance by eliminating redundant reads of a
            common metric YAML file. Alternatively, set ``yaml_path``.
        yaml_path : `str`, optional
            The full file path to a metric YAML file. Alternatively, set
            ``yaml_doc``.
        resolve_dependencies : `bool`, optional
            API users should always set this to `True`. The opposite is used
            only used internally.

        Raises
        ------
        RuntimeError
            Raised when neither ``yaml_doc`` or ``yaml_path`` are set.
        """
        if yaml_doc is None and yaml_path is not None:
            with open(yaml_path) as f:
                yaml_doc = yaml.load(f)
        elif yaml_doc is None and yaml_path is None:
            raise RuntimeError('Set either yaml_doc or yaml_path argument')
        metric_doc = yaml_doc[metric_name]

        # NOTE: description is a folded block, which gets an appended '\n'.
        # NOTE: Fix would be to denote the block with '>-' in the .yaml.
        description = metric_doc['description'].rstrip('\n')
        unit = u.Unit(metric_doc['unit'])
        if 'reference' not in metric_doc:
            m = cls(metric_name, description=description, unit=unit)
        else:
            m = cls(metric_name,
                    description=description,
                    unit=unit,
                    reference_doc=metric_doc['reference'].get('doc', None),
                    reference_url=metric_doc['reference'].get('url', None),
                    reference_page=metric_doc['reference'].get('page', None))
        return m

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
        m = cls(json_data['name'],
                json_data['description'],
                u.Unit(json_data['unit']),
                reference_doc=json_data['reference']['doc'],
                reference_page=json_data['reference']['page'],
                reference_url=json_data['reference']['url'])
        return m

    def check_unit(self, quantity):
        """Check that quantity has equivalent units to this metric."""
        if not quantity.unit.is_equivalent(self.unit):
            return False
        return True

    def __eq__(self, other):
        return ((self.name == other.name) and
                (self.reference == other.reference))

    def __str__(self):
        return '{0.name} ({0.unit_str}): "{0.description}"'.format(self)

    @property
    def unit_str(self):
        """The string representation of the `Unit` of this metric."""
        if self.unit == '':
            unit = 'dimensionless_unscaled'
        else:
            unit = self.unit
        return unit

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
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'reference': ref_doc})


def load_metrics(yaml_path):
    """Load metric from a YAML document into an ordered dictionary of
    `Metric`\ s.

    .. seealso::

       :ref:`validate-base-metric-yaml`.

    Parameters
    ----------
    yaml_path : `str`
        The full file path to a metric YAML file.

    Returns
    -------
    metrics : `collections.OrderedDict`
        A dictionary of `Metric` instances, ordered to matched layout of YAML
        document at YAML path. Keys are names of metrics (`str`).

    See also
    --------
    Metric.from_yaml
        Make a single `Metric` instance from a YAML document.
    """
    with open(yaml_path) as f:
        metrics_doc = _load_ordered_yaml(f)
    metrics = []
    for key in metrics_doc:
        metrics.append((key, Metric.from_yaml(key, metrics_doc)))
    return OrderedDict(metrics)


def _load_ordered_yaml(stream, Loader=yaml.Loader,
                       object_pairs_hook=OrderedDict):
    """Load a YAML document into an OrderedDict

    Solution from http://stackoverflow.com/a/21912744
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)

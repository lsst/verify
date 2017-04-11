# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import uuid

import astropy.units as u
from .jsonmixin import JsonSerializationMixin
from .blob import DeserializedBlob
from .datum import Datum, QuantityAttributeMixin
from .metric import Metric


__all__ = ['MeasurementSet', 'Measurement']


class MeasurementSet(object):
    """A collection of Measurements of Metrics, associated with a MetricSet.

    Parameters
    ----------
    name : `str`
        The name of this `MetricSet` (usually the name of a package).
    measurements : `dict` of `str`: `astropy.Quantity`
        The measurements (astropy.Quantities) of each metric, keyed on the
        metric name, to be looked up in metric_set.
    job : `Job`, optional
        The Job that produced these `Measurements`, linking them to their
        provenance and other metadata.
    metric_set : MetricSet, optional
        A `MetricSet` to extract the metric definitions from. If None, use
        name from the verify_metrics package.
    """
    name = None
    """`str` the name of the `MetricSet` these `Measurement`s are of."""

    measurements = None
    """`dict` of all `Measurement` names to `Measurement`s."""

    job = None
    """`Job` that this MeasurementSet was produced by."""

    def __init__(self, name, measurements, job=None, metric_set=None):
        if metric_set is None:
            raise NotImplementedError('Cannot autoload verify_metrics yet')
        self.name = name
        self.measurements = {}
        self.job = job
        for m, v in measurements.items():
            self.measurements[m] = Measurement(m, v, metric_set=metric_set)

    def __getitem__(self, key):
        return self.measurements[key]

    def __len__(self):
        return len(self.measurements)

    def __str__(self):
        items = ",\n".join(str(self.measurements[k])
                           for k in sorted(self.measurements))
        return "{0.name}: {{\n{1}\n}}".format(self, items)


class Measurement(QuantityAttributeMixin, JsonSerializationMixin):
    """A realization of a single Metric.
    """

    _metric = None
    """`Metric` that this is a measurement of."""

    value = None
    """`astropy.Quantity` the value that was measured.
    Must be an equivalent unit (i.e. convertible to) of the parent `Metric`.
    """

    parameters = None
    """`dict` containing all input parameters used by this measurement.
    Parameters are `Datum` instances. Parameter values can be accessed
    and updated as instance attributes named after the parameter.
    """

    extras = None
    """`dict` containing all measurement by-products (called *extras*) that
    have been registered for serialization.

    Extras are `Datum` instances. Values of extras can also be accessed and
    updated as instance attributes named after the extra.
    """
    def __init__(self, name, value, metric_set=None):
        """Summary

        Parameters
        ----------
        name : 'str'
            The name of this metric.
        value : 'astropy.Quantity'
            The value that was measured for this metric.
        metric_set : None
            A `MetricSet` to extract the metric definitions from.

        Raises
        ------
        KeyError
            Raised if name is not a valid name of a metric in metric_set
        UnitTypeError
            Raised if value is not convertible to the type of this
            measurement's metric.
        """
        if metric_set is not None:
            self._metric = metric_set[name]
        else:
            raise NotImplementedError('Cannot autoload verify_metrics yet')

        if not self._metric.check_unit(value):
            raise u.UnitTypeError
        else:
            self.value = value
        self._id = uuid.uuid4().hex

    @property
    def blobs(self):
        """`dict` of blobs attached to this measurement instance."""
        return self._linked_blobs

    @property
    def identifier(self):
        """Unique UUID4-based identifier for this measurement (`str`)."""
        return self._id

    def __str__(self):
        return "{0.name}: {0.value}".format(self)

    @property
    def name(self):
        """Name of the `Metric` associated with this measurement (`str`)."""
        return self._metric.name

    @property
    def description(self):
        return self._metric.description

    # @property
    # def datum(self):
    #     """Representation of this measurement as a `Datum`."""
    #     return Datum(self.quantity, label=self.name,
    #                  description=self.metric.description)

    @property
    def json(self):
        """A `dict` that can be serialized as semantic SQUASH JSON."""
        if isinstance(self.quantity, u.Quantity):
            _value = self.quantity.value
        else:
            _value = self.quantity
        blob_ids = {k: b.identifier for k, b in self._linked_blobs.items()}
        object_doc = {'metric': self.metric,
                      'identifier': self.identifier,
                      'value': _value,
                      'unit': self.unit_str,
                      'parameters': self.parameters,
                      'extras': self.extras,
                      'blobs': blob_ids,
                      'spec_name': self.spec_name,
                      'filter_name': self.filter_name}
        json_doc = JsonSerializationMixin.jsonify_dict(object_doc)
        return json_doc

    @classmethod
    def from_json(cls, json_data, blobs_json=None):
        """Construct a measurement from a JSON dataset.

        Parameters
        ----------
        json_data : `dict`
            Measurement JSON object.
        blobs_json : `list`
            JSON serialization of blobs. This is the ``blobs`` object
            produced by `Job.json`.

        Returns
        -------
        measurement : `MeasurementBase`-type
            Measurement from JSON.
        """
        q = cls._rebuild_quantity(json_data['value'], json_data['unit'])

        parameters = {k: Datum.from_json(v)
                      for k, v in json_data['parameters'].items()}
        extras = {k: Datum.from_json(v)
                  for k, v in json_data['extras'].items()}

        linked_blobs = {}
        if blobs_json is not None:
            for k, id_ in json_data['blobs'].items():
                for blob_doc in blobs_json:
                    if blob_doc['identifier'] == id_:
                        blob = DeserializedBlob.from_json(blob_doc)
                        linked_blobs[k] = blob

        m = cls(quantity=q,
                id_=json_data['identifier'],
                metric=Metric.from_json(json_data['metric']),
                parameters=parameters,
                linked_blobs=linked_blobs,
                extras=extras)
        return m

    def check_spec(self, name):
        """Check this measurement against a `Specification` level, of the
        `Metric`.

        Parameters
        ----------
        name : `str`
            `Specification` level name.

        Returns
        -------
        passed : `bool`
            `True` if the measurement meets the `Specification` level, `False`
            otherwise.

        Notes
        -----
        Internally this method retrieves the `Specification` object, filtering
        first by the ``name``, but also by this object's `filter_name`
        attribute if specifications are filter-dependent.
        """
        return self.metric.check_spec(self.quantity, name,
                                      filter_name=self.filter_name)

    def __eq__(self, other):
        return (self.value == other.value) and (self.metric == other.metric)

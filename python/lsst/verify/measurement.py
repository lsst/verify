# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

__all__ = ['MeasurementSet', 'Measurement']

import uuid

import astropy.units as u
from astropy.tests.helper import quantity_allclose

from .blob import Blob
from .datum import Datum
from .jsonmixin import JsonSerializationMixin
from .metric import Metric
from .naming import Name


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


class Measurement(JsonSerializationMixin):
    """A measurement of a single Metric.

    Parameters
    ----------
    metric : `str`, `lsst.verify.Name`, or `lsst.verify.Metric`
        The name of this metric or the corresponding `~lsst.verify.Metric`
        instance. If a `~lsst.verify.Metric` is providing then the units of
        the ``quantity`` are automatically validated.
    quantity : `astropy.units.Quantity`, optional
        The measured value as an Astropy `~astropy.units.Quantity`.
        If a ``~lsst.verify.Metric`` instance is provided, the units of
        ``quantity`` are compared to the ``~lsst.verify.Metric`\ 's units
        for compatibility. The ``quantity`` can also be set, updated, or
        read from a Measurement instance with the `quantity` property.
    blobs : `list` of `~lsst.verify.Blob`\ s, optional
        List of `lsst.verify.Blob` instances that are associated with a
        measurement. Blobs are datasets that can be associated with many
        measurements and provide context to a measurement.
    extras : `dict` of `lsst.verify.Datum` instances, optional
        `~lsst.verify.Datum` instances can be attached to a measurement.
        Extras can be accessed from the `Measurement.extras` attribute.

    Raises
    ------
    TypeError
        Raised if arguments are not valid types.
    """

    blobs = None
    """`dict` of `lsst.verify.Blob` instances associated with this measurement.
    """

    extras = None
    """`~lsst.verify.Blob` of `lsst.verify.Datum` instances associated with
    this measurement.
    """

    def __init__(self, metric, quantity=None, blobs=None, extras=None):
        # Internal attributes
        self._quantity = None
        # every instance gets a unique identifier, useful for serialization
        self._id = uuid.uuid4().hex

        try:
            self.metric = metric
        except TypeError:
            # must be a name
            self._metric = None
            self.metric_name = metric

        self.quantity = quantity

        self.blobs = {}
        if blobs is not None:
            for blob in blobs:
                if not isinstance(blob, Blob):
                    message = 'Blob {0} is not a Blob-type'
                    raise TypeError(message.format(blob))
                self.blobs[blob.name] = blob

        # extras is a blob automatically created for a measurement.
        # by attaching extras to the self.blobs we ensure it is serialized
        # with other blobs.
        if str(self.metric_name) not in self.blobs:
            self.extras = Blob(str(self.metric_name))
            self.blobs[str(self.metric_name)] = self.extras
        else:
            # pre-existing Blobs; such as from a deserialization
            self.extras = self.blobs[str(self.metric_name)]
        if extras is not None:
            for key, extra in extras.items():
                if not isinstance(extra, Datum):
                    message = 'Extra {0} is not a Datum-type'
                    raise TypeError(message.format(extra))
                self.extras[key] = extra

    @property
    def metric(self):
        """Metric associated with the measurement (`lsst.verify.Metric` or
        `None`).
        """
        return self._metric

    @metric.setter
    def metric(self, value):
        if not isinstance(value, Metric):
            message = '{0} must be an lsst.verify.Metric-type'
            raise TypeError(message.format(value))

        # Ensure the existing quantity has compatible units
        if self.quantity is not None:
            if not value.check_unit(self.quantity):
                message = ('Cannot assign metric {0} with units incompatible '
                           'with existing quantity {1}')
                raise TypeError(message.format(value, self.quantity))

        self._metric = value

        # Reset metric_name for consistency
        self.metric_name = value.name

    @property
    def metric_name(self):
        """Name of the corresponding metric (`lsst.verify.Name`)."""
        return self._metric_name

    @metric_name.setter
    def metric_name(self, value):
        if not isinstance(value, Name):
            self._metric_name = Name(metric=value)
        else:
            if not value.is_metric:
                message = "Expected {0} to be a metric's name".format(value)
                raise TypeError(message)
            else:
                self._metric_name = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, q):
        # a quantity can be None or a Quantity
        if not isinstance(q, u.Quantity) and q is not None:
            message = '{0} is not an astropy.units.Quantity-type'
            raise TypeError(message.format(q))

        if self.metric is not None and q is not None:
            # check unit consistency
            if not self.metric.check_unit(q):
                message = ("The quantity's units {0} are incompatible with "
                           "the metric's units {1}")
                raise TypeError(message.format(q.unit, self.metric.unit))

        self._quantity = q

    @property
    def identifier(self):
        """Unique UUID4-based identifier for this measurement (`str`)."""
        return self._id

    def __str__(self):
        return "{self.metric_name!s}: {self.quantity!s}".format(self=self)

    @property
    def description(self):
        """Description of the metric (`str`, or `None` if
        `Measurement.metric` is not set).
        """
        if self._metric is not None:
            return self._metric.description
        else:
            return None

    @property
    def datum(self):
        """Representation of this measurement as a `Datum`."""
        return Datum(self.quantity,
                     label=str(self.metric_name),
                     description=self.description)

    def link_blob(self, blob):
        """Link a blob to this measurement.

        Blobs can be linked to a measurement so that they can be retrieved
        by analysis and visualization tools post-serialization. Blob data
        is not copied, and one blob can be linked to multiple measurements.

        Parameters
        ----------
        blob : `lsst.verify.Blob`
            A `~lsst.verify.Blob` instance.

        Notes
        -----
        After linking, the `Blob` instance can be accessed by name
        (`Blob.name`) through the `Measurement.blobs` `dict`.
        """
        if not isinstance(blob, Blob):
            message = 'Blob {0} is not a Blob-type'.format(blob)
            raise TypeError(message)
        self.blobs[blob.name] = blob

    @property
    def json(self):
        """A `dict` that can be serialized as semantic SQUASH JSON."""
        if self.quantity is None:
            _normalized_value = None
            _normalized_unit_str = None
        elif self.metric is not None:
            # ensure metrics are normalized to metric definition's units
            _normalized_value = self.quantity.to(self.metric.unit).value
            _normalized_unit_str = self.metric.unit_str
        else:
            _normalized_value = self.quantity.value
            _normalized_unit_str = str(self.quantity.unit)

        blob_refs = [b.identifier for k, b in self.blobs.items()]
        # Remove any reference to an empty extras blob
        if len(self.extras) == 0:
            blob_refs.remove(self.extras.identifier)

        object_doc = {'metric': str(self.metric_name),
                      'identifier': self.identifier,
                      'value': _normalized_value,
                      'unit': _normalized_unit_str,
                      'blob_refs': blob_refs}
        json_doc = JsonSerializationMixin.jsonify_dict(object_doc)
        return json_doc

    @classmethod
    def deserialize(cls, metric=None, identifier=None, value=None, unit=None,
                    blob_refs=None, blobs=None, **kwargs):
        """Create a Measurement instance from a parsed YAML/JSON document.
        """
        # Resolve blobs from references:
        if blob_refs is not None and blobs is not None:
            # get only referenced blobs
            _blobs = [blob for blob in blobs if blob.identifier in blob_refs]
        elif blobs is not None:
            # use all the blobs if none were specifically referenced
            _blobs = blobs
        else:
            _blobs = None

        # Resolve quantity
        _quantity = u.Quantity(value, u.Unit(unit))

        instance = cls(metric, quantity=_quantity, blobs=_blobs)
        instance._identifer = identifier  # re-wire id from serialization
        return instance

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
        blobs = []
        if blobs_json is not None:
            for id_ in json_data['blob_refs']:
                for blob_doc in blobs_json:
                    if blob_doc['identifier'] == id_:
                        blob = Blob.from_json(blob_doc)
                        blobs.append(blob)

        return cls(blobs=blobs, **json_data)

    def __eq__(self, other):
        return quantity_allclose(self.quantity, other.quantity) and \
            (self.metric_name == other.metric_name)

    def __ne__(self, other):
        return not self.__eq__(other)

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

__all__ = ['Measurement', 'MeasurementNotes']

import uuid

import astropy.units as u
from astropy.tests.helper import quantity_allclose

from .blob import Blob
from .datum import Datum
from .jsonmixin import JsonSerializationMixin
from .metric import Metric
from .naming import Name


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
    notes : `dict`, optional
        Measurement annotations. These key-value pairs are automatically
        available from `Job.meta`, though keys are prefixed with the
        metric's name. This metadata can be queried by specifications,
        so that specifications can be written to test only certain types
        of measurements.

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

    def __init__(self, metric, quantity=None, blobs=None, extras=None,
                 notes=None):
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

        self._notes = MeasurementNotes(self.metric_name)
        if notes is not None:
            self.notes.update(notes)

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

    def _repr_latex_(self):
        """Get a LaTeX-formatted string representation of the measurement
        quantity (used in Jupyter notebooks).

        Returns
        -------
        rep : `str`
            String representation.
        """
        return '{0.value:0.1f} {0.unit:latex_inline}'.format(self.quantity)

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
    def notes(self):
        return self._notes

    @property
    def json(self):
        """A `dict` that can be serialized as semantic SQUASH JSON.

        Fields:

        - ``metric`` (`str`) Name of the metric the measurement measures.
        - ``identifier`` (`str`) Unique identifier for this measurement.
        - ``value`` (`float`) Value of the measurement.
        - ``unit`` (`str`) Units of the ``value``, as an
          `astropy.units`-compatible string.
        - ``blob_refs`` (`list` of `str`) List of `Blob.identifier`\ s for
          Blobs associated with this measurement.

        .. note::

           `Blob`\ s are not serialized with a measurement, only their
           identifiers. The `lsst.verify.Job` class handles serialization of
           blobs alongside measurements.

           Likewise, `Measurement.notes` are not serialized with the
           measurement. They are included with `lsst.verify.Job`\ 's
           serialization, alongside job-level metadata.
        """
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

        Parameters
        ----------
        metric : `str`
            Name of the metric the measurement measures.
        identifier : `str`
            Unique identifier for this measurement.
        value : `float`
            Value of the measurement.
        unit : `str`
            Units of the ``value``, as an `astropy.units`-compatible string.
        blob_refs : `list` of `str`
            List of `Blob.identifier`\ s for Blob associated with this
            measurement.
        blobs : `BlobSet`
            `BlobSet` containing all `Blob`\ s referenced by the measurement's
            ``blob_refs`` field. Note that the `BlobSet` must be created
            separately, prior to deserializing measurement objects.

        Returns
        -------
        measurement : `Measurement`
            Measurement instance.
        """
        # Resolve blobs from references:
        if blob_refs is not None and blobs is not None:
            # get only referenced blobs
            _blobs = [blob for blob_identifier, blob in blobs.items()
                      if blob_identifier in blob_refs]
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

    def __eq__(self, other):
        return quantity_allclose(self.quantity, other.quantity) and \
            (self.metric_name == other.metric_name) and \
            (self.notes == other.notes)

    def __ne__(self, other):
        return not self.__eq__(other)


class MeasurementNotes(object):
    """Container for annotations (notes) associated with a single measurement.

    Parameters
    ----------
    metric_name : `Name` or `str`
        Fully qualified name of the measurement's metric. The metric's name
        is used as a prefix for key names.

    Examples
    --------
    ``MeasurementNotes`` implements a `dict`-like interface. The only
    difference is that internally keys are always prefixed with the name of
    a metric. This allows measument annotations to mesh with reduced key
    collision likelihood with Job metadata keys (`lsst.verify.Metadata`).

    Users of `MeasurementNotes`, typically though `Measurement.notes`, do
    not need to use this prefix. Keys are prefixed behind the scenes.

    >>> notes = MeasurementNotes('validate_drp')
    >>> notes['filter_name'] = 'r'
    >>> notes['filter_name']
    'r'
    >>> notes['validate_drp.filter_name']
    'r'
    >>> print(notes)
    {'validate_drp.filter_name': 'r'}
    """

    def __init__(self, metric_name):
        # cast Name to str form to deal with prefixes
        self._metric_name = str(metric_name)
        # Enforced key prefix for all notes
        self._prefix = '{self._metric_name}.'.format(self=self)
        self._data = {}

    def _format_key(self, key):
        """Ensures the key includes the metric name prefix."""
        if not key.startswith(self._prefix):
            key = self._prefix + key
        return key

    def __getitem__(self, key):
        key = self._format_key(key)
        return self._data[key]

    def __setitem__(self, key, value):
        key = self._format_key(key)
        self._data[key] = value

    def __delitem__(self, key):
        key = self._format_key(key)
        del self._data[key]

    def __contains__(self, key):
        key = self._format_key(key)
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        return (self._metric_name == other._metric_name) and \
            (self._data == other._data)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        for key in self._data:
            yield key

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def keys(self):
        return [key for key in self]

    def items(self):
        for item in self._data.items():
            yield item

    def update(self, data):
        for key, value in data.items():
            self[key] = value

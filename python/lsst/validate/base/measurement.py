# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import abc
import uuid

import astropy.units as u
from .datummixin import DatumAttributeMixin
from .jsonmixin import JsonSerializationMixin
from .blob import BlobBase, DeserializedBlob
from .datum import Datum, QuantityAttributeMixin
from .metric import Metric


__all__ = ['MeasurementBase', 'DeserializedMeasurement']


class MeasurementBase(QuantityAttributeMixin, JsonSerializationMixin,
                      DatumAttributeMixin):
    """Base class for Measurement classes.

    This class isn't instantiated directly. Instead, developers should
    subclass `MeasurementBase` to create measurement classes for each
    metric being measured.

    Subclasses must (at least) implement the following attributes:

    - `metric` (set to a `Metric` instance).
    - `spec_name` (if applicable).
    - `filter_name` (if applicable).

    Subclasses are also responsible for assiging the measurement's value
    to the `quantity` attribute (as an `astropy.units.Quantity`).

    .. seealso::

       The :ref:`validate-base-measurement-class` page shows how to create
       measurement classes using `MeasurementBase`.
    """

    __metaclass__ = abc.ABCMeta

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

    spec_name = None
    """Name of the specification level (e.g., 'design,' 'minimum,' 'stretch')
    that this measurement represents.

    `None` if this measurement applies to all specification levels.
    """

    filter_name = None
    """Name of the optical filter for the observations this measurement
    was made from.

    `None` if a measurement is not filter-dependent.
    """

    def __init__(self):
        self._quantity = None
        self.parameters = {}
        self.extras = {}
        self._linked_blobs = {}
        self._id = uuid.uuid4().hex
        self.spec_name = None
        self.filter_name = None

    def __getattr__(self, key):
        if key in self.parameters:
            # Requesting a serializable parameter
            return self.parameters[key].quantity
        elif key in self.extras:
            return self.extras[key].quantity
        elif key in self._linked_blobs:
            return self._linked_blobs[key]
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, key))

    def __setattr__(self, key, value):
        # avoiding __setattr__ loops by not handling names in _bootstrap
        _bootstrap = ('parameters', 'extras', '_linked_blobs')
        if key not in _bootstrap and isinstance(value, BlobBase):
            self._linked_blobs[key] = value
        elif key not in _bootstrap and self.parameters is not None and \
                key in self.parameters:
            # Setting value of a serializable parameter
            self.parameters[key].quantity = value
        elif key not in _bootstrap and self.extras is not None and \
                key in self.extras:
            # Setting value of a serializable measurement extra
            self.extras[key].quantity = value
        else:
            super(MeasurementBase, self).__setattr__(key, value)

    @property
    def blobs(self):
        """`dict` of blobs attached to this measurement instance."""
        return self._linked_blobs

    @property
    def identifier(self):
        """Unique UUID4-based identifier for this measurement (`str`)."""
        return self._id

    def register_parameter(self, param_key, quantity=None,
                           label=None, description=None, datum=None):
        """Register a measurement input parameter attribute.

        The value of the parameter can either be set at registration time
        (see ``quantity`` argument), or later by setting the object's attribute
        named ``param_key``.

        The value of a parameter can always be accessed through the object's
        attribute named after the provided ``param_key``.

        Parameters are stored as `Datum` objects, which can be accessed
        through the `parameters` attribute `dict`.

        Parameters
        ----------
        param_key : `str`
            Name of the parameter; used as the key in the `parameters`
            attribute of this object.
        quantity : `astropy.units.Quantity`, `str` or `bool`.
            Value of the parameter.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            ``param_key`` is used as the `label`. Setting this ``label``
            argument overrides that default.
        description : `str`, optional
            Extended description of the parameter.
        datum : `Datum`, optional
            If a `Datum` is provided, its quantity, label and description
            are be used unless overriden by other arguments to this method.
        """
        self._register_datum_attribute(self.parameters, param_key,
                                       quantity=quantity, label=label,
                                       description=description,
                                       datum=datum)

    def register_extra(self, extra_key, quantity=None, unit=None, label=None,
                       description=None, datum=None):
        """Register a measurement extra---a by-product of a metric measurement.

        The value of the extra can either be set at registration time
        (see ``quantity`` argument), or later by setting the object's attribute
        named ``extra_key``.

        The value of an extra can always be accessed through the object's
        attribute named after ``extra_key``.

        Extras are stored as `Datum` objects, which can be accessed
        through the `parameters` attribute `dict`.

        Parameters
        ----------
        extra_key : `str`
            Name of the extra; used as the key in the `extras`
            attribute of this object.
        quantity : `astropy.units.Quantity`, `str`, or `bool`
            Value of the extra.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            ``extra_key`` is used as the ``label``. Setting this label argument
            overrides both of these.
        description : `str`, optional
            Extended description.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, label and description
            will be used unless overriden by other arguments to
            `register_extra`.
        """
        self._register_datum_attribute(self.extras, extra_key,
                                       quantity=quantity, label=label,
                                       description=description,
                                       datum=datum)

    @property
    def metric(self):
        """`Metric` that this measurement is associated to.
        """
        try:
            return self._metric
        except AttributeError:
            raise AttributeError('`metric` attribute not set in {0}'.format(self.__class__))

    @metric.setter
    def metric(self, value):
        assert isinstance(value, Metric)
        self._metric = value

    @property
    def label(self):
        """Name of the `Metric` associated with this measurement (`str`)."""
        return self.metric.name

    @property
    def datum(self):
        """Representation of this measurement as a `Datum`."""
        return Datum(self.quantity, label=self.label,
                     description=self.metric.description)

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
                extras=extras,
                spec_name=json_data['spec_name'],
                filter_name=json_data['filter_name'])
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


class DeserializedMeasurement(MeasurementBase):
    """Measurement deserialized from JSON.

    For internal use only.
    """

    metric = None

    def __init__(self, quantity=None, id_=None, metric=None,
                 parameters=None, extras=None, linked_blobs=None,
                 spec_name=None, filter_name=None):
        MeasurementBase.__init__(self)
        if linked_blobs is not None:
            self._linked_blobs = linked_blobs
        if parameters is not None:
            self.parameters = parameters
        if extras is not None:
            self.extras = extras

        self.metric = metric
        self._quantity = quantity
        self._id = id_
        self.spec_name = spec_name
        self.filter_name = filter_name

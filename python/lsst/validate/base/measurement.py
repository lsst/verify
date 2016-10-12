# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import abc
import uuid
import astropy.units

from .datummixin import DatumAttributeMixin
from .jsonmixin import JsonSerializationMixin
from .blob import BlobBase
from .datum import Datum


__all__ = ['MeasurementBase']


class MeasurementBase(JsonSerializationMixin, DatumAttributeMixin):
    """Base class for Measurement classes.

    This class isn't instantiated directly. Instead, developers should
    subclass `MeasurementBase` to create a measurement classes for each
    metric being measured.

    Subclasses must (at least) implement the following attributes:

    - `metric`
    - `value`
    - `units`
    - `label`
    - `spec_name` (if applicable)
    - `filter_name` (if applicable)

    .. seealso::

       The :ref:`validate-base-measurement-class` page shows how to create
       measurement classes using `MeasurementBase`.
    """

    __metaclass__ = abc.ABCMeta

    parameters = dict()
    """`dict` containing all input parameters used by this measurement.
    Parameters are `Datum` instances. Parameter values can be accessed
    and updated as instance attributes named after the parameter.
    """

    extras = dict()
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
        self.parameters = {}
        self.extras = {}
        self._linked_blobs = {}
        self._id = uuid.uuid4().hex
        self.spec_name = None
        self.filter_name = None

    def __getattr__(self, key):
        if key in self.parameters:
            # Requesting a serializable parameter
            return self.parameters[key].value
        elif key in self.extras:
            return self.extras[key].value
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
        elif key not in _bootstrap and key in self.parameters:
            # Setting value of a serializable parameter
            self.parameters[key].value = value
        elif key not in _bootstrap and key in self.extras:
            # Setting value of a serializable measurement extra
            self.extras[key].value = value
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

    def register_parameter(self, param_key, value=None, units=None, label=None,
                           description=None, datum=None):
        """Register a measurement input parameter attribute.

        The value of the parameter can either be set at registration time
        (see ``value`` argument), or later by setting the object's attribute
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
        value : obj, optional
            Value of the parameter.
        units : `str`, optional
            `astropy.units.Unit`-compatible string.
            See http://docs.astropy.org/en/stable/units/.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            ``param_key`` is used as the `label`. Setting this ``label``
            argument overrides that default.
        description : `str`, optional
            Extended description of the parameter.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, units and label will be used
            unless overriden by other arguments to this method.
        """
        self._register_datum_attribute(self.parameters, param_key,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

    def register_extra(self, extra_key, value=None, units=None, label=None,
                       description=None, datum=None):
        """Register a measurement extra---a by-product of a metric measurement.

        The value of the extra can either be set at registration time
        (see ``value`` argument), or later by setting the object's attribute
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
        value : obj
            Value of the extra, either as a regular object, or already
            represented as a `Datum`.
        units : `str`, optional
            `astropy.units.Unit`-compatible string indicating units of
            ``value``. See http://docs.astropy.org/en/stable/units/.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            ``extra_key`` is used as the ``label``. Setting this label argument
            overrides both of these.
        description : `str`, optional
            Extended description.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, units, label and description
            will be used unless overriden by other arguments to
            `register_extra`.
        """
        self._register_datum_attribute(self.extras, extra_key,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

    @abc.abstractproperty
    def metric(self):
        """`Metric` that this measurement is associated to.
        """
        pass

    @abc.abstractproperty
    def value(self):
        """`Metric` measurement value."""
        pass

    @abc.abstractproperty
    def units(self):
        """`astropy.units.Unit`-compatible string with units of `value`
        (`str`).
        """
        pass

    @property
    def latex_units(self):
        """Units as a LaTeX string, wrapped in ``$``."""
        if self.units != '':
            fmtr = astropy.units.format.Latex()
            return fmtr.to_string(self.astropy_units)
        else:
            return ''

    @property
    def astropy_units(self):
        """Measurement units as a `astropy.units.Unit`."""
        return astropy.units.Unit(self.units)

    @property
    def label(self):
        """Name of the `Metric` associated with this measurement (`str`)."""
        return self.metric.name

    @property
    def datum(self):
        """Representation of this measurement as a `Datum`."""
        return Datum(self.value, units=self.units, label=self.label,
                     description=self.metric.description)

    @property
    def json(self):
        """A `dict` that can be serialized as semantic SQUASH JSON."""
        blob_ids = list(set([b.identifier for n, b in
                             self._linked_blobs.items()]))
        object_doc = {'metric': self.metric,
                      'identifier': self.identifier,
                      'value': self.value,
                      'parameters': self.parameters,
                      'extras': self.extras,
                      'blobs': blob_ids,
                      'spec_name': self.spec_name,
                      'filter': self.filter_name}
        json_doc = JsonSerializationMixin.jsonify_dict(object_doc)
        return json_doc

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
        return self.metric.check_spec(self.value, name,
                                      filter_name=self.filter_name)

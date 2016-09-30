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
    """Baseclass for Measurement classes.

    Attributes
    ----------
    blobs
    identifier
    metric
    value
    units
    latex_units
    label
    datum
    json
    spec_name : `str`
        A `str` identifying the specification level (e.g., 'design,' 'minimum,'
        'stretch') that this measurement represents. `None` if this measurement
        applies to all specification levels.
    filter_name : `str`
        A `str` identifying the optical filter of observatons this measurement
        was made from. Defaults to `None` if a measurement is not
        filter-dependent. `filter_name` should be specificed if needed to
        resolve a filter-specific specification.
    parameters : dict
        A `dict` containing all input parameters used by this measurement.
        Parameters are :class:`lsst.validate.base.Datum` instances.
        Parameter values can also be accessed and updated as instance
        attributes named after the parameter.
    extras : dict
        A `dict` containing all measurement by-products (extras) that have
        been registered for serialization. Extras are
        :class:`lsst.validate.base.Datum` instances. Values of extras can
        also be accessed and updated as instance attributes named after
        the extra.
    """
    __metaclass__ = abc.ABCMeta

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
        """A unique UUID4-based identifier for this measurement."""
        return self._id

    def register_parameter(self, param_key, value=None, units=None, label=None,
                           description=None, datum=None):
        """Register a measurement input parameter attribute.

        The value of the parameter can either be set at registration time
        (see `value` argument), or later by setting the object's attribute
        named `param_key`.

        The value of a parameter can always be accessed through the object's
        attribute named `param_key.`

        Parameters are stored as :class:`Datum` objects, which can be accessed
        through the `parameters` attribute `dict`.

        Parameters
        ----------
        param_key : `str`
            Name of the parameter; used as the key in the `parameters`
            attribute of this object.
        value : obj
            Value of the parameter.
        units : `str`, optional
            An astropy-compatible unit string.
            See http://docs.astropy.org/en/stable/units/.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            `paramKey` is used as the `label`. Setting this label argument
            overrides this default.
        description : `str`, optional
            Extended description.
        datum : :class:`~lsst.validate.base.Datum`, optional
            If a :class:`~lsst.validate.base.Datum` is provided, its value,
            units and label will be used unless overriden by other arguments to
            :class:`~lsst.validate.base.Measurement.register_parameter`.
        """
        self._register_datum_attribute(self.parameters, param_key,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

    def register_extra(self, extra_key, value=None, units=None, label=None,
                       description=None, datum=None):
        """Register a measurement extra---a by-product of a metric measurement.

        The value of the extra can either be set at registration time
        (see `value` argument), or later by setting the object's attribute
        named `extra_key`.

        The value of an extra can always be accessed through the object's
        attribute named `extra_key.`

        Extras are stored as :class:`Datum` objects, which can be accessed
        through the `parameters` attribute `dict`.

        Parameters
        ----------
        extra_key : str
            Name of the extra; used as the key in the `extras`
            attribute of this object.
        value : obj
            Value of the extra, either as a regular object, or already
            represented as a :class:`~lsst.validate.base.Datum`.
        units : str, optional
            The astropy-compatible unit string.
            See http://docs.astropy.org/en/stable/units/.
        label : str, optional
            Label suitable for plot axes (without units). By default the
            `extra_key` is used as the `label`. Setting this label argument
            overrides both of these.
        description : `str`, optional
            Extended description.
        datum : :class:`~lsst.validate.base.Datum`, optional
            If a :class:`~lsst.validate.base.Datum` is provided, its value,
            units, label and description will be used unless overriden by other
            arguments to
            :meth:`~lsst.validate.base.Measurement.register_extra`.
        """
        self._register_datum_attribute(self.extras, extra_key,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

    @abc.abstractproperty
    def metric(self):
        """An instance derived from
        :class:`~lsst.validate.base.Metric`.
        """
        pass

    @abc.abstractproperty
    def value(self):
        """Metric measurement value."""
        pass

    @abc.abstractproperty
    def units(self):
        """Astropy-compatible units string. (`str`)."""
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
        """Astropy unit object."""
        return astropy.units.Unit(self.units)

    @abc.abstractproperty
    def label(self):
        """Lable (`str`) suitable for plot axes; without units."""
        pass

    @property
    def datum(self):
        """Representation of this measurement as a
        :class:`lsst.validate.base.Datum`.
        """
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
        """Check this measurement against a specification level, of the
        metric.

        Parameters
        ----------
        name : `str`
            Specification level name.

        Returns
        -------
        passed : `bool`
            `True` if the measurement meets the specification level, `False`
            otherwise.

        Notes
        -----
        Internally this method retrieves the Specification object, filtering
        first by the `name`, but also by this object's `filter_name` attribute
        if specifications are filter-dependent.
        """
        return self.metric.check_spec(self.value, name,
                                      filter_name=self.filter_name)

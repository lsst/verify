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
    metric
    units
    label
    json
    specName : str
        A `str` identifying the specification level (e.g., design, minimum
        stretch) that this measurement represents. `None` if this measurement
        applies to all specification levels.
    bandpass : str
        A `str` identifying the bandpass of observatons this measurement was
        made from. Defaults to `None` if a measurement is not
        bandpass-dependent. `bandpass` should be specificed if needed to
        resolve a bandpass-specific specification.
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
        self._linkedBlobs = {}
        self._id = uuid.uuid4().hex
        self.specName = None
        self.bandpass = None

    def __getattr__(self, key):
        if key in self.parameters:
            # Requesting a serializable parameter
            return self.parameters[key].value
        elif key in self.extras:
            return self.extras[key].value
        elif key in self._linkedBlobs:
            return self._linkedBlobs[key]
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, key))

    def __setattr__(self, key, value):
        # avoiding __setattr__ loops by not handling names in _bootstrap
        _bootstrap = ('parameters', 'extras', '_linkedBlobs')
        if key not in _bootstrap and isinstance(value, BlobBase):
            self._linkedBlobs[key] = value
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
        return self._linkedBlobs

    @property
    def identifier(self):
        return self._id

    def registerParameter(self, paramKey, value=None, units=None, label=None,
                          description=None, datum=None):
        """Register a measurement input parameter attribute.

        The value of the parameter can either be set at registration time
        (see `value` argument), or later by setting the object's attribute
        named `paramKey`.

        The value of a parameter can always be accessed through the object's
        attribute named `paramKey.`

        Parameters are stored as :class:`Datum` objects, which can be accessed
        through the `parameters` attribute `dict`.

        Parameters
        ----------
        paramKey : str
            Name of the parameter; used as the key in the `parameters`
            attribute of this object.
        value : obj
            Value of the parameter.
        units : str, optional
            An astropy-compatible unit string.
            See http://docs.astropy.org/en/stable/units/.
        label : str, optional
            Label suitable for plot axes (without units). By default the
            `paramKey` is used as the `label`. Setting this label argument
            overrides this default.
        description : `str`, optional
            Extended description.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, units and label will be
            used unless overriden by other arguments to `registerParameter`.
        """
        self._register_datum_attribute(self.parameters, paramKey,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

    def registerExtra(self, extraKey, value=None, units=None, label=None,
                      description=None, datum=None):
        """Register a measurement extra---a by-product of a metric measurement.

        The value of the extra can either be set at registration time
        (see `value` argument), or later by setting the object's attribute
        named `extraKey`.

        The value of an extra can always be accessed through the object's
        attribute named `exrtaKey.`

        Extras are stored as :class:`Datum` objects, which can be accessed
        through the `parameters` attribute `dict`.

        Parameters
        ----------
        extraKey : str
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
            `extraKey` is used as the `label`. Setting this label argument
            overrides both of these.
        description : `str`, optional
            Extended description.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, units, label and description
            will be used unless overriden by other arguments to
            `registerExtra`.
        """
        self._register_datum_attribute(self.extras, extraKey,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

    @abc.abstractproperty
    def metric(self):
        """An instance derived from
        :class:`~lsst.validate.base.MetricBase`.
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
        """Units as a LateX string, wrapped in ``$``."""
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
        """a `dict` that can be serialized as semantic SQuaSH json."""
        blobIds = list(set([b.identifier for n, b in
                            self._linkedBlobs.items()]))
        object_doc = {'metric': self.metric,
                      'identifier': self.identifier,
                      'value': self.value,
                      'parameters': self.parameters,
                      'extras': self.extras,
                      'blobs': blobIds,
                      'spec_name': self.specName,
                      'filter': self.bandpass}
        json_doc = JsonSerializationMixin.jsonify_dict(object_doc)
        return json_doc

    def checkSpec(self, name):
        """Check this measurement against a specification level `name`, of the
        metric.

        Internally this method retrieves the Specification object, filtering
        first by the `name`, but also by this object's `bandpass` attribute
        if specifications are bandpass-dependent.
        """
        return self.metric.checkSpec(self.value, name, bandpass=self.bandpass)

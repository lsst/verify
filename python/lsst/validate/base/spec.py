# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import astropy.units

from .jsonmixin import JsonSerializationMixin
from .datum import Datum


__all__ = ['Specification']


class Specification(JsonSerializationMixin):
    """A specification level or threshold associated with a Metric.

    Parameters
    ----------
    name : `str`
        Name of the specification level for a metric. LPM-17 uses `'design'`,
        `'minimum'` and `'stretch'`.
    value : `float`
        The specification threshold level.
    filter_names : `list`, optional
        A list of optical filter names that this specification applies to.
        Set only if the specification level is dependent on the filter.
    dependencies : `dict`
        A dictionary of named :class:`lsst.validate.base.Datum` values that
        must be known when making a measurement against a specification level.
        Dependencies can be accessed as attributes of the specification object.
    """
    def __init__(self, name, value, units, filter_names=None,
                 dependencies=None):
        self.name = name
        self.label = name
        self.value = value
        self.units = units
        self.description = ''
        self.filter_names = filter_names
        if dependencies:
            self.dependencies = dependencies
        else:
            self.dependencies = {}

    def __getattr__(self, key):
        """Access dependencies with keys as attributes."""
        if key in self.dependencies:
            return self.dependencies[key]
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, key))

    @property
    def datum(self):
        """Representation of this Specification as a
        :class:`lsst.validate.base.Datum`.
        """
        return Datum(self.value, units=self.units, label=self.name,
                     description=self.description)

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
        """Astropy :astropy:class:`~astropy.units.Unit` object."""
        return astropy.units.Unit(self.units)

    @property
    def astropy_quanitity(self):
        """Datum as an Astropy :astropy:class:`~astropy.units.Quantity`."""
        return self.value * self.astropy_units

    @property
    def json(self):
        """Specification data as a JSON-serialiable `dict`."""
        return JsonSerializationMixin.jsonify_dict({
            'name': self.name,
            'value': Datum(self.value, self.units),
            'filters': self.filter_names,
            'dependencies': self.dependencies})

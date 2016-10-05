# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import numpy as np
import astropy.units

from .jsonmixin import JsonSerializationMixin


__all__ = ['Datum']


class Datum(JsonSerializationMixin):
    """A value annotated with units, a plot label and description.

    Parameters
    ----------
    value : `str`, `int`, `float` or 1-D iterable.
        Value of the `Datum`.
    units : `str`
        See http://docs.astropy.org/en/stable/units/.
    label : `str`, optional
        Label suitable for plot axes (without units).
    description : `str`, optional
        Extended description of the `Datum`.
    """
    def __init__(self, value, units, label=None, description=None):
        self._doc = {}
        self.value = value
        self.units = units
        self.label = label
        self.description = description

    @property
    def json(self):
        """Datum as a `dict` compatible with overall `Job` JSON schema."""
        # Copy the dict so that the serializer is immutable
        v = self.value
        if isinstance(v, np.ndarray):
            v = v.tolist()
        d = {
            'value': v,
            'units': self.units,
            'label': self.label,
            'description': self.description
        }
        return d

    @property
    def value(self):
        """Value of the datum (`str`, `int`, `float` or 1-D iterable.)."""
        return self._doc['value']

    @value.setter
    def value(self, v):
        self._doc['value'] = v

    @property
    def units(self):
        """`astropy.units.Unit`-compatible `str` indicating units of ``value``.
        """
        return self._doc['units']

    @units.setter
    def units(self, value):
        # verify that Astropy can parse the unit string
        if value is not None:
            astropy.units.Unit(value, parse_strict='raise')
        self._doc['units'] = value

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

    @property
    def quantity(self):
        """Datum as an astropy Quantity."""
        return self.value * self.astropy_units

    @property
    def label(self):
        """Label for plotting (without units)."""
        return self._doc['label']

    @label.setter
    def label(self, value):
        assert isinstance(value, basestring) or value is None
        self._doc['label'] = value

    @property
    def description(self):
        """Extended description of Datum."""
        return self._doc['description']

    @description.setter
    def description(self, value):
        assert isinstance(value, basestring) or value is None
        self._doc['description'] = value

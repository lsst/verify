# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import astropy.units

from .jsonmixin import JsonSerializationMixin


__all__ = ['Datum', 'QuantityAttributeMixin']


class QuantityAttributeMixin(object):
    """Mixin with common attributes for classes that wrap an
    `astropy.units.Quantity`.

    Subclasses must have a self._quantity attribute that is an
    `astropy.units.Quantity` or `str` or `bool` (only numeric values are
    astropy quantities).
    """

    @property
    def quantity(self):
        """Value of the datum (`astropy.units.Quantity`, `str`, or `bool`)."""
        return self._quantity

    @quantity.setter
    def quantity(self, q):
        assert isinstance(q, astropy.units.Quantity) or \
            isinstance(q, basestring) or isinstance(q, bool)
        self._quantity = q

    @property
    def unit(self):
        """Read-only `astropy.units.Unit` of the `quantity`.

        If the `quantity` is a `str` or `bool`, the unit is `None`.
        """
        q = self.quantity
        if q is None or isinstance(q, basestring) or isinstance(q, bool):
            return None
        else:
            return q.unit

    @property
    def unit_str(self):
        """Read-only `astropy.units.Unit`-compatible `str` indicating units of
        `quantity`.
        """
        if self.unit is None:
            # unitless quantites have an empty string for a unit; retain this
            # behaviour for str and bool quantities.
            return ''
        else:
            return str(self.unit)

    @property
    def latex_unit(self):
        """Units as a LaTeX string, wrapped in ``$``."""
        if self.unit is not None and self.unit != '':
            fmtr = astropy.units.format.Latex()
            return fmtr.to_string(self.unit)
        else:
            return ''


class Datum(QuantityAttributeMixin, JsonSerializationMixin):
    """A value annotated with units, a plot label and description.

    Datum supports natively support Astropy `~astropy.units.Quantity` and
    units. In addition, a Datum can also wrap string and boolean values.

    Parameters
    ----------
    quantity : `astropy.units.Quantity`, `int`, `float` or iterable.
        Value of the `Datum`.
    unit : `str`
        Units of ``quantity`` as a `str` if ``quantity`` is not supplied as an
        `astropy.units.Quantity`. See http://docs.astropy.org/en/stable/units/.
    label : `str`, optional
        Label suitable for plot axes (without units).
    description : `str`, optional
        Extended description of the `Datum`.
    """
    def __init__(self, quantity=None, unit=None, label=None, description=None):
        self._label = None
        self._description = None

        self.label = label
        self.description = description

        self._quantity = None

        if quantity is None:
            self._quantity = None
        elif isinstance(quantity, astropy.units.Quantity) or \
                isinstance(quantity, basestring) or isinstance(quantity, bool):
            self.quantity = quantity
        elif unit is not None:
            self.quantity = astropy.units.Quantity(quantity, unit=unit)
        else:
            print(quantity)
            raise ValueError('`unit` argument must be supplied to Datum '
                             'if `quantity` is not an astropy.unit.Quantity.')

    @property
    def json(self):
        """Datum as a `dict` compatible with overall `Job` JSON schema."""
        if self.quantity is None:
            v = None
        elif isinstance(self.quantity, basestring) or \
                isinstance(self.quantity, bool):
            v = self.quantity
        elif len(self.quantity.shape) > 0:
            v = self.quantity.value.tolist()
        else:
            v = self.quantity.value

        d = {
            'value': v,
            'unit': self.unit_str,
            'label': self.label,
            'description': self.description
        }
        return d

    @property
    def label(self):
        """Label for plotting (without units)."""
        return self._label

    @label.setter
    def label(self, value):
        assert isinstance(value, basestring) or value is None
        self._label = value

    @property
    def description(self):
        """Extended description."""
        return self._description

    @description.setter
    def description(self, value):
        assert isinstance(value, basestring) or value is None
        self._description = value

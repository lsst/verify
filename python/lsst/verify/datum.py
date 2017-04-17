# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division
from builtins import object
from past.builtins import basestring

import numpy as np
from astropy.tests.helper import quantity_allclose
import astropy.units as u

from .jsonmixin import JsonSerializationMixin


__all__ = ['Datum', 'QuantityAttributeMixin']


class QuantityAttributeMixin(object):
    """Mixin with common attributes for classes that wrap an
    `astropy.units.Quantity`.

    Subclasses must have a self._quantity attribute that is an
    `astropy.units.Quantity`, `str`, `bool`, or `None` (only numeric values are
    astropy quantities).
    """

    @property
    def quantity(self):
        """Value of the datum (`astropy.units.Quantity`, `str`, `bool`,
           `None`)."""
        return self._quantity

    @staticmethod
    def _is_non_quantity_type(q):
        """Test if a quantity is a acceptable (`str`, `bool`, `int`, or
        `None`), but not `astropy.quantity`."""
        return isinstance(q, basestring) or isinstance(q, bool) or \
            isinstance(q, int) or q is None

    @quantity.setter
    def quantity(self, q):
        assert isinstance(q, u.Quantity) or \
            QuantityAttributeMixin._is_non_quantity_type(q)
        self._quantity = q

    @property
    def unit(self):
        """Read-only `astropy.units.Unit` of the `quantity`.

        If the `quantity` is a `str` or `bool`, the unit is `None`.
        """
        q = self.quantity
        if QuantityAttributeMixin._is_non_quantity_type(q):
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
            fmtr = u.format.Latex()
            return fmtr.to_string(self.unit)
        else:
            return ''

    @staticmethod
    def _rebuild_quantity(value, unit):
        """Rebuild a quantity from the value and unit serialized to JSON.

        Parameters
        ----------
        value : `list`, `float`, `int`, `str`, `bool`
            Serialized quantity value.
        unit : `str`
            Serialized quantity unit string.

        Returns
        -------
        q : `astropy.units.Quantity`, `str`, `int`, `bool` or `None`
            Astropy quantity.
        """
        if QuantityAttributeMixin._is_non_quantity_type(value):
            _quantity = value
        elif isinstance(value, list):
            # an astropy quantity array
            _quantity = np.array(value) * u.Unit(unit)
        else:
            # scalar astropy quantity
            _quantity = value * u.Unit(unit)
        return _quantity


class Datum(QuantityAttributeMixin, JsonSerializationMixin):
    """A value annotated with units, a plot label and description.

    Datum supports natively support Astropy `~astropy.units.Quantity` and
    units. In addition, a Datum can also wrap strings, booleans and integers.
    A Datums's value can also be `None`.

    Parameters
    ----------
    quantity : `astropy.units.Quantity`, `int`, `float` or iterable.
        Value of the `Datum`.
    unit : `str`
        Units of ``quantity`` as a `str` if ``quantity`` is not supplied as an
        `astropy.units.Quantity`. See http://docs.astropy.org/en/stable/units/.
        Units are not used by `str`, `bool`, `int` or `None` types.
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

        if isinstance(quantity, u.Quantity) or \
                QuantityAttributeMixin._is_non_quantity_type(quantity):
            self.quantity = quantity
        elif unit is not None:
            self.quantity = u.Quantity(quantity, unit=unit)
        else:
            raise ValueError('`unit` argument must be supplied to Datum '
                             'if `quantity` is not an astropy.unit.Quantity, '
                             'str, bool, int or None.')

    @classmethod
    def deserialize(cls, label=None, description=None, value=None, unit=None):
        """Deserialize fields from a Datum JSON object into a `Datum` instance.

        Parameters
        ----------
        value : `float`, `int`, `bool`, `str`, or `list`
            Values, which may be scalars or lists of scalars.
        unit : `str` or `None`
            An `astropy.units`-compatible string with units of ``value``,
            or `None` if the value does not have physical units.
        label : `str`, optional
            Label suitable for plot axes (without units).
        description : `str`, optional
            Extended description of the `Datum`.

        Returns
        -------
        datum : `Datum`
            Datum instantiated from provided JSON fields.

        Examples
        --------
        With this class method, a `Datum` may be round-tripped from its
        JSON serialized form.

        >>> datum = Datum(50. * u.mmag, label='sigma',
        ...               description="Photometric uncertainty.")
        >>> print(datum)
        sigma = 50.0 mmag
        Photometric uncertainty.
        >>> json_data = datum.json
        >>> new_datum = datum.deserialize(**json_data)
        >>> print(new_datum)
        sigma = 50.0 mmag
        Photometric uncertainty.
        """
        return cls(quantity=value, unit=unit, label=label,
                   description=description)

    @classmethod
    def from_json(cls, json_data):
        """Construct a Datum from a JSON dataset.

        Parameters
        ----------
        json_data : `dict`
            Datum JSON object.

        Returns
        -------
        datum : `Datum`
            Datum from JSON.
        """
        q = Datum._rebuild_quantity(json_data['value'], json_data['unit'])
        d = cls(quantity=q, label=json_data['label'],
                description=json_data['description'])
        return d

    @property
    def json(self):
        """Datum as a `dict` compatible with overall `Job` JSON schema."""
        if QuantityAttributeMixin._is_non_quantity_type(self.quantity):
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

    def __eq__(self, other):
        if self.label != other.label:
            return False

        if self.description != other.description:
            return False

        if isinstance(self.quantity, u.Quantity):
            if not quantity_allclose(self.quantity, other.quantity):
                return False
        else:
            if self.quantity != other.quantity:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        template = ''
        if self.label is not None:
            template += '{self.label} = '
        template += '{self.quantity}'
        if self.description is not None:
            template += '\n{self.description}'
        return template.format(self=self)

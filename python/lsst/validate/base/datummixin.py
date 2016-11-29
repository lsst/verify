# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import astropy.units
from .datum import Datum


__all__ = ['DatumAttributeMixin']


class DatumAttributeMixin(object):
    """Mixin that provides a `~lsst.validate.base.Datum`-like API to
    non-`~lsst.validate.base.Datum` classes.
    """

    def _register_datum_attribute(self, attribute, key, quantity=None,
                                  label=None, description=None,
                                  datum=None):
        _value = None
        _label = None
        _description = None

        if datum is not None:
            assert isinstance(datum, Datum)
            _value = datum.quantity
            _label = datum.label
            _description = datum.description

        if quantity is not None and _value is None:
            assert isinstance(quantity, astropy.units.Quantity) or \
                isinstance(quantity, str) or isinstance(quantity, bool) or \
                isinstance(quantity, int)
            _value = quantity

        if description is not None:
            _description = description

        if label is not None:
            _label = label

        # Use parameter name as label if necessary
        if _label is None:
            _label = key

        attribute[key] = Datum(_value, label=_label, description=_description)

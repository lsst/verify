# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from .datum import Datum


__all__ = ['DatumAttributeMixin']


class DatumAttributeMixin(object):
    """Mixin that provides a `~lsst.validate.base.Datum`-like API to
    non-`~lsst.validate.base.Datum` classes.
    """

    def _register_datum_attribute(self, attribute, key, value=None,
                                  units=None, label=None, description=None,
                                  datum=None):
        _value = None
        _units = None
        _label = None
        _description = None

        # default to values from Datum
        if datum is not None:
            _label = datum.label
            _description = datum.description
            _units = datum.units
            _value = datum.value

        # Apply overrides if arguments are supplied
        if value is not None:
            _value = value

        if units is not None:
            _units = units

        if description is not None:
            _description = description

        if label is not None:
            _label = label

        # Use parameter name as label if necessary
        if _label is None:
            _label = key

        attribute[key] = Datum(
            _value, units=_units, label=_label, description=_description)

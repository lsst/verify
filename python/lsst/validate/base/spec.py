# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import astropy.units as u

from .jsonmixin import JsonSerializationMixin
from .datum import Datum, QuantityAttributeMixin


__all__ = ['Specification']


class Specification(QuantityAttributeMixin, JsonSerializationMixin):
    """A specification level, or threshold, associated with a `Metric`.

    Parameters
    ----------
    name : `str`
        Name of the specification level for a metric. LPM-17, for example,
        uses ``'design'``, ``'minimum'`` and ``'stretch'`` terminology.
    quantity : `astropy.units.Quantity`, `float`, or `int`
        The specification threshold level.
    unit : `str`, optional
        `astropy.units.Unit`-compatible `str` describing the units of
        ``value`` (only necessary if `quantity` is a `float`).
        An empty string (``''``) describes a unitless quantity.
    filter_names : `list`, optional
        A list of optical filter names that this specification applies to.
        Set only if the specification level is dependent on the filter.
    dependencies : `dict`, optional
        A dictionary of named `Datum` values that must be known when making a
        measurement against a specification level. Dependencies can be
        accessed as attributes of the specification object. The names of
        class attributes match keys in `dependencies`.
    """

    name = None
    """Name of the specification level for a metric.

    LPM-17, for example, uses ``'design'``, ``'minimum'`` and ``'stretch'``
    terminology.
    """

    quantity = None
    """The specification threshold level (`astropy.units.Quantity`)."""

    filter_names = None
    """`list` of names of optical filters that this Specification level
    applies to.

    Default is `None` if the `Specification` is filter-independent.
    """

    dependencies = None
    """`dict` of named `Datum` values that must be known when making a
    measurement against a specification level.

    Dependencies can also be accessed as attributes of the `Specification`
    object. The names of class attributes match keys in `dependencies`.
    """

    def __init__(self, name, quantity, unit=None, filter_names=None,
                 dependencies=None):
        self.name = name
        if unit is not None:
            self.quantity = quantity * u.Unit(unit)
        else:
            self.quantity = quantity
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
        """Representation of this `Specification` as a `Datum`."""
        return Datum(self.quantity, label=self.name)

    @classmethod
    def from_json(cls, json_data):
        """Construct a Specification from a JSON document.

        Parameters
        ----------
        json_data : `dict`
            Specification JSON object.

        Returns
        -------
        specification : `Specification`
            Specification from JSON.
        """
        q = Datum._rebuild_quantity(json_data['value'], json_data['unit'])
        deps = {k: Datum.from_json(v)
                for k, v in json_data['dependencies'].items()}
        s = cls(name=json_data['name'],
                quantity=q,
                filter_names=json_data['filter_names'],
                dependencies=deps)
        return s

    @property
    def json(self):
        """`dict` that can be serialized as semantic JSON, compatible with
        the SQUASH metric service.
        """
        if isinstance(self.quantity, u.Quantity):
            v = self.quantity.value
        else:
            v = self.quantity
        return JsonSerializationMixin.jsonify_dict({
            'name': self.name,
            'value': v,
            'unit': self.unit_str,
            'filter_names': self.filter_names,
            'dependencies': self.dependencies})

#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
from __future__ import print_function, division

__all__ = ['Metric']

from past.builtins import basestring

import astropy.units as u

from .jsonmixin import JsonSerializationMixin
from .naming import Name


class Metric(JsonSerializationMixin):
    """Container for the definition of a metric.

    Metrics can either be instantiated programatically, or from a :ref:`metric
    YAML file <verify-metric-yaml>` with the `from_yaml` class method.

    .. seealso::

       See the :ref:`verify-using-metrics` page for usage details.

    Parameters
    ----------
    name : `str`
        Name of the metric (e.g., ``'PA1'``).
    description : `str`
        Short description about the metric.
    unit : `str` or `astropy.units.Unit`
        Units of the metric. `Measurements` of this metric must be in an
        equivalent (i.e. convertable) unit. Argument can either be a
        `~astropy.unit.Unit` instance, or a an astropy.unit.Unit-compatible
        string representation. Use an empty string, ``''``, or
        ``astropy.units.dimensionless_unscaled`` for a unitless quantity.
    tags : `list` of `str`
        Tags associated with this metric. Tags are user-submitted string
        tokens that are used to group metrics.
    reference_doc : `str`, optional
        The document handle that originally defined the metric
        (e.g., ``'LPM-17'``).
    reference_url : `str`, optional
        The document's URL.
    reference_page : `str`, optional
        Page where metric in defined in the reference document.
    """

    description = None
    """Short description of the metric (`str`)."""

    reference_doc = None
    """Name of the document that specifies this metric (`str`)."""

    reference_url = None
    """URL of the document that specifies this metric (`str`)."""

    reference_page = None
    """Page number in the document that specifies this metric (`int`)."""

    def __init__(self, name, description, unit, tags=None,
                 reference_doc=None, reference_url=None, reference_page=None):
        self.name = name
        self.description = description
        self.unit = u.Unit(unit)
        if tags is None:
            self.tags = set()
        else:
            # FIXME DM-8477 Need type checking that tags are actually strings
            # and are a set.
            self.tags = tags
        self.reference_doc = reference_doc
        self.reference_url = reference_url
        self.reference_page = reference_page

    @classmethod
    def deserialize(cls, name=None, description=None, unit=None,
                    tags=None, reference=None):
        """Create a Metric instance from a parsed YAML/JSON document.

        Parameters
        ----------
        kwargs : `dict`
            Keyword arguments that match fields from the `Metric.json`
            serialization.

        Returns
        -------
        metric : `Metric`
            A Metric instance.
        """
        # keyword args for Metric __init__
        args = {
            'unit': unit,
            'tags': tags,
            # Remove trailing newline from folded block description field.
            # This isn't necessary if the field is trimmed with `>-` in YAML,
            # but won't hurt either.
            'description': description.rstrip('\n')
        }

        if reference is not None:
            args['reference_doc'] = reference.get('doc', None)
            args['reference_page'] = reference.get('page', None)
            args['reference_url'] = reference.get('url', None)

        return cls(name, **args)

    def __eq__(self, other):
        return ((self.name == other.name) and
                (self.unit == other.unit) and
                (self.tags == other.tags) and
                (self.description == other.description) and
                (self.reference == other.reference))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        # self.unit_str provides the astropy.unit.Unit's string representation
        # that can be used to create a new Unit. But for readability,
        # we use 'dimensionless_unscaled' (an member of astropy.unit) rather
        # than an empty string for the Metric's string representation.
        if self.unit_str == '':
            unit_str = 'dimensionless_unscaled'
        else:
            unit_str = self.unit_str
        return '{self.name!s} ({unit_str}): {self.description}'.format(
            self=self, unit_str=unit_str)

    @property
    def name(self):
        """Metric's name (`Name`)."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = Name(metric=value)

    @property
    def unit(self):
        """The metric's unit (`astropy.units.Unit`)."""
        return self._unit

    @unit.setter
    def unit(self, value):
        if not isinstance(value, (u.UnitBase, u.FunctionUnitBase)):
            message = ('unit attribute must be an astropy.units.Unit-type. '
                       ' Currently type {0!s}.'.format(type(value)))
            if isinstance(value, basestring):
                message += (' Set the `unit_str` attribute instead for '
                            'assigning the unit as a string')
            raise ValueError(message)
        self._unit = value

    @property
    def unit_str(self):
        """The string representation of the metric's unit
        (`~astropy.unit.Unit`-compatible `str`).
        """
        return str(self.unit)

    @unit_str.setter
    def unit_str(self, value):
        self.unit = u.Unit(value)

    @property
    def tags(self):
        """Tag labels (`set` of `str`)."""
        return self._tags

    @tags.setter
    def tags(self, t):
        # Ensure that tags is always a set.
        if isinstance(t, basestring):
            t = [t]
        self._tags = set(t)

    @property
    def reference(self):
        """Documentation reference as human-readable text (`str`, read-only).

        Uses `reference_doc`, `reference_page`, and `reference_url`, as
        available.
        """
        ref_str = ''
        if self.reference_doc and self.reference_page:
            ref_str = '{doc}, p. {page:d}'.format(doc=self.reference_doc,
                                                  page=self.reference_page)
        elif self.reference_doc:
            ref_str = self.reference_doc

        if self.reference_url and self.reference_doc:
            ref_str += ', {url}'.format(url=self.reference_url)
        elif self.reference_url:
            ref_str = self.reference_url

        return ref_str

    @property
    def json(self):
        """`dict` that can be serialized as semantic JSON, compatible with
        the SQUASH metric service.
        """
        ref_doc = {
            'doc': self.reference_doc,
            'page': self.reference_page,
            'url': self.reference_url}
        return JsonSerializationMixin.jsonify_dict({
            'name': str(self.name),
            'description': self.description,
            'unit': self.unit_str,
            'tags': self.tags,
            'reference': ref_doc})

    def check_unit(self, quantity):
        """Check that a `~astropy.units.Quantity` has equivalent units to
        this metric.

        Parameters
        ----------
        quantity : `astropy.units.Quantity`
            Quantity to be tested.

        Returns
        -------
        is_equivalent : `bool`
            `True` if the units are equivalent, meaning that the quantity
            can be presented in the units of this metric. `False` if not.
        """
        if not quantity.unit.is_equivalent(self.unit):
            return False
        else:
            return True

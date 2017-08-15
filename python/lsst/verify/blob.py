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

__all__ = ['Blob']

from past.builtins import basestring

import uuid

from .jsonmixin import JsonSerializationMixin
from .datum import Datum


class Blob(JsonSerializationMixin):
    """Blob is a flexible container of data, as `lsst.verify.Datum` \s, that
    are serializable to JSON.

    Parameters
    ----------
    name : `str`
        Name of this type of blob. Blobs from one pipeline Job execution to
        another that share the same name generally share the same schema of
        `lsst.verify.Datum`\ s.
    datums : `dict` of `lsst.verify.Datum`-types, optional
        Keys are names of datums. Values are `~lsst.verify.Datum`\ -types.
        Each `~lsst.verify.Datum` can be later retrived from the Blob instance
        by key.
    """

    def __init__(self, name, **datums):
        # Internal read-only instance ID, access with the name attribute
        self._id = uuid.uuid4().hex

        if not isinstance(name, basestring):
            message = 'Blob name {0!r} must be a string'.format(name)
            raise TypeError(message)
        self._name = name

        # Internal Datum dictionary
        self._datums = {}

        for key, datum in datums.items():
            self[key] = datum

    @property
    def name(self):
        """Name of this blob (`str`)."""
        return self._name

    @property
    def identifier(self):
        """Unique UUID4-based identifier for this blob (`str`)."""
        return self._id

    @classmethod
    def deserialize(cls, identifier=None, name=None, data=None):
        """Deserialize fields from a blob JSON object into a `Blob` instance.

        Parameters
        ----------
        identifier : `str`
            Blob identifier.
        name : `str`
            Name of the blob type.
        data : `dict`
            Dictionary of named ``name: datum object`` key-value pairs.

        Returns
        -------
        blob : `Blob`
            The `Blob` instance deserialied from a blob JSON object.

        Example
        -------
        This class method is designed to roundtrip JSON objects created a
        Blob instance. For example:

        >>> import astropy.units as u
        >>> blob = Blob('demo')
        >>> blob['a_mag'] = Datum(28 * u.mag, label='i')
        >>> json_data = blob.json
        >>> new_blob = Blob.deserialize(**json_data)
        """
        datums = {}
        if data is not None:
            for datum_key, datum_doc in data.items():
                datum = Datum.deserialize(**datum_doc)
                datums[datum_key] = datum
        instance = cls(name, **datums)
        instance._id = identifier
        return instance

    @property
    def json(self):
        """Job data as a JSON-serializable `dict`."""
        json_doc = JsonSerializationMixin.jsonify_dict({
            'identifier': self.identifier,
            'name': self.name,
            'data': self._datums})
        return json_doc

    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            message = 'Key {0!r} is not a string.'.format(key)
            raise KeyError(message)

        if not isinstance(value, Datum):
            message = '{0} is not a Datum-type'.format(value)
            raise TypeError(message)

        self._datums[key] = value

    def __getitem__(self, key):
        return self._datums[key]

    def __delitem__(self, key):
        del self._datums[key]

    def __len__(self):
        return len(self._datums)

    def __contains__(self, key):
        return key in self._datums

    def __iter__(self):
        for key in self._datums:
            yield key

    def __eq__(self, other):
        return (self.identifier == other.identifier) \
            and (self.name == other.name) \
            and (self._datums == other._datums)

    def __ne__(self, other):
        return not self.__eq__(other)

    def keys(self):
        """Get keys of blob items.

        Returns
        -------
        keys : sequence of `str`
            Sequence of keys to items in the Blob.
        """
        return self._datums.keys()

    def items(self):
        """Get pairs of keys and values in the Blob.

        Yields
        ------
        keyval : tuple
            Tuple of:

            - key (`str`)
            - datum (`lsst.verify.Datum`)
        """
        for key, val in self._datums.items():
            yield key, val

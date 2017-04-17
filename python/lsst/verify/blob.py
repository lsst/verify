# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from past.builtins import basestring

import uuid

from .jsonmixin import JsonSerializationMixin
from .datum import Datum


__all__ = ['Blob']


class Blob(JsonSerializationMixin):
    """Blobs is a flexible container of data, as Datums, that are serializable
    to JSON.

    .. seealso::

       The page :ref:`verify-creating-blobs` describes how to create
       blob classes.

    Parameters
    ----------
    name : `str`
        Name of this type of blob. Blobs that share the same name generally
        share the same schema of Datums.
    datums : `dict` of `Datum`-types, optional
        Datum-types. Each `Datum` can be later retrived from the Blob by key.
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

    @classmethod
    def from_json(cls, json_data):
        """Construct a Blob from a JSON dataset.

        Parameters
        ----------
        json_data : `dict`
            Blob JSON object.

        Returns
        -------
        blob : `Blob`-type
            Blob from JSON.
        """
        datums = {k: Datum.from_json(v) for k, v in json_data['data'].items()}
        instance = cls(json_data['name'], **datums)

        # Insert the unique identifier to match the serialized blob
        instance._id = json_data['identifier']

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

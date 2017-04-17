# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

__all__ = ['BlobSet']

from .blob import Blob
from .jsonmixin import JsonSerializationMixin


class BlobSet(JsonSerializationMixin):
    """A collection of Blobs.

    Parameters
    ----------
    blobs : `list` of `lsst.verify.Blob`\ s
        Blobs to include in the set.
    """

    def __init__(self, blobs=None):
        # internal dict of Blobs
        self._items = {}
        # internal mapping of blob names to identifiers
        self._name_map = {}

        if blobs is not None:
            for blob in blobs:
                self.insert(blob)

    @classmethod
    def deserialize(cls, blobs=None):
        """Create a BlobSet from a parsed JSON dataset.

        Parameters
        ----------
        blobs : `list`, optional
            A list of blob JSON serializations.

        Returns
        -------
        instance : `BlobSet`
            A `BlobSet` instance.
        """
        instance = cls()
        if blobs is None:
            blobs = []
        for blob_doc in blobs:
            blob = Blob.deserialize(**blob_doc)
            instance.insert(blob)
        return instance

    def __getitem__(self, key):
        try:
            # key may be a blob's name, rather than identifier
            key = self._name_map[key]
        except KeyError:
            pass

        return self._items[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Blob):
            message = ('Blob {0} is not a '
                       'lsst.verify.Blob-type')
            raise TypeError(message.format(value))

        if key != value.identifier:
            message = ("Key {0} is inconsistent with the blob's "
                       "identifier, {1}")
            raise KeyError(message.format(key, value.identifier))

        self._items[key] = value
        self._name_map[value.name] = key

    def __len__(self):
        return len(self._items)

    def __contains__(self, key):
        try:
            # key may be a blob's name, rather than identifier
            key = self._name_map[key]
        except KeyError:
            pass

        return key in self._items

    def __delitem__(self, key):
        try:
            # key may be a blob's name, rather than identifier
            key = self._name_map[key]
        except KeyError:
            pass

        del self._items[key]

    def __iter__(self):
        for key in self._items:
            yield key

    def __eq__(self, other):
        return self._items == other._items

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        count = len(self)
        if count == 0:
            count_str = 'empty'
        elif count == 1:
            count_str = '1 Blob'
        else:
            count_str = '{count:d} Blobs'.format(count=count)
        return '<BlobSet: {0}>'.format(count_str)

    def items(self):
        """Iterate over (identifier, `Blob`) pairs in the set.

        Yields
        ------
        item : tuple
            Tuple containing:

            - ``identifier`` of the Blob (`str`)
            - `Blob` instance
        """
        for item in self._items.items():
            yield item

    def insert(self, blob):
        """Insert a blob into the set."""
        self[blob.identifier] = blob

    @property
    def json(self):
        """A `dict` that can be serialized as JSON."""
        json_doc = JsonSerializationMixin._jsonify_list(
            [blob for identifier, blob in self.items()]
        )
        return json_doc

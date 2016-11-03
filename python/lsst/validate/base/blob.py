# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import abc
import uuid

from .jsonmixin import JsonSerializationMixin
from .datummixin import DatumAttributeMixin
from .datum import Datum


__all__ = ['BlobBase', 'DeserializedBlob']


class BlobBase(JsonSerializationMixin, DatumAttributeMixin):
    """Base class for blobs: flexible containers of data that are serialized
    to JSON.

    .. seealso::

       The page :ref:`validate-base-creating-blobs` describes how to create
       blob classes.
    """

    datums = None
    """`dict` of `Datum` instances contained by the blob instance.

    The values of blobs can also be accessed as attributes of the `BlobBase`
    subclass. Keys in `datums` and attributes share the same names.
    """

    def __init__(self):
        self.datums = {}
        self._id = uuid.uuid4().hex

    def __getattr__(self, key):
        if key in self.datums:
            return self.datums[key].quantity
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, key))

    def __setattr__(self, key, value):
        if key != 'datums' and key in self.datums:
            # Setting value of a serialized Datum
            self.datums[key].quantity = value
        else:
            super(BlobBase, self).__setattr__(key, value)

    @abc.abstractproperty
    def name(self):
        """Name of this blob (the `BlobBase` subclass's Python namespace)."""
        pass

    @property
    def identifier(self):
        """Unique UUID4-based identifier for this blob (`str`)."""
        return self._id

    @classmethod
    def from_json(cls, json_data):
        """Construct a Blob from a JSON dataset.

        Parameters
        ----------
        json_data : `dict`
            Blob JSON object.

        Returns
        -------
        blob : `BlobBase`-type
            Blob from JSON.
        """
        datums = {k: Datum.from_json(v) for k, v in json_data['data'].items()}
        return cls(json_data['name'], json_data['identifier'], datums)

    @property
    def json(self):
        """Job data as a JSON-serializable `dict`."""
        json_doc = JsonSerializationMixin.jsonify_dict({
            'identifier': self.identifier,
            'name': self.name,
            'data': self.datums})
        return json_doc

    def register_datum(self, name, quantity=None, label=None,
                       description=None, datum=None):
        """Register a new `Datum` to be contained by, and serialized via,
        this blob.

        The value of the `Datum` can either be set at registration time (with
        the ``quantity`` or ``datum`` arguments) or later by setting the instance
        attribute named ``name``.

        Values of `Datum`\ s can always be accessed or updated through instance
        attributes.

        The full `Datum` object can be accessed as items of the `datums`
        dictionary attached to this class. This method is useful for accessing
        or updating metadata about a `Datum`, such as: `~Datum.unit`,
        `~Datum.label`, or `~Datum.description`.

        Parameters
        ----------
        name : `str`
            Name of the `Datum`; used as the key in the `datums` attribute of
            this object.
        value : obj
            Value of the `Datum`.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            `name` is used as the ``label``. Setting this label argument
            overrides this default.
        description : `str`, optional
            Extended description.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, units and label will be
            used unless overriden by other arguments to `register_datum`.
        """
        self._register_datum_attribute(self.datums, name,
                                       quantity=quantity, label=label,
                                       description=description, datum=datum)


class DeserializedBlob(BlobBase):
    """A concrete Blob deserialized from JSON.

    This class should only be used internally.
    """

    name = None

    def __init__(self, name, id_, datums):
        BlobBase.__init__(self)
        self.name = name
        self._id = id_
        self.datums = datums

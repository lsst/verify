# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import abc
import uuid

from .jsonmixin import JsonSerializationMixin
from .datummixin import DatumAttributeMixin


__all__ = ['BlobBase']


class BlobBase(JsonSerializationMixin, DatumAttributeMixin):
    """Base class for Blob classes.

    Blobs are flexible containers of data that are serialized to JSON.

    Attributes
    ----------
    datums : dict
        A `dict` of `Datums` instances contained by the Blob instance. The
        values of blobs can also be accessed as attributes of the BlobBase
        subclass. Keys in `datums` and attributes share the same names.
    identifier : str
        Unique identifier for this blob instance
    name : str
        Name of the Blob class.
    """

    def __init__(self):
        self.datums = {}
        self._id = uuid.uuid4().hex

    def __getattr__(self, key):
        if key in self.datums:
            return self.datums[key].value
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, key))

    def __setattr__(self, key, value):
        if key != 'datums' and key in self.datums:
            # Setting value of a serialized Datum
            self.datums[key].value = value
        else:
            super(BlobBase, self).__setattr__(key, value)

    @abc.abstractproperty
    def name(self):
        """Name of this blob (the BlobBase subclass's Python namespace)."""
        pass

    @property
    def identifier(self):
        """A unique UUID4-based identifier for this blob (`str`)."""
        return self._id

    @property
    def json(self):
        """Job data as a JSON-serialiable `dict`."""
        json_doc = JsonSerializationMixin.jsonify_dict({
            'identifer': self.identifier,
            'name': self.name,
            'data': self.datums})
        return json_doc

    def register_datum(self, name, value=None, units=None, label=None,
                       description=None, datum=None):
        """Register a new `Datum` to be contained by, and serialized via,
        this blob.

        The value of the `Datum` can either be set at registration time (with
        the `value` argument) or later by setting the instance attribute
        named `name`.

        Values of Datums can always be accessed or updated through instance
        attributes.

        The full `Datum` object can be accessed as items of the `datums`
        dictionary attached to this class. This method is useful for accessing
        or updating metadata about a datum, such as
        :attr:`~lsst.validate.drp.base.Datum.units`,
        :attr:`~lsst.validate.drp.base.Datum.label`, or
        :attr:`~lsst.validate.drp.base.Datum.description`.

        Parameters
        ----------
        name : `str`
            Name of the datum; used as the key in the `datums`
            attribute of this object.
        value : obj
            Value of the datum.
        units : `str`, optional
            An astropy-compatible unit string.
            See http://docs.astropy.org/en/stable/units/.
        label : `str`, optional
            Label suitable for plot axes (without units). By default the
            `name` is used as the `label`. Setting this label argument
            overrides this default.
        description : `str`, optional
            Extended description.
        datum : `Datum`, optional
            If a `Datum` is provided, its value, units and label will be
            used unless overriden by other arguments to `register_parameter`.
        """
        self._register_datum_attribute(self.datums, name,
                                       value=value, label=label, units=units,
                                       description=description, datum=datum)

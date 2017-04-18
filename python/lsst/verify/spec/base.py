# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

__all__ = ["Specification"]

import abc
from future.utils import with_metaclass

from ..jsonmixin import JsonSerializationMixin
from ..naming import Name


class Specification(with_metaclass(abc.ABCMeta, JsonSerializationMixin)):
    """Specification base class.

    Specification classes must implement:

    - `type`
    - `serialize_type`
    - `check`

    Subclasses should also call ``Specification.__init__`` to initialize
    the specifications ``name`` attribute (a `~lsst.verify.Name`
    instance).
    """

    def __init__(self, name, **kwargs):
        # name attibute must be a Name instance representing a specification
        if not isinstance(name, Name):
            self._name = Name(spec=name)
        else:
            self._name = name
        if not self._name.is_spec:
            message = 'name {0!r} does not represent a specification'
            raise TypeError(message.format(self._name))

    @property
    def name(self):
        """Specification name (`lsst.verify.Name`)."""
        return self._name

    @abc.abstractproperty
    def type(self):
        """Specification type (`str`)."""
        pass

    @abc.abstractmethod
    def _serialize_type(self):
        """Serialize type-specific specification data to a JSON-serializable
        `dict`.

        This method is used by the `json` property as the value associated
        with the key named for `type`.
        """
        pass

    @property
    def json(self):
        """`dict` that can be serialized as semantic JSON, compatible with
        the SQUASH metric service.
        """
        return JsonSerializationMixin.jsonify_dict(
            {
                'name': str(self.name),
                'type': self.type,
                self.type: self._serialize_type()
            }
        )

    @abc.abstractmethod
    def check(self, measurement):
        """Check if a measurement passes this specification.

        Parameters
        ----------
        measurement : `astropy.units.Quantity`
            The measurement value. The measurement `~astropy.units.Quantity`
            must have units *compatible* with `threshold`.

        Returns
        -------
        passed : `bool`
            `True` if the measurement meets the specification,
            `False` otherwise.
        """
        pass

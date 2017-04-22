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

__all__ = ["Specification"]

import abc
from future.utils import with_metaclass

from ..jsonmixin import JsonSerializationMixin
from ..metaquery import MetadataQuery
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

        if 'metadata_query' in kwargs:
            self.metadata_query = MetadataQuery(kwargs['metadata_query'])
        else:
            self.metadata_query = MetadataQuery()

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
                self.type: self._serialize_type(),
                'metadata_query': self.metadata_query
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

    def query_metadata(self, metadata):
        """Query a Job's metadata to determine if this specification applies.

        Parameters
        ----------
        metadata : `lsst.verify.Metadata` or `dict`-type
            Metadata mapping. Typically this is the `lsst.verify.Job.meta`
            attribute.

        Returns
        -------
        applies : `bool`
            `True` if this specification applies to a Job's measurement, or
            `False` otherwise.
        """
        return self.metadata_query(metadata)

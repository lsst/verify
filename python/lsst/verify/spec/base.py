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

__all__ = ["Specification"]

import abc
from future.utils import with_metaclass
from past.builtins import basestring

from ..jsonmixin import JsonSerializationMixin
from ..metaquery import MetadataQuery
from ..naming import Name


class Specification(with_metaclass(abc.ABCMeta, JsonSerializationMixin)):
    """Specification base class.

    Specification classes must implement:

    - `type`
    - `_serialize_type`
    - `check`

    Subclasses should also call ``Specification.__init__`` to initialize
    the specifications ``name`` attribute (a `~lsst.verify.Name`
    instance).
    """

    def __init__(self, name, **kwargs):
        # interal object behind self.tags
        self._tags = set()

        # name attibute must be a Name instance representing a specification
        if not isinstance(name, Name):
            self._name = Name(spec=name)
        else:
            self._name = name
        if not self._name.is_spec:
            message = 'name {0!r} does not represent a specification'
            raise TypeError(message.format(self._name))

        if 'metadata_query' in kwargs:
            self._metadata_query = MetadataQuery(kwargs['metadata_query'])
        else:
            self._metadata_query = MetadataQuery()

        if 'tags' in kwargs:
            self.tags = kwargs['tags']

    @property
    def name(self):
        """Specification name (`lsst.verify.Name`)."""
        return self._name

    @property
    def metric_name(self):
        """Name of the metric this specification corresponds to
        (`lsst.verify.Name`)."""
        return Name(package=self.name.package, metric=self.name.metric)

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
                'metadata_query': self._metadata_query,
                'tags': self.tags
            }
        )

    @abc.abstractmethod
    def check(self, measurement):
        """Check if a measurement passes this specification.

        Parameters
        ----------
        measurement : `astropy.units.Quantity`
            The measurement value. The measurement `~astropy.units.Quantity`
            must have units *compatible* with the specification.

        Returns
        -------
        passed : `bool`
            `True` if the measurement meets the specification,
            `False` otherwise.
        """
        pass

    def query_metadata(self, metadata, arg_driven=False):
        """Query a Job's metadata to determine if this specification applies.

        Parameters
        ----------
        metadata : `lsst.verify.Metadata` or `dict`-type
            Metadata mapping. Typically this is the `lsst.verify.Job.meta`
            attribute.
        arg_driven : `bool`, optional
            If `False` (default), ``metadata`` matches the ``MetadataQuery``
            if ``metadata`` has all the terms defined in ``MetadataQuery``,
            and those terms match. If ``metadata`` has more terms than
            ``MetadataQuery``, it can still match. This behavior is
            appropriate for finding if a specification applies to a Job
            given metadata.

            If `True`, the orientation of the matching is reversed. Now
            ``metadata`` matches the ``MetadataQuery`` if ``MetadataQuery``
            has all the terms defined in ``metadata`` and those terms match.
            If ``MetadataQuery`` has more terms than ``metadata``, it can
            still match. This behavior is appropriate for discovering
            specifications.

        Returns
        -------
        matched : `bool`
            `True` if this specification matches, `False` otherwise.

        See also
        --------
        lsst.verify.MetadataQuery
        """
        return self._metadata_query(metadata, arg_driven=arg_driven)

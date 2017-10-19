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

__all__ = ['MetadataQuery']

from .jsonmixin import JsonSerializationMixin


class MetadataQuery(JsonSerializationMixin):
    """Query of `lsst.verify.Job.meta` metadata.

    Parameters
    ----------
    terms : `dict`, optional
        A mapping of key-value query terms. In the default query mode, the
        user-provided job metadata must have all these terms, and matching
        values, to pass the query.

    Examples
    --------
    A MetadataQuery returns `True` if all key-value terms found in
    `MetadataQuery.terms` are equal to key-value metadata items.

    >>> metadata = {'filter': 'r', 'camera': 'MegaCam'}

    An example of a query with a conflicting term:

    >>> query1 = MetadataQuery({'filter': 'r', 'camera': 'SDSS'})
    >>> query1(metadata)
    False

    A query with matching terms (albeit, a subset of the metadata):

    >>> query2 = MetadataQuery({'filter': 'r'})
    >>> query2(metadata)
    True

    A query that overconstrains the available metadata:

    >>> query3 = MetadataQuery({'filter': 'r', 'camera': 'MegaCam',
    ...                         'photometric': True})
    >>> query3(metadata)
    False

    The ``arg_driven=True`` mode reverses the matching logic so that all terms
    in the user-provided metadata must be in the MetadataQuery:

    >>> query3(metadata, arg_driven=True)
    True
    >>> query2(metadata, arg_driven=True)
    False
    """

    terms = None
    """Term mapping (`dict`). Metadata must have all keys and corresponding
    values.
    """

    def __init__(self, terms=None):
        self.terms = terms or dict()

    def __call__(self, metadata, arg_driven=False):
        """Determine if a metadata set matches the query terms.

        Parameters
        ----------
        metadata : `dict` or `lsst.verify.Metadata`
            Metadata mapping. Typically this is a job's
            `lsst.verify.Job.meta`.

        arg_driven : `bool`, optional
            If `False` (default), ``metadata`` matches the ``MetadataQuery``
            if ``metadata`` has all the terms defined in ``MetadataQuery``,
            and those terms match. If ``metadata`` has more terms than
            ``MetadataQuery``, it can still match.

            If `True`, the orientation of the matching is reversed. Now
            ``metadata`` matches the ``MetadataQuery`` if ``MetadataQuery``
            has all the terms defined in ``metadata`` and those terms match.
            If ``MetadataQuery`` has more terms than ``metadata``, it can
            still match.

        Returns
        -------
        match : `bool`
            `True` if the metadata matches the query terms; `False` otherwise.
        """
        if arg_driven:
            # Match if self.terms has all the terms defined in metadata
            for arg_term, arg_term_value in metadata.items():
                if arg_term not in self.terms:
                    return False

                # If metadata can be floats, may need to do more sophisticated
                # comparison
                if arg_term_value != self.terms[arg_term]:
                    return False
        else:
            # Match if metadata has all the terms defined in this MetadataQuery
            for term_key, term_value in self.terms.items():
                if term_key not in metadata:
                    return False

                # If metadata can be floats, may need to do more sophisticated
                # comparison
                if term_value != metadata[term_key]:
                    return False

        return True

    def __eq__(self, other):
        return self.terms == other.terms

    def __str__(self):
        return str(self.terms)

    def __repr__(self):
        template = 'MetadataQuery({0!r})'
        return template.format(self.terms)

    @property
    def json(self):
        """A JSON-serializable dict.

        Keys are metadata keys. Values are the associated metadata values
        of the query term.
        """
        return self.jsonify_dict(self.terms)

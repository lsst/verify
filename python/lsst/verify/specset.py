# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from past.builtins import basestring

from .spec.base import Specification
from .naming import Name

__all__ = ['SpecificationSet']


class SpecificationSet(object):
    """A collection of Specifications.

    Parameters
    ----------
    specifications : `list` or `tuple` of `Specification` instances
        A sequence of `Specification` instances.
    partials : `list` or `tuple` of `SpecificationPartial` instances
        A sequence of `SpecificationPartial` instances. These partials
        can be used as bases for specification definitions.
    """

    def __init__(self, specifications=None, partials=None):
        # Specifications, keyed by Name (a specification name)
        self._specs = {}

        # SpecificationPartial instances, keyed by the fully-qualified
        # name: ``package_name:yaml_id#name``.
        self._partials = {}

        if specifications is not None:
            for spec in specifications:
                if not isinstance(spec, Specification):
                    message = '{0!r} must be a Specification type'
                    raise TypeError(message.format(spec))

                self._specs[spec.name] = spec

        if partials is not None:
            for partial in partials:
                if not isinstance(partial, SpecificationPartial):
                    message = '{0!r} must be a SpecificationPartial type'
                    raise TypeError(message.format(partial))

                self._partials[partial.name] = partial

    def __str__(self):
        count = len(self)
        if count == 0:
            count_str = 'empty'
        elif count == 1:
            count_str = '1 Specification'
        else:
            count_str = '{count:d} Specifications'.format(count=count)
        return '<SpecificationSet: {0}>'.format(count_str)

    def __len__(self):
        """Number of `Specifications` in the set."""
        return len(self._specs)

    def __contains__(self, name):
        """Check if the set contains a `Specification` by name."""
        if isinstance(name, basestring) and '#' in name:
            # must be a partial's name
            return name in self._partials

        else:
            # must be a specification.
            if not isinstance(name, Name):
                name = Name(spec=name)

            return name in self._specs

    def __getitem__(self, name):
        """Retrive a Specification or a SpecificationPartial."""
        if isinstance(name, basestring) and '#' in name:
            # must be a partial's name
            return self._partials[name]

        else:
            # must be a specification.
            if not isinstance(name, Name):
                name = Name(spec=name)

            if not name.is_spec:
                message = 'Expected key {0!r} to resolve a specification'
                raise KeyError(message.format(name))

            return self._specs[name]


class SpecificationPartial(object):
    """A specification definition partial, used when parsing specification
    YAML repositories.
    """

    def __init__(self, yaml_doc):
        self.yaml_doc = yaml_doc
        self.name = self.yaml_doc.pop('id')

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    @property
    def json(self):
        """JSON-serializable representation of the partial."""
        # This API is for compatibility with Specification classes
        return self.yaml_doc

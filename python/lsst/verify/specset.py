# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from past.builtins import basestring

from collections import OrderedDict

from .spec.base import Specification
from .naming import Name
from .errors import SpecificationResolutionError
from .yamlutils import merge_documents

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

    def resolve_document(self, spec_doc):
        """Resolve inherited properties in a specification document using
        specifications available in the repo.

        Parameters
        ----------
        spec_doc : `dict`
            A specification document. A document is typically either a YAML
            document, where the specification is defined, or a JSON object
            that was serialized from a `~lsst.validate.base.Specification`
            instance.

        Returns
        -------
        spec_doc : `OrderedDict`
            The specification document is returned with bases resolved.

        Raises
        ------
        SpecificationResolutionError
           Raised when a document's bases cannot be resolved (an inherited
           `~lsst.validate.base.Specification` cannot be found in the repo).
        """
        # Goal is to process all specifications and partials mentioned in
        # the 'base' field (first in, first out) and merge their information
        # to the spec_doc.
        if 'base' in spec_doc:
            # Coerce 'base' field into a list for consistency
            if isinstance(spec_doc['base'], basestring):
                spec_doc['base'] = [spec_doc['base']]

            built_doc = OrderedDict()

            # Process all base dependencies into the specification
            # document until all are merged
            while len(spec_doc['base']) > 0:
                # Select first base (first in, first out queue)
                base_name = spec_doc['base'][0]

                # Get the base: it's either another specification or a partial
                if '#' in base_name:
                    # We make base names fully qualifed when loading them
                    try:
                        base_spec = self._partials[base_name]
                    except KeyError:
                        # Abort because this base is not available yet
                        raise SpecificationResolutionError

                else:
                    # Must be a specification.
                    # Resolve its name (use package info from present doc since
                    # they're consistent).
                    base_name = Name(package=spec_doc['package'],
                                     spec=base_name)
                    # Try getting the specification from the repo
                    try:
                        base_spec = self[base_name]
                    except KeyError:
                        # Abort because this base is not resolved
                        # or not yet available
                        raise SpecificationResolutionError

                # Merge this spec_doc onto the base document using
                # our inheritance algorithm
                built_doc = merge_documents(built_doc, base_spec.json)

                # Mix in metric information if available. This is useful
                # because a specification may only assume its metric
                # identity from inheritance.
                try:
                    built_doc['metric'] = base_spec.name.metric
                except AttributeError:
                    # base spec must be a partial
                    pass

                # Remove this base spec from the queue
                del spec_doc['base'][0]

            # if base list is empty remove it so we don't loop over it again
            if len(spec_doc['base']) == 0:
                del spec_doc['base']

            # Merge this spec_doc onto the base document using
            # our inheritance algorithm
            built_doc = merge_documents(built_doc, spec_doc)

            return built_doc

        else:
            # No inheritance to resolve
            return spec_doc


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

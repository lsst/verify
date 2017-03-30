# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

from past.builtins import basestring

from collections import OrderedDict
import os
import re

from .spec.base import Specification
from .naming import Name
from .errors import SpecificationResolutionError
from .yamlutils import merge_documents, load_all_ordered_yaml

__all__ = ['SpecificationSet']


# Pattern for SpecificationPartial names
# package:path#name
PARTIAL_PATTERN = re.compile('^(?:(?P<package>\S+):)'
                             '?(?P<path>\S+)?#(?P<name>\S+)$')


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

    @staticmethod
    def _load_yaml_file(yaml_file_path, package_dirname):
        """Ingest specifications and partials from a single YAML file.

        Parameters
        ----------
        yaml_file_path : `str`
            File path of the specification YAML file.
        package_dirname : `str`
            Path of the root directory for a package's specifications.

        Returns
        -------
        spec_docs : `list`
            Specification YAML documents (`~collections.OrderedDict`\ s).
        partial_docs : `list`
            Specificaton partial YAML documents
            (`~collections.OrderedDict`\ s).

        Notes
        -----
        As it loads specification and specification partial documents from
        YAML, it normalizes and enriches the documents with context necessary
        for constructing Specification and SpecificationPartial instances
        in other methods:

        - A ``'package`` field is added.
        - A ``'metric'`` field is added, if possible.
        - Specification names are made fully-qualified with the
          format ``package.metric.spec_name`` if possible (as `str`).
        - Partial IDs are fully-qualified with the format
          ``package:relative_yaml_path_without_extension#id``, for example
          ``validate_drp:custom/gri#base``.
        - The ``base`` field is processed so that each partial or specification
          name is fully-qualified.
        """
        # Ensure paths are absolute so we can make relative paths and
        # determine the package name from the last directory component of
        # the package_dirname.
        package_dirname = os.path.abspath(package_dirname)
        yaml_file_path = os.path.abspath(yaml_file_path)

        if not os.path.isdir(package_dirname):
            message = 'Specification package directory {0!r} not found.'
            raise OSError(message.format(package_dirname))
        if not os.path.isfile(yaml_file_path):
            message = 'Specification YAML file {0!r} not found.'
            raise OSError(message.format(yaml_file_path))

        # Name of the stack package these specifcation belong to, based
        # on our metrics/specification repo directory structure.
        package_name = package_dirname.split(os.path.sep)[-1]

        # path identifier used in names for partials does not have an
        # extension, and must have '/' directory separators.
        yaml_id = os.path.relpath(yaml_file_path,
                                  start=package_dirname)
        yaml_id = os.path.splitext(yaml_id)[0]
        yaml_id = '/'.join(yaml_id.split(os.path.sep))

        spec_docs = []
        partial_docs = []
        with open(yaml_file_path) as stream:
            parsed_docs = load_all_ordered_yaml(stream)

            for doc in parsed_docs:
                doc['package'] = package_name

                if 'id' in doc:
                    # Must be a partial
                    doc = SpecificationSet._process_partial_yaml_doc(
                        doc, yaml_id)
                    partial_docs.append(doc)

                else:
                    # Must be a specification
                    doc = SpecificationSet._process_specification_yaml_doc(
                        doc, yaml_id)
                    spec_docs.append(doc)

        return spec_docs, partial_docs

    @staticmethod
    def _process_specification_yaml_doc(doc, yaml_id):
        """Process a specification yaml document.

        Principle functionality is:

        1. Make ``name`` fully qualified (if possible).
        2. Add ``metric`` field (if possible).
        3. Add ``package`` field (if possible).
        """
        # Ensure name is fully specified
        metric = doc.get('metric', None)
        package = doc.get('package', None)

        try:
            doc['name'] = SpecificationSet._normalize_spec_name(
                doc['name'], metric=metric, package=package)

            _name = Name(doc['name'])
            doc['metric'] = _name.metric
            doc['package'] - _name.package
        except TypeError:
            # Can't resolve the fully-qualified specification
            # name until inheritance is resolved. No big deal.
            pass

        # Make all bases fully-specified
        if 'base' in doc:
            processed_bases = SpecificationSet._process_bases(
                doc['base'], doc['package'], yaml_id)
            doc['base'] = processed_bases

        return doc

    @staticmethod
    def _process_partial_yaml_doc(doc, yaml_id):
        """Process a specification yaml document.

        Principle functionality is:

        1. Make `id` fully specified.
        2. Make bases fully specified.
        """
        package = doc['package']

        # Ensure the id is fully specified
        doc['id'] = SpecificationSet._normalize_partial_name(
            doc['id'],
            current_yaml_id=yaml_id,
            package=package)

        # Make all bases fully-specified
        if 'base' in doc:
            processed_bases = SpecificationSet._process_bases(
                doc['base'], doc['package'], yaml_id)
            doc['base'] = processed_bases

        return doc

    @staticmethod
    def _process_bases(bases, package_name, yaml_id):
        if not isinstance(bases, list):
            bases = [bases]

        processed_bases = []
        for base_name in bases:
            if '#' in base_name:
                # Base name points is a partial
                base_name = SpecificationSet._normalize_partial_name(
                    base_name,
                    current_yaml_id=yaml_id,
                    package=package_name)
            else:
                # Base name points to a specification
                base_name = SpecificationSet._normalize_spec_name(
                    base_name,
                    package=package_name)

            processed_bases.append(base_name)

        return processed_bases

    @staticmethod
    def _normalize_partial_name(name, current_yaml_id=None, package=None):
        """Normalize a partial's identifier.

        >>> SpecificationSet._normalize_partial_name(
                '#base',
                current_yaml_id='custom/bases',
                package='validate_drp')
        'validate.drp:custom/bases#base'
        """
        if '#' not in name:
            # Name is probably coming from a partial's own `id` field
            # which just has the post-# part of a specification's fully
            # qualified name.
            name = '#' + name

        matches = PARTIAL_PATTERN.search(name)

        # Use info from user arguments if not given directly.
        # Thus a user can't override info already in the name
        _package = matches.group('package')
        if _package is None:
            _package = package
        _path = matches.group('path')
        if _path is None:
            _path = current_yaml_id
        partial_name = matches.group('name')

        # Create the fully-specified name
        fmt = '{package}:{path}#{name}'
        return fmt.format(package=_package,
                          path=_path,
                          name=partial_name)

    @staticmethod
    def _normalize_spec_name(name, metric=None, package=None):
        """Normalize a specification name to a fully-qualified specification
        name.

        >>> SpecificationSet._normalize_spec_name('PA1.design',
                                                  package='validate_drp')
        'validate_drp.PA1.design'
        """
        name = Name(package=package, metric=metric, spec=name)
        return name.fqn

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

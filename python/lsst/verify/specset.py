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

__all__ = ['SpecificationSet']

from past.builtins import basestring

from collections import OrderedDict
import os
import re

import lsst.pex.exceptions
from lsst.utils import getPackageDir

from .errors import SpecificationResolutionError
from .jsonmixin import JsonSerializationMixin
from .naming import Name
from .spec.base import Specification
from .spec.threshold import ThresholdSpecification
from .yamlutils import merge_documents, load_all_ordered_yaml


# Pattern for SpecificationPartial names
# package:path#name
PARTIAL_PATTERN = re.compile('^(?:(?P<package>\S+):)'
                             '?(?P<path>\S+)?#(?P<name>\S+)$')


class SpecificationSet(JsonSerializationMixin):
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

    @classmethod
    def deserialize(cls, specifications=None):
        """Deserialize a specification set from a JSON serialization.

        Parameters
        ----------
        specifications : `list`, optional
            List of specification JSON objects.

        Returns
        -------
        spec_set : `SpecificationSet`
            SpecificationSet instance.
        """
        instance = cls()

        if specifications is not None:
            for spec_doc in specifications:
                # FIXME DM-8477 Need a registry to support multiple types
                # check type
                if 'threshold' in spec_doc:
                    spec = ThresholdSpecification.deserialize(**spec_doc)
                else:
                    message = ("We only support threshold-type "
                               "specifications\n"
                               "{0!r}".format(spec_doc))
                    raise NotImplementedError(message)
                instance.insert(spec)

        return instance

    @classmethod
    def load_metrics_package(cls, package_name_or_path='verify_metrics',
                             subset=None):
        """Create a SpecificationSet from an Verification Framework metrics
        package.

        Parameters
        ----------
        package_name_or_path : `str`, optional
            Name of an EUPS package that hosts metric and specification
            definition YAML files **or** the file path to a metrics package.
            ``verify_metrics`` is the default package, and is where metrics
            and specifications are defined for most packages.
        subset : `str`, optional
            If set, only specifications defined for this package are loaded.
            For example, if ``subset='validate_drp'``, only ``validate_drp``
            specifications are included in the SpecificationSet. This argument
            is equivalent to the `SpecificationSet.subset` method. Default
            is `None`.

        Returns
        -------
        spec_set : `SpecificationSet`
            A `SpecificationSet` containing `Specification` instances.

        See also
        --------
        `SpecificationSet.load_single_package`

        Notes
        -----
        EUPS packages that host metrics and specification definitions for the
        Verification Framework have top-level directories named ``'metrics'``
        and ``'specs'``.

        Within ``'specs/'``, directories are named after *packages* that
        have defined metrics. Contained within these directories are YAML files
        defining specifications for those metrics.

        To make a `SpecificationSet` from a single package's specifications,
        use `load_single_package` instead.
        To make a `SpecificationSet` from a single package's YAML definition
        directory that **is not** contained in a metrics package, use
        `load_single_package` instead.
        """
        try:
            # Try an EUPS package name
            package_dir = getPackageDir(package_name_or_path)
        except lsst.pex.exceptions.NotFoundError:
            # Try as a filesystem path instead
            package_dir = package_name_or_path
        finally:
            package_dir = os.path.abspath(package_dir)

        specs_dirname = os.path.join(package_dir, 'specs')
        if not os.path.isdir(specs_dirname):
            message = 'Specifications directory {0} not found'
            raise OSError(message.format(specs_dirname))

        instance = cls()

        if subset is not None:
            # Load specifications only for the package given by `subset`
            package_names = [subset]
        else:
            # Load specifications for each 'package' within specs/
            package_names = os.listdir(specs_dirname)

        for name in package_names:
            package_specs_dirname = os.path.join(specs_dirname, name)
            if not os.path.isdir(package_specs_dirname):
                continue
            instance._load_package_dir(package_specs_dirname)

        return instance

    @classmethod
    def load_single_package(cls, package_specs_dirname):
        """Create a SpecificationSet from a filesystem directory containing
        specification YAML files for a single package.

        Parameters
        ----------
        package_specs_dirname : `str`
            Directory containing specification definition YAML files for
            metrics of a single package. The name of this directory (final
            path component) is taken as the name of the package.

        Returns
        -------
        spec_set : `SpecificationSet`
            A `SpecificationSet` containing `Specification` instances.

        See also
        --------
        SpecificationSet.load_metrics_package

        Notes
        -----
        This SpecificationSet constructor is useful for loading specifications
        from a directory containing specification definitions for a single
        package. The directory name is interpreted as a package name
        for fully-qualified metric and specification names.

        To load a Verification Framework metrics package, like
        ``verify_metrics``, with specifications for multple packages,
        use `load_metrics_packge` instead.
        """
        instance = cls()
        instance._load_package_dir(package_specs_dirname)

        return instance

    def _load_package_dir(self, package_specs_dirname):
        yaml_extensions = ('.yaml', '.yml')
        package_specs_dirname = os.path.abspath(package_specs_dirname)

        all_docs = []

        for (root_dir, _, filenames) in os.walk(package_specs_dirname):
            for filename in filenames:
                if os.path.splitext(filename)[-1] not in yaml_extensions:
                    continue
                filename = os.path.join(root_dir, filename)
                spec_docs, partial_docs = SpecificationSet._load_yaml_file(
                    filename,
                    package_specs_dirname)
                all_docs.extend(partial_docs)
                all_docs.extend(spec_docs)

        # resolve inheritance and Specification* instances when possible
        while len(all_docs) > 0:
            redo_queue = []

            for doc in all_docs:
                try:
                    doc = self.resolve_document(doc)
                except SpecificationResolutionError:
                    # try again later
                    redo_queue.append(doc)
                    continue

                if 'id' in doc:
                    partial = SpecificationPartial(doc)
                    self._partials[partial.name] = partial
                else:
                    # Make sure the name is fully qualified
                    # since _process_specification_yaml_doc may not have
                    # finished this yet
                    doc['name'] = SpecificationSet._normalize_spec_name(
                        doc['name'], metric=doc.get('metric', None),
                        package=doc.get('package', None))

                    # FIXME DM-8477 Need a registry to support multiple types
                    if 'threshold' not in doc:
                        message = ("We only support threshold-type "
                                   "specifications\n"
                                   "{0!r}".format(doc))
                        raise NotImplementedError(message)
                    spec = ThresholdSpecification.deserialize(**doc)

                    name = spec.name

                    if not name.is_fq:
                        message = (
                            'Fully-qualified name not resolved for'
                            '{0!s}'.format(spec))
                        raise SpecificationResolutionError(message)

                    self._specs[name] = spec

            if len(redo_queue) == len(all_docs):
                message = ("There are unresolved specification "
                           "documents: {0!r}")
                raise SpecificationResolutionError(message.format(redo_queue))

            all_docs = redo_queue

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
        # on our metrics/specification package directory structure.
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
        ...     '#base',
        ...     current_yaml_id='custom/bases',
        ...     package='validate_drp')
        'validate_drp:custom/bases#base'
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
        ...                                       package='validate_drp')
        'validate_drp.PA1.design'
        """
        name = Name(package=package, metric=metric, spec=name)
        return name.fqn

    @property
    def json(self):
        doc = JsonSerializationMixin._jsonify_list(
            [spec for name, spec in self.items()]
        )
        return doc

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

    def __setitem__(self, key, value):
        if isinstance(key, basestring) and '#' in key:
            # must be a partial's name
            if not isinstance(value, SpecificationPartial):
                message = ('Expected {0!s}={1!r} to be a '
                           'SpecificationPartial-type')
                raise TypeError(message.format(key, value))

            # Ensure key and value.name are consistent
            if key != value.name:
                message = ("Key {0!s} does not match the "
                           "SpecificationPartial's name {1!s})")
                raise KeyError(message.format(key, value.name))
            self._partials[key] = value

        else:
            # must be a specification.
            if not isinstance(key, Name):
                key = Name(spec=key)

            if not key.is_spec:
                message = 'Expected key {0!r} to resolve a specification'
                raise KeyError(message.format(key))

            if not isinstance(value, Specification):
                message = ('Expected {0!s}={1!r} to be a '
                           'Specification-type')
                raise TypeError(message.format(key, value))

            # Ensure key and value.name are consistent
            if key != value.name:
                message = ("Key {0!s} does not match the "
                           "Specification's name {1!s})")
                raise KeyError(message.format(key, value.name))

            self._specs[key] = value

    def __delitem__(self, key):
        if isinstance(key, basestring) and '#' in key:
            # must be a partial's name
            del self._partials[key]

        else:
            # must be a specification
            if not isinstance(key, Name):
                key = Name(spec=key)

            del self._specs[key]

    def __iter__(self):
        for key in self._specs:
            yield key

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for name, spec in self.items():
            try:
                if spec != other[name]:
                    return False
            except KeyError:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iadd__(self, other):
        """Merge another `SpecificationSet` into this one.

        Parameters
        ---------
        other : `SpecificationSet`
            Another `SpecificationSet`. Specification in ``other`` that do
            exist in this set are added to this one. Specification in ``other``
            replace specifications of the same name in this one.

        Returns
        -------
        self : `SpecificationSet`
            This `SpecificationSet`.

        Notes
        -----
        Equivalent to `update`.
        """
        self.update(other)
        return self

    def keys(self):
        """Get a sequence of specification names, which are keys to the set.

        Returns
        -------
        keys : sequence of `Name`
            Keys to the specification set.
        """
        return self._specs.keys()

    def items(self):
        """Iterate over name, specification pairs.

        Yields
        ------
        item : `tuple`
            Tuple containing:

            - `Name` of the specification.
            - `Specification`-type object.
        """
        for name, spec in self._specs.items():
            yield name, spec

    def insert(self, spec):
        """Insert a Specification into the set.

        A pre-existing specification with the same name is replaced.

        Parameters
        ----------
        spec : `Specification`-type
            A specification.
        """
        key = spec.name
        self[key] = spec

    def update(self, other):
        """Merge another `SpecificationSet` into this one.

        Parameters
        ---------
        other : `SpecificationSet`
            Another `SpecificationSet`. Specification in ``other`` that do
            exist in this set are added to this one. Specification in ``other``
            replace specifications of the same name in this one.
        """
        for _, spec in other.items():
            self.insert(spec)

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

    def subset(self, name=None, meta=None):
        """Create a new `SpecificationSet` with specifications belonging to
        a single package or metric, and that apply to the given metadata.

        Parameters
        ----------
        name : `str` or `lsst.verify.Name`, optional
            Name to subset specifications by. If this is the name of a package,
            then all specifications for that package are included in the
            subset. If this is a metric name, then only specifications
            for that metric are included in the subset. The metric name
            must be fully-qualified (that is, it includes a package component).
        meta : `lsst.verify.Metadata`, optional
            If supplied, only specifications that apply to the given metadata
            are included in the subset. Metadata is usually obtained from
            the `Job.meta` attribute of a `Job` instance.

        Returns
        -------
        spec_subset : `SpecificationSet`
            Subset of this `SpecificationSet` containing only specifications
            belonging to the indicated package or metric, and/or that are
            compatible with the job metadata.. Any partials in
            the SpecificationSet are also included in ``spec_subset``.
        """
        all_partials = [partial
                        for partial_name, partial in self._partials.items()]

        # Filter by package or metric name
        if name is not None:
            if not isinstance(name, Name):
                name = Name(name)

            if not name.is_fq:
                message = '{0!s} is not a fully-qualified name'.format(name)
                raise RuntimeError(message)

            specs = [spec for spec_name, spec in self._specs.items()
                     if spec_name in name]

            spec_subset = SpecificationSet(specifications=specs,
                                           partials=all_partials)
        else:
            spec_subset = self

        # Filter by metadata
        if meta is not None:
            specs = [spec for spec_name, spec in spec_subset.items()
                     if spec.query_metadata(meta)]

            spec_subset = SpecificationSet(specifications=specs,
                                           partials=all_partials)

        return spec_subset


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

# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Utilities for working with YAML documents."""

from collections import OrderedDict
from copy import deepcopy
import yaml

__all__ = ['load_ordered_yaml', 'load_all_ordered_yaml']


def load_ordered_yaml(stream, **kwargs):
    """Load a YAML document from a stream as an `~collections.OrderedDict`.

    Parameters
    ----------
    stream :
        A stream for a YAML file (made with `open` or `~io.StringIO`, for
        example).
    loader : optional
        A YAML loader class. Default is ``yaml.Loader``.
    object_pairs_hook : obj, optional
        Class that YAML key-value pairs are loaded into by the ``loader``.
        Default is `collections.OrderedDict`.

    Returns
    -------
    yaml_doc : `~collections.OrderedDict`
        The YAML document as an `~collections.OrderedDict` (or the type
        specified in ``object_pairs_hook``).
    """
    OrderedLoader = _build_ordered_loader(**kwargs)
    return yaml.load(stream, OrderedLoader)


def load_all_ordered_yaml(stream, **kwargs):
    r"""Load all YAML documents from a stream as a `list` of
    `~collections.OrderedDict`\ s.

    Parameters
    ----------
    stream :
        A stream for a YAML file (made with `open` or `~io.StringIO`, for
        example).
    loader : optional
        A YAML loader class. Default is ``yaml.Loader``.
    object_pairs_hook : obj, optional
        Class that YAML key-value pairs are loaded into by the ``loader``.
        Default is `collections.OrderedDict`.

    Returns
    -------
    yaml_docs : `list` of `~collections.OrderedDict`
        The YAML documents as a `list` of `~collections.OrderedDict`\ s (or
        the type specified in ``object_pairs_hook``).
    """
    OrderedLoader = _build_ordered_loader(**kwargs)
    return yaml.load_all(stream, OrderedLoader)


def _build_ordered_loader(Loader=yaml.CSafeLoader,
                          object_pairs_hook=OrderedDict):
    # Solution from http://stackoverflow.com/a/21912744

    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return OrderedLoader


def merge_documents(base_doc, new_doc):
    r"""Merge the content of a dict-like object onto a base dict-like object,
    recursively following embedded dictionaries and lists.

    Parameters
    ----------
    base_doc : `dict`-like
        The base document.
    new_doc : `dict`-like
        The new document. Content from the new document are added to the
        base document. Matching keys from the new document will override
        the base document and new keys in the document are added to the
        base document.

    Returns
    -------
    merged_doc : `~collections.OrderedDict`
        The merged document. The contents of ``merged_doc`` are copies
        of originals in ``base_doc`` and ``new_doc``.

    Notes
    -----
    This function implements a key-value document merging algorithm
    design for specification YAML documents. The rules are:

    - Key-values from ``base_doc`` not present in ``new_doc`` are carried into
      ``merged_doc``.

    - Key-values from ``new_doc`` not present in ``base_doc`` are carried into
      ``merged_doc``.

    - If both ``new_doc`` and ``base_doc`` share a key and the value from
      **either** is a scalar (not a `dict` or `list`-type), the value from
      ``new_doc`` is carried into ``merged_doc``.

    - If both ``new_doc`` and ``base_doc`` share a key and the value from
      **both** is a sequence (`list`-type) then the list items from the
      ``new_doc`` are **appended** to the ``base_doc``\ 's list.

    - If both ``new_doc`` and ``base_doc`` share a key and the value from
      **both** is a mapping (`dict`-type) then the two values are
      merged by recursively calling this ``merge_documents`` function.
    """
    # Create a copy so that the base doc is not mutated
    merged_doc = deepcopy(base_doc)

    for new_key, new_value in new_doc.items():
        if new_key in merged_doc:
            # Deal with merge by created the 'merged_value' from base and new
            base_value = merged_doc[new_key]

            if isinstance(base_value, dict) and isinstance(new_value, dict):
                # Recursively merge these two dictionaries
                merged_value = merge_documents(base_value, new_value)

            elif isinstance(base_value, list) and isinstance(new_value, list):
                # Both are lists: merge by appending the new items to the end
                # of the base items.
                # Copy the base's list so we're not modify the input
                merged_value = deepcopy(base_value)
                merged_value.extend(deepcopy(new_value))  # modifies in-place

            else:
                # A scalar: just over-write the existing base value
                merged_value = deepcopy(new_value)

            # Done merging this key-value pair
            merged_doc[new_key] = merged_value

        else:
            # Add the new key that isn't over-writing merged_doc
            merged_doc[new_key] = deepcopy(new_value)

    return merged_doc

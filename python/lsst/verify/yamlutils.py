# See COPYRIGHT file at the top of the source tree.
"""Utilities for working with YAML documents."""

from __future__ import print_function, division

from collections import OrderedDict
import yaml

__all__ = ['load_ordered_yaml']


def load_ordered_yaml(stream, Loader=yaml.Loader,
                      object_pairs_hook=OrderedDict):
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

    Notes
    -----
    Solution from http://stackoverflow.com/a/21912744
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)

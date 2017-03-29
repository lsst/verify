# See COPYRIGHT file at the top of the source tree.
"""Utilities for working with YAML documents."""

from __future__ import print_function, division

from collections import OrderedDict
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
    """Load all YAML documents from a stream as a `list` of
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


def _build_ordered_loader(Loader=yaml.Loader, object_pairs_hook=OrderedDict):
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

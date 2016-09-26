# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import abc
import json


__all__ = ['JsonSerializationMixin']


class JsonSerializationMixin(object):
    """Mixin that provides JSON serialization support to subclasses."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def json(self):
        """a `dict` that can be serialized as semantic SQuaSH json."""
        pass

    @staticmethod
    def jsonify_dict(d):
        """Recursively render JSON on all values in a dict."""
        json_dict = {}
        for k, v in d.iteritems():
            json_dict[k] = JsonSerializationMixin._jsonify_value(v)
        return json_dict

    @staticmethod
    def jsonify_list(lst):
        json_array = []
        for v in lst:
            json_array.append(JsonSerializationMixin._jsonify_value(v))
        return json_array

    @staticmethod
    def _jsonify_value(v):
        if isinstance(v, JsonSerializationMixin):
            return v.json
        elif isinstance(v, dict):
            return JsonSerializationMixin.jsonify_dict(v)
        elif isinstance(v, (list, tuple)):
            return JsonSerializationMixin.jsonify_list(v)
        else:
            return v

    def write_json(self, filepath):
        """Write JSON to `filepath` on disk."""
        with open(filepath, 'w') as outfile:
            json.dump(self.json, outfile, sort_keys=True, indent=2)

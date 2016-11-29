# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import abc
import json


__all__ = ['JsonSerializationMixin']


class JsonSerializationMixin(object):
    """Mixin that provides JSON serialization support to subclasses.

    Subclasses must implement the `json` method. The method returns a `dict`
    that can be serialized to JSON. Use the `jsonify_dict` method to handle
    the conversion of iterables, numbers, strings, booleans and
    `JsonSerializationMixin`-compatible objects into a JSON-serialiable object.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def json(self):
        """`dict` that can be serialized as semantic JSON, compatible with
        the SQUASH metric service.
        """
        pass

    @staticmethod
    def jsonify_dict(d):
        """Recursively build JSON-renderable objects on all values in a dict.

        Parameters
        ----------
        d : `dict`
            Dictionary ito convert into a JSON-serializable object. Values
            are recursively JSON-ified.

        Returns
        -------
        json_dict : `dict`
            Dictionary that can be serialized to JSON.

        Examples
        --------
        Subclasses can use this method to prepare output in their `json`-method
        implementation. For example::

          def json(self):
              return JsonSerializationMixin.jsonify_dict({
              'value': self.value,
              })
        """
        json_dict = {}
        for k, v in d.iteritems():
            json_dict[k] = JsonSerializationMixin._jsonify_value(v)
        return json_dict

    @staticmethod
    def _jsonify_list(lst):
        """Recursively convert items of a list into JSON-serializable objects.
        """
        json_array = []
        for v in lst:
            json_array.append(JsonSerializationMixin._jsonify_value(v))
        return json_array

    @staticmethod
    def _jsonify_value(v):
        """Convert an object into a JSON-serizable object, recursively
        processes dicts and iterables.
        """
        if isinstance(v, JsonSerializationMixin):
            return v.json
        elif isinstance(v, dict):
            return JsonSerializationMixin.jsonify_dict(v)
        elif isinstance(v, (list, tuple)):
            return JsonSerializationMixin._jsonify_list(v)
        else:
            return v

    def write_json(self, filepath):
        """Write JSON to a file.

        Parameters
        ----------
        filepath : `str`
            Destination file name for JSON output.
        """
        with open(filepath, 'w') as outfile:
            json.dump(self.json, outfile, sort_keys=True, indent=2)

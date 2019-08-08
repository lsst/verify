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

__all__ = ['JsonSerializationMixin']

from builtins import object
from future.utils import with_metaclass

import abc
import json


class JsonSerializationMixin(with_metaclass(abc.ABCMeta, object)):
    """Mixin that provides JSON serialization support to subclasses.

    Subclasses must implement the `json` method. The method returns a `dict`
    that can be serialized to JSON. Use the `jsonify_dict` method to handle
    the conversion of iterables, numbers, strings, booleans and
    `JsonSerializationMixin`-compatible objects into a JSON-serialiable object.
    """

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
            Dictionary to convert into a JSON-serializable object. Values
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
        for k, v in d.items():
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
        elif isinstance(v, (list, tuple, set)):
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

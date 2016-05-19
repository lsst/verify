# LSST Data Management System
# Copyright 2008-2016 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
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

from __future__ import print_function, division, absolute_import

import json
import numpy as np
import astropy.units
import lsst.pipe.base as pipeBase


class DatumSerializer(object):
    """Serializer for an annotated data point.

    Use the `DatumSerializer.json` property to convert a datum to a JSON-ready
    data structure.

    Parameters
    ----------
    value : `str`, `int`, `float` or 1-D iterable.
        Value of the datum.
    units : `str`
        Astropy-compatible units string. See
        http://docs.astropy.org/en/stable/units/
    label : `str`, optional
        Label suitable for plot axes (without units).
    description : `str`, optional
        Extended description.
    """

    def __init__(self, value, units, label=None, description=None):
        self._doc = {}
        self.value = value
        self.units = units
        self.label = label
        self.description = description

    @property
    def json(self):
        """Datum as a `dict` compatible with overall Job JSON schema."""
        # Copy the dict so that the serializer is immutable
        d = {
            'value': self.value,
            'units': self.units,
            'label': self.label,
            'description': self.description
        }
        return d

    @property
    def value(self):
        """Value of the datum (`str`, `int`, `float` or 1-D iterable.)."""
        return self._doc['value']

    @value.setter
    def value(self, v):
        self._doc['value'] = v

    @property
    def units(self):
        """Astropy-compatible unit string."""
        return self._doc['units']

    @units.setter
    def units(self, value):
        # verify that Astropy can parse the unit string
        if value is not None and value != 'millimag':
            print(value)
            astropy.units.Unit(value, parse_strict='raise')
        self._doc['units'] = value

    @property
    def label(self):
        """Label for plotting (without units)."""
        return self._doc['label']

    @label.setter
    def label(self, value):
        assert isinstance(value, basestring) or None
        self._doc['label'] = value

    @property
    def description(self):
        """Extended description of Datum."""
        return self._doc['description']

    @description.setter
    def description(self, value):
        assert isinstance(value, basestring) or None
        self._doc['description'] = value


def saveKpmToJson(KpmStruct, filename):
    """Save KPM `lsst.pipe.base.Struct` to JSON file.

    Parameters
    ----------
    KpmStruct : lsst.pipe.base.Struct
        Information to serialize in JSON.
    filename : str
        Output filename.

    Examples
    --------
    >>> import lsst.pipe.base as pipeBase
    >>> foo = pipeBase.Struct(a=2)
    >>> outfile = 'tmp.json'
    >>> saveKpmToJson(foo, outfile)

    Notes
    -----
    Rewrites `numpy.ndarray` as a list`
    """
    data = KpmStruct.getDict()

    # Simple check to convert numpy.ndarray to list
    for k, v in data.iteritems():
        if isinstance(v, np.ndarray):
            data[k] = v.tolist()

    with open(filename, 'w') as outfile:
        # Structure the output with sort_keys, and indent
        # to make comparisons of output results easy on a line-by-line basis.
        json.dump(data, outfile, sort_keys=True, indent=4)


def loadKpmFromJson(filename):
    """Load KPM `lsst.pipe.base.Struct` from JSON file.

    Parameters
    ----------
    filename : str
        Input filename.

    Returns
    -------
    KpmStruct : lsst.pipe.base.Struct
        Reconstructed information from file reconstructed

    Examples
    --------
    >>> import lsst.pipe.base as pipeBase
    >>> foo = pipeBase.Struct(a=2)
    >>> outfile = 'tmp.json'
    >>> saveKpmToJson(foo, outfile)
    >>> bar = loadKpmFromJson(outfile)
    >>> print(bar.a)
    2

    Notes
    -----
    Rewrites `numpy.ndarray` as a list`
    """

    with open(filename, 'r') as infile:
        data = json.load(infile)

    return pipeBase.Struct(**data)

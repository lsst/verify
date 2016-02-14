#!/usr/bin/env python

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

def saveKpmToJson(KpmStruct, filename):
    """Save Kpm `lsst.pipe.base.Struct` to JSON file.

    Inputs
    ------
    KpmStruct : lsst.pipe.base.Struct
        Information to serialize in JSON.
    filename : str
        Output filename.

    Examples
    --------
    >>> foo = {'a': b}
    >>> outfile = 'tmp.json'
    >>> saveKpmToJson(bar, outfile)

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

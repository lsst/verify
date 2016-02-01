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

from __future__ import print_function, division

import lsst.pipe.base as pipeBase

from .base import ValidateError

srdSpec = pipeBase.Struct(
    levels = ("design", "minimum", "stretch"),
    PA2 = {"design" : 15, "minimum" : 15, "stretch" : 10},  # mmag
    D1 = 5,  # arcmin
    AM1 = {"design" : 10, "minimum" : 20, "stretch" : 5},  # mas
    AF1 = {"design" : 10, "minimum" : 20, "stretch" : 5},  # %
    AD1 = {"design" : 20, "minimum" : 40, "stretch" : 10},  # mas
    D2 = 20,
    AM2 = {"design" : 10, "minimum" : 20, "stretch" : 5},  # mas
    AF2 = {"design" : 10, "minimum" : 20, "stretch" : 5},  # %
    AD2 = {"design" : 20, "minimum" : 40, "stretch" : 10},  # mas
    D3 = 200,
    AM3 = {"design" : 15, "minimum" : 30, "stretch" : 10},  # mas
    AF3 = {"design" : 10, "minimum" : 20, "stretch" : 5},  # %
    AD3 = {"design" : 30, "minimum" : 50, "stretch" : 20},  # mas
)


def getAstrometricSpec(x=None, level='design'):
    """Return SRD specification for given astrometric test.

    @param[in] x  -- One of [1,2,3].
    @param[in] level -- ["design", "minimum", "stretch"]


    Returns:
    --------
       AMx, AFx, ADx  -- tuple of SRD relevant specifications

    Raises:
    -------
    ValidateError if `x` isn't in `getAstrometricSpec`
    """

    if x == 1:
        AMx = srdSpec.AM1[level]
        AFx = srdSpec.AF1[level]
        ADx = srdSpec.AD1[level]
    elif x == 2:
        AMx = srdSpec.AM2[level]
        AFx = srdSpec.AF2[level]
        ADx = srdSpec.AD2[level]
    elif x == 3:
        AMx = srdSpec.AM3[level]
        AFx = srdSpec.AF3[level]
        ADx = srdSpec.AD3[level]
    else:
        raise ValidateError("Unknown astrometric test specification: %s" % str(x))

    return AMx, AFx, ADx

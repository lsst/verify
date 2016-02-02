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

import numpy as np

class ValidateError(Exception):
    """Base classes for exceptions in validate_drp."""
    pass

def averageRaDec(cat):
    """Calculate the RMS for RA, Dec for a set of observations an object.

    This is WRONG!
    Doesn't do wrap-around
    """
    ra = np.mean(cat.get('coord_ra'))
    dec = np.mean(cat.get('coord_dec'))
    return ra, dec

# Some thoughts from Paul Price on how to do the coordinate differences correctly:
#    mean = sum([afwGeom.Extent3D(coord.toVector())
#                for coord in coordList, afwGeom.Point3D(0, 0, 0)])
#    mean /= len(coordList)
#    mean = afwCoord.IcrsCoord(mean)

# Paul Price suggests the following to calculate average
#  import lsst.afw.coord
#    average = lsst.afw.coord.averageCoord(coords)
### And then to calculate RMS:
#    offsets = [cc.getTangentPlaneOffset(average) for cc in coords]
#    rms = numpy.array([xx[0].asArcseconds() for xx in offsets]).std(), numpy.array([xx[1].asArcseconds() for xx in offsets]).std()
#
#     average = safeMatches.aggregate(getAverageCoord)
#
# def getAverageCoord(cat):
#     ra = cat.get('coord_ra')
#     dec = cat.get('coord_dec')
#     coords = lsst.afw.coord.makeCoord(ra, dec)
#     lsst.afw.coord.averageCoord(coords)


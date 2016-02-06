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

import lsst.afw.geom as afwGeom
import lsst.afw.coord as afwCoord


def averageRaDec(ra, dec):
    """Calculate average RA, Dec from input lists using spherical geometry.

    Inputs
    ------
    ra : list of float
        RA in [radians]
    dec : list of float
        Dec in [radians]

    Returns
    -------
    float, float
       meanRa, meanDec -- Tuple of average RA, Dec [radians]
    """
    assert(len(ra) == len(dec))

    angleRa = [afwGeom.Angle(r, afwGeom.radians) for r in ra]
    angleDec = [afwGeom.Angle(d, afwGeom.radians) for d in dec]
    coords = [afwCoord.IcrsCoord(ar, ad) for (ar, ad) in zip(angleRa, angleDec)]

    meanRa, meanDec = afwCoord.averageCoord(coords)

    return meanRa.asRadians(), meanDec.asRadians()


def averageRaDecFromCat(cat):
    return averageRaDec(cat.get('coord_ra'), cat.get('coord_dec'))

def averageRaFromCat(cat):
    meanRa, meanDec = averageRaDecFromCat(cat)
    return meanRa

def averageDecFromCat(cat):
    meanRa, meanDec = averageRaDecFromCat(cat)
    return meanDec

# Paul Price suggests the following to calculate average
#  import lsst.afw.coord
#    average = lsst.afw.coord.averageCoord(coords)
### And then to calculate RMS:
#    offsets = [cc.getTangentPlaneOffset(average) for cc in coords]
#    rms = numpy.array([xx[0].asArcseconds() for xx in offsets]).std(), numpy.array([xx[1].asArcseconds() for xx in offsets]).std()

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

import os

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


def getCcdKeyName(dataid):
    """Return the key in a dataId that's referring to the CCD or moral equivalent.

    Inputs
    ------
    dataid : dict
        A dictionary that will be searched for a key that matches
        an entry in the hardcoded list of possible names for the CCD field.

    Notes
    -----
    Motiviation: Different camera mappings use different keys to indicate
      the different amps/ccds in the same exposure.  This function looks
      through the reference dataId to locate a field that could be the one.
    """
    possibleCcdFieldNames = ['ccd', 'ccdnum', 'camcol']

    for name in possibleCcdFieldNames:
        if name in dataid:
            return name
    else:
        return None


def repoNameToPrefix(repo):
    """Generate a base prefix for plots based on the repo name.

    Examples
    --------
    >>> repoNameToPrefix('a/b/c')
    'a_b_c_'
    >>> repoNameToPrefix('/bar/foo/')
    'bar_foo_'
    >>> repoNameToPrefix('CFHT/output')
    'CFHT_output_'
    >>> repoNameToPrefix('./CFHT/output')
    'CFHT_output_'
    >>> repoNameToPrefix('.a/CFHT/output')
    'a_CFHT_output_'
    """

    return repo.lstrip('\.').strip(os.sep).replace(os.sep, "_")+"_"

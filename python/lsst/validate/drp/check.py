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

from .util import averageRaDecFromCat


def isExtended(source, extendedKey, extendedThreshold=1.0):
    """Is the source extended attribute above the threshold.

    Inputs
    ------
    cat : collection with a .get method
        for `extendedKey`
    extendedKey
        key to look up the extended object parameter from a schema.

    Higher values of extendedness indicate a resolved object
    that is larger than a point source.
    """
    return source.get(extendedKey) >= extendedThreshold


def magNormDiff(cat):
    """Calculate the normalized mag/mag_err difference from the mean for a
    set of observations of an objection.

    Inputs
    ------
    cat : collection with a .get method
         for flux, flux+"-"

    Returns
    -------
    pos_median : float
        median diff of positions in milliarcsec.
    """
    mag = cat.get('base_PsfFlux_mag')
    magerr = cat.get('base_PsfFlux_magerr')
    mag_avg = np.mean(mag)
    normDiff = (mag - mag_avg) / magerr

    return normDiff


def positionRms(cat):
    """Calculate the RMS for RA, Dec for a set of observations an object.

    Inputs
    ------
    cat -- collection with a .get method
         for 'coord_ra', 'coord_dec' that returns radians.

    Returns
    -------
    pos_rms -- RMS of positions in milliarcsecond.  Float.

    This routine doesn't handle wrap-around
    """
    ra_avg, dec_avg = averageRaDecFromCat(cat)
    ra, dec = cat.get('coord_ra'), cat.get('coord_dec')
    # Approximating that the cos(dec) term is roughly the same
    #   for all observations of this object.
    ra_var = np.var(ra) * np.cos(dec_avg)**2
    dec_var = np.var(dec)
    pos_rms = np.sqrt(ra_var + dec_var)  # radians
    pos_rms = afwGeom.radToMas(pos_rms)  # milliarcsec

    return pos_rms


def checkAstrometry(mag, mmagrms, dist, match,
                    good_mag_limit=19.5,
                    medianRef=100, matchRef=500):
    """Print out the astrometric scatter for all stars, and for good stars.

    Inputs
    ------
    mag : list or numpy.array
        Average magnitudes of each star
    mmagrms ; list or numpy.array
        Magnitude RMS of the multiple observation of each star.
    dist : list or numpy.array
        Distances between successive measurements of one star
    match : int
        Number of stars matched.

    good_mag_limit : float, optional
        Minimum average brightness (in magnitudes) for a star to be considered.
    medianRef : float, optional
        Median reference astrometric scatter in milliarcseconds.
    matchRef : int, optional
        Should match at least matchRef stars.

    Returns
    -------
    float
        The astrometric scatter (RMS, milliarcsec) for all good stars.

    Notes
    -----
    The scatter and match defaults are appropriate to SDSS are the defaults
      for `medianRef` and `matchRef`
    For SDSS, stars with mag < 19.5 should be completely well measured.
    """

    print("Median value of the astrometric scatter - all magnitudes: %.3f %s" %
          (np.median(dist), "mas"))

    bright = np.where(np.asarray(mag) < good_mag_limit)
    astromScatter = np.median(np.asarray(dist)[bright])
    print("Astrometric scatter (median) - mag < %.1f : %.1f %s" %
          (good_mag_limit, astromScatter, "mas"))

    if astromScatter > medianRef:
        print("Median astrometric scatter %.1f %s is larger than reference : %.1f %s " %
              (astromScatter, "mas", medianRef, "mas"))
    if match < matchRef:
        print("Number of matched sources %d is too small (shoud be > %d)" % (match, matchRef))

    return astromScatter


def checkPhotometry(mag, mmagrms, dist, match,
                    good_mag_limit=19.5,
                    medianRef=100, matchRef=500):
    """Print out the astrometric scatter for all stars, and for good stars.

    Inputs
    ------
    mag : list or numpy.array
        Average magnitudes of each star
    mmagrms ; list or numpy.array
        Magnitude RMS of the multiple observation of each star.
    dist : list or numpy.array
        Distances between successive measurements of one star
    match : int
        Number of stars matched.

    good_mag_limit : float, optional
        Minimum average brightness (in magnitudes) for a star to be considered.
    medianRef : float, optional
        Median reference astrometric scatter in millimagnitudes
    matchRef : int, optional
        Should match at least matchRef stars.

    Returns
    -------
    float
        The photometry scatter (RMS, millimag) for all good stars.

    Notes
    -----
    The scatter and match defaults are appropriate to SDSS are stored here.
    For SDSS, stars with mag < 19.5 should be completely well measured.
    This limit is a band-dependent statement most appropriate to r.
    """

    print("Median value of the photometric scatter - all magnitudes: %.3f %s" %
          (np.median(mmagrms), "mmag"))

    bright = np.where(np.asarray(mag) < good_mag_limit)
    photoScatter = np.median(np.asarray(mmagrms)[bright])
    print("Photometric scatter (median) - mag < %.1f : %.1f %s" %
          (good_mag_limit, photoScatter, "mmag"))

    if photoScatter > medianRef:
        print("Median photometric scatter %.3f %s is larger than reference : %.3f %s "
              % (photoScatter, "mmag", medianRef, "mag"))
    if match < matchRef:
        print("Number of matched sources %d is too small (shoud be > %d)"
              % (match, matchRef))

    return photoScatter

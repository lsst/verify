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
from scipy.optimize import curve_fit

import lsst.afw.geom as afwGeom
import lsst.pipe.base as pipeBase

from .util import averageRaDecFromCat


def isExtended(source, extendedKey, extendedThreshold=1.0):
    """Is the source extended attribute above the threshold.

    Parameters
    ----------
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

    Parameters
    ----------
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


def fitExp(x, y, y_err, deg=2):
    """Fit an exponential quadratic to x, y, y_err.
    """
    fit_params, fit_param_covariance = \
        curve_fit(expModel, x, y, p0=[1, 0.02, 5], sigma=y_err)

    return fit_params


def fitAstromErrModel(snr, dist):
    """Fit model of astrometric error from LSST Overview paper

    Parameters
    ----------
    snr : list or numpy.array
        Signal-to-noise ratio of photometric observations
    dist : list or numpy.array
        Scatter in measured positions [mas]

    Returns
    -------
    dict
        The fit results for C, theta, sigmaSys along with their Units.
    """
    fit_params, fit_param_covariance = \
        curve_fit(astromErrModel, snr, dist, p0=[1, 0.01])

    params = {'C': 1, 'theta': fit_params[0], 'sigmaSys': fit_params[1],
              'cUnits': '', 'thetaUnits': 'mas', 'sigmaSysUnits': 'mas'}
    return params


def fitPhotErrModel(mag, mmag_err):
    """Fit model of photometric error from LSST Overview paper

    Parameters
    ----------
    mag : list or numpy.array
        Magnitude
    mmag_err : list or numpy.array
        Magnitude uncertainty or variation in *mmag*.

    Returns
    -------
    dict
        The fit results for sigmaSys, gamma, and m5 along with their Units.
    """
    mag_err = mmag_err / 1000
    fit_params, fit_param_covariance = \
        curve_fit(photErrModel, mag, mag_err, p0=[0.01, 0.039, 24.35])

    params = {'sigmaSys': fit_params[0], 'gamma': fit_params[1], 'm5': fit_params[2],
              'sigmaSysUnits': 'mmag', 'gammaUnits': '', 'm5Units': 'mag'}
    return params


def positionRms(cat):
    """Calculate the RMS for RA, Dec for a set of observations an object.

    Parameters
    ----------
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


def checkAstrometry(snr, dist, match,
                    brightSnr=100,
                    medianRef=100, matchRef=500):
    """Print out the astrometric scatter for all stars, and for good stars.

    Parameters
    ----------
    snr : list or numpy.array
        Average PSF flux SNR of each star
    dist : list or numpy.array
        Distances between successive measurements of one star
    match : int
        Number of stars matched.

    brightSnr : float, optional
        Minimum average brightness (in magnitudes) for a star to be considered.
    medianRef : float, optional
        Median reference astrometric scatter in milliarcseconds.
    matchRef : int, optional
        Should match at least matchRef stars.

    Returns
    -------
    pipeBase.Struct
        name -- str: "checkAstrometry"
        model_name -- str: "astromErrModel"
        doc -- str: Description of astrometric error model
        params -- dict: Fit parameters as "name": value.
        astromRmsScatter -- float: 
           The astrometric scatter (RMS, milliarcsec) for all good stars.

    Notes
    -----
    The scatter and match defaults are appropriate to SDSS are the defaults
      for `medianRef` and `matchRef`
    For SDSS, stars with mag < 19.5 should be completely well measured.
    """

    print("Median value of the astrometric scatter - all magnitudes: %.3f %s" %
          (np.median(dist), "mas"))

    bright = np.where(np.asarray(snr) > brightSnr)
    astromScatter = np.median(np.asarray(dist)[bright])
    print("Astrometric scatter (median) - snr > %.1f : %.1f %s" %
          (brightSnr, astromScatter, "mas"))

    fit_params = fitAstromErrModel(snr[bright], dist[bright])

    if astromScatter > medianRef:
        print("Median astrometric scatter %.1f %s is larger than reference : %.1f %s " %
              (astromScatter, "mas", medianRef, "mas"))
    if match < matchRef:
        print("Number of matched sources %d is too small (shoud be > %d)" % (match, matchRef))

    return pipeBase.Struct(name="checkAstrometry",
                           model_name="astromErrModel",
                           doc=astromErrModel.__doc__,
                           params=fit_params,
                           astromRmsScatter=astromScatter) 


def checkPhotometry(snr, mag, mmagErr, mmagrms, dist, match,
                    brightSnr=100,
                    medianRef=100, matchRef=500):
    """Print out the astrometric scatter for all stars, and for good stars.

    Parameters
    ----------
    snr : list or numpy.array
        Median SNR of PSF flux
    mag : list or numpy.array
        Average magnitudes of each star.  [mag]
    mmagErr : list or numpy.array
        Uncertainties in magnitudes of each star.  [mmag]
    mmagrms : list or numpy.array
        Magnitude RMS of the multiple observation of each star. [mmag]
    dist : list or numpy.array
        Distances between successive measurements of one star
    match : int
        Number of stars matched.
    brightSnr : float, optional
        Minimum SNR for a star to be considered "bright".
    medianRef : float, optional
        Median reference astrometric scatter in millimagnitudes
    matchRef : int, optional
        Should match at least matchRef stars.

    Returns
    -------
    pipeBase.Struct
        name -- str: "checkPhotometry"
        model_name -- str:  "photErrModel"
        doc -- str: Description of photometric error model
        params -- dict: Fit parameters as "name": value.
        photRmsScatter -- float: 
            The photometric scatter (RMS, mmag) for all good star stars.

    Notes
    -----
    The scatter and match defaults are appropriate to SDSS are stored here.
    For SDSS, stars with mag < 19.5 should be completely well measured.
    This limit is a band-dependent statement most appropriate to r.
    """

    print("Median value of the photometric scatter - all magnitudes: %.3f %s" %
          (np.median(mmagrms), "mmag"))

    bright = np.where(np.asarray(snr) > brightSnr)
    photScatter = np.median(np.asarray(mmagrms)[bright])
    print("Photometric scatter (median) - SNR > %.1f : %.1f %s" %
          (brightSnr, photScatter, "mmag"))

    fit_params = fitPhotErrModel(mag[bright], mmagErr[bright])

    if photScatter > medianRef:
        print("Median photometric scatter %.3f %s is larger than reference : %.3f %s "
              % (photScatter, "mmag", medianRef, "mag"))
    if match < matchRef:
        print("Number of matched sources %d is too small (shoud be > %d)"
              % (match, matchRef))

    return pipeBase.Struct(name="checkPhotometry",
                           model_name="photErrModel",
                           doc=photErrModel.__doc__,
                           params=fit_params,
                           photRmsScatter=photScatter)


def astromErrModel(snr, theta=1000, sigmaSys=10, C=1, **kwargs):
    """Calculate expected astrometric uncertainty based on SNR.

    mas = C*theta/SNR + sigmaSys

    Parameters
    ----------
    snr : list or numpy.array
        S/N of photometric measurements
    theta : float or numpy.array, optional
        Seeing
    sigmaSys : float
        Systematic error floor
    C : float
        Scaling factor

    theta and sigmaSys must be given in the same units.  
    Typically choices might be any of arcsec, milli-arcsec, or radians
    The default values are reasonable astronominal values in milliarcsec.
    But the only thing that matters is that they're the same.

    Returns
    -------
    np.array
        Expected astrometric uncertainty.
        Units will be those of theta + sigmaSys.
    """
    return C*theta/snr + sigmaSys


def photErrModel(mag, sigmaSys, gamma, m5, **kwargs):
    """Fit model of photometric error from LSST Overview paper
    http://arxiv.org/abs/0805.2366v4

    Photometric errors described by
    Eq. 4
    sigma_1^2 = sigma_sys^2 + sigma_rand^2

    Eq. 5
    sigma_rand^2 = (0.04 - gamma) * x + gamma * x^2 [mag^2]
    where x = 10**(0.4*(m-m_5))

    Parameters
    ----------
    mag : list or numpy.array
        Magnitude
    sigmaSq : float
        Limiting systematics floor [mag]
    gamma : float
        proxy for sky brightness and readout noise
    m5 : float
        5-sigma depth [mag]

    Returns
    -------
    numpy.array
        Result of noise estimation function
    """
    x = 10**(0.4*(mag - m5))
    sigmaRandSq = (0.04 - gamma) * x + gamma * x**2
    sigmaSq = sigmaSys**2 + sigmaRandSq
    return np.sqrt(sigmaSq)

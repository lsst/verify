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

import math

import numpy as np
import scipy.stats

import lsst.pipe.base as pipeBase

from .base import ValidateErrorNoStars
from .util import averageRaFromCat, averageDecFromCat
from .srdSpec import srdSpec, getAstrometricSpec


def calcPA1(matches, magKey, numRandomShuffles=50, verbose=False):
    """Calculate the photometric repeatability of measurements across a set of observations.

    Parameters
    ----------
    matches : lsst.afw.table.GroupView
         GroupView object of matched observations from MultiMatch.
    magKey : lookup key to a `schema`
         The lookup key of the field storing the magnitude of interest.
         E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
         where `allMatches` is the result of lsst.afw.table.MultiMatch.finish()
    numRandomShuffles : int
        Number of times to draw random pairs from the different observations.
    verbose : bool, optional
        Output additional information on the analysis steps.

    Returns
    -------
    pipeBase.Struct
        name -- str: 'PA1'.  Name of Key Performance Metric stored in this struct.
        rms -- average RMS
        iqr -- and average inter-quartile range (IQR)
        rmsStd -- standard deviation of the RMS
        iqrStd -- standard deviation of the IQR
           These 4 quantities are derived from the `numRandomShuffles` trials.
        magDiffs -- differences between pairs of observations.  Selected from one random trial.
        magMean -- mean magnitude of each object.

    Notes
    -----
    We calculate differences for 50 different random realizations
    of the measurement pairs, to provide some estimate of the uncertainty
    on our RMS estimates due to the random shuffling.
    This estimate could be stated and calculated from a more formally
    derived motivation but in practice 50 should be sufficient.

    The LSST Science Requirements Document (LPM-17), or SRD,
    characterizes the photometric repeatability by putting a requirement
    on the median RMS of measurements of non-variable bright stars.
    This quantity is PA1, with a design, minimum, and stretch goals of
      (5, 8, 3) millimag
    following LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.

    This present routine calculates this quantity in two different ways:
       RMS
       interquartile range (IQR)
    and also returns additional quantities of interest:
      the pair differences of observations of stars,
      the mean magnitude of each star

    While the SRD specifies that we should just compute the RMS directly,
       the current filter doesn't screen out variable stars as carefully
       as the SRD specifies, so using a more robust estimator like the IQR
       allows us to reject some outliers.
    However, the IRQ is also less sensitive some realistic sources of scatter
       such as bad zero points, that the metric should include.

    See Also
    --------
    doCalcPA1 : Worker routine that calculates PA1 for one random sample.
    calcPA2 : Calculate photometric repeatability outlier fraction.

    Examples
    --------
    >>> import lsst.daf.persistence as dafPersist
    >>> from lsst.afw.table import SourceCatalog, SchemaMapper, Field
    >>> from lsst.afw.table import MultiMatch, SourceRecord, GroupView
    >>> repo = "CFHT/output"
    >>> butler = dafPersist.Butler(repo)
    >>> dataset = 'src'
    >>> schema = butler.get(dataset + "_schema", immediate=True).schema
    >>> mmatch = MultiMatch(newSchema,
    >>>                     dataIdFormat={'visit': int, 'ccd': int},
    >>>                     radius=matchRadius,
    >>>                     RecordClass=SourceRecord)
    >>> for vId in visitDataIds:
    ...     cat = butler.get('src', vId)
    ...     mmatch.add(catalog=cat, dataId=vId)
    ...
    >>> matchCat = mmatch.finish()
    >>> allMatches = GroupView.build(matchCat)
    >>> allMatches
    >>> psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
    >>> pa1 = calcPA1(allMatches, psfMagKey)
    >>> print("LSST SRD Key Performance Metric %s" % pa1.name)
    >>> print("The RMS was %.3f+-%.3f, the IQR was %.3f+-%.3f" % (pa1.rms, pa1.iqr, pa1.rmsStd, pa1.iqrStd))
    """

    pa1Samples = [doCalcPA1(matches, magKey) for n in range(numRandomShuffles)]
    rmsPA1 = np.array([pa1.rms for pa1 in pa1Samples])
    iqrPA1 = np.array([pa1.iqr for pa1 in pa1Samples])

    PA1=np.mean(iqrPA1)
    return pipeBase.Struct(name='PA1',
                           PA1=PA1, pa1Units='mmag',
                           rms=np.mean(rmsPA1), iqr=np.mean(iqrPA1),
                           rmsStd=np.std(rmsPA1), iqrStd=np.std(iqrPA1),
                           rmsUnits='mmag', iqrUnits='mmag',
                           magDiffs=pa1Samples[0].magDiffs, magMean=pa1Samples[0].magMean,
                           magDiffsUnits='mmag', magMeanUnits='mag')


def doCalcPA1(groupView, magKey):
    """Calculate PA1 for one random realization.

    Parameters
    ----------
    groupView : lsst.afw.table.GroupView
         GroupView object of matched observations from MultiMatch.
    magKey : lookup key to a `schema`
         The lookup key of the field storing the magnitude of interest.
         E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
         where `allMatches` is the result of lsst.afw.table.MultiMatch.finish()

    Returns
    -------
    pipeBase.Struct
       The RMS, inter-quartile range,
       differences between pairs of observations, mean mag of each object.
    """

    magDiffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
    magMean = groupView.aggregate(np.mean, field=magKey)
    rmsPA1, iqrPA1 = computeWidths(magDiffs)
    return pipeBase.Struct(rms=rmsPA1, iqr=iqrPA1,
                           rmsUnits='mmag', iqrUnits='mmag',
                           magDiffs=magDiffs, magMean=magMean,
                           magDiffsUnits='mmag', magMeanUnits='mag')


def calcPA2(groupView, magKey, defaultLevel='design', verbose=False):
    """Calculate the fraction of outliers from PA1.

    Calculate the fraction of outliers from the median RMS characterizaing
    the photometric repeatability of measurements as calculated via `calcPA1`.

    Parameters
    ----------
    groupView : lsst.afw.table.GroupView
         GroupView object of matched observations from MultiMatch.
    magKey : lookup key to a `schema`
         The lookup key of the field storing the magnitude of interest.
         E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
         where `allMatches` is a the result of lsst.afw.table.MultiMatch.finish()
    defaultLevel : str
        One of ('design', 'minimum', 'stretch')
        While performance against all levels i computed
        the summary 'PA2', and 'PF1' numbers are presented for `defaultLevel`.
    verbose : bool, optional
        Output additional information on the analysis steps.

    Returns
    -------
    pipeBase.Struct
        name -- str: 'PA2'.  Name of Key Performance Metric stored in this struct.
       Contains the results of calculating PA2, the millimags of variation at the
       `design`, `minimum`, and `stretch` fraction of outliers
       The specified fractions are also avialable as `PF1`.

    See Also
    --------
    calcPA1 : Calculate photometric repeatability median RMS

    Examples
    --------
    >>> import lsst.daf.persistence as dafPersist
    >>> from lsst.afw.table import SourceCatalog, SchemaMapper, Field
    >>> from lsst.afw.table import MultiMatch, SourceRecord, GroupView
    >>> repo = "CFHT/output"
    >>> butler = dafPersist.Butler(repo)
    >>> dataset = 'src'
    >>> schema = butler.get(dataset + "_schema", immediate=True).schema
    >>> mmatch = MultiMatch(newSchema,
    >>>                     dataIdFormat={'visit': int, 'ccd': int},
    >>>                     radius=matchRadius,
    >>>                     RecordClass=SourceRecord)
    >>> for vId in visitDataIds:
    ...     cat = butler.get('src', vId)
    ...     mmatch.add(catalog=cat, dataId=vId)
    ...
    >>> matchCat = mmatch.finish()
    >>> allMatches = GroupView.build(matchCat)
    >>> allMatches
    >>> psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
    >>> pa2 = calcPA2(allMatches, psfMagKey)
    >>> print("LSST SRD Key Performance Metric %s" % pa2.name)
    >>> print("minimum: PF1=%2d%% of magDiffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" %
    ...       (pa2.PF1['minimum'], pa2.PA2_measured['minimum']))
    >>> print("design:  PF1=%2d%% of magDiffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" %
    ...       (pa2.PF1['design'], pa2.PA2_measured['design']))
    >>> print("stretch: PF1=%2d%% of magDiffs more than PA2 = %4.2f mmag (target is PA2 < 10 mmag)" %
    ...       (pa2.PF1['stretch'], pa2.PA2_measured['stretch']))


    Notes
    -----
    The LSST Science Requirements Document (LPM-17) is commonly referred
    to as the SRD.  The SRD puts a limit that no more than PF1 % of difference
    will vary by more than PA2 millimag.  The design, minimum, and stretch goals
    are PF1 = (10, 20, 5) % at PA2 = (15, 15, 10) millimag
      following LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.
    """

    PA2_spec = srdSpec.PA2

    magDiffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
    PF1_percentiles = 100 - np.asarray([srdSpec.PF1[l] for l in srdSpec.levels])
    PA2_measured = dict(zip(srdSpec.levels,
                            np.percentile(np.abs(magDiffs), PF1_percentiles)))

    PF1_measured = {l: 100*np.mean(np.asarray(magDiffs) > srdSpec.PA2[l]) 
                    for l in srdSpec.levels}

    return pipeBase.Struct(name='PA2', pa2Units='mmag', pf1Units='%',
                           PA2=PA2_measured['design'], PF1=PF1_measured['design'],
                           PA2_measured=PA2_measured,
                           PF1_measured=PF1_measured,
                           PF1_spec=srdSpec.PF1, PA2_spec=PA2_spec)


def getRandomDiffRmsInMas(array):
    """Calculate the RMS difference in mmag between a random pairs of magnitudes.

    Input
    -----
    array : list or np.array
        Magnitudes from which to select the pair  [mag]

    Returns
    -------
    float
        RMS difference

    Notes
    -----
    The LSST SRD recommends computing repeatability from a histogram of
    magnitude differences for the same star measured on two visits
    (using a median over the magDiffs to reject outliers).
    Because we have N>=2 measurements for each star, we select a random
    pair of visits for each star.  We divide each difference by sqrt(2)
    to obtain RMS about the (unknown) mean magnitude,
    instead of obtaining just the RMS difference.

    See Also
    --------
    getRandomDiff : Get the difference

    Examples
    --------
    >>> mag = [24.2, 25.5]
    >>> rms = getRandomDiffRmsInMas(mag)
    >>> print(rms)
    212.132034
    """
    # For scalars, math.sqrt is several times faster than numpy.sqrt.
    return (1000/math.sqrt(2)) * getRandomDiff(array)


def getRandomDiff(array):
    """Get the difference between two randomly selected elements of an array.

    Input
    -----
    array : list or np.array

    Returns
    -------
    float or int
        Difference between two random elements of the array.

    Notes
    -----
    * As implemented the returned value is the result of subtracting
        two elements of the input array.  In all of the imagined uses
        that's going to be a scalar (float, maybe int).
        In principle, however the code as implemented returns the result
        of subtracting two elements of the array, which could be any
        arbitrary object that is the result of the subtraction operator
        applied to two elements of the array.
    * This is not the most efficient way to extract a pair,
        but it's the easiest to write.
    * Shuffling works correctly for low N (even N=2), where a naive
        random generation of entries would result in duplicates.
    * In principle it might be more efficient to shuffle the indices,
        then extract the difference.  But this probably only would make a
        difference for arrays whose elements were objects that were
        substantially larger than a float.  And that would only make
        sense for objects that had a subtraction operation defined.
    """
    copy = array.copy()
    np.random.shuffle(copy)
    return copy[0] - copy[1]


def computeWidths(array):
    """Compute the RMS and the scaled inter-quartile range of an array.

    Input
    -----
    array : list or np.array

    Returns
    -------
    float, float
        RMS and scaled inter-quartile range (IQR).

    Notes
    -----
    We estimate the width of the histogram in two ways:
       using a simple RMS,
       using the interquartile range (IQR)
    The IQR is scaled by the IQR/RMS ratio for a Gaussian such that it
       if the array is Gaussian distributed, then the scaled IQR = RMS.
    """
    rmsSigma = math.sqrt(np.mean(array**2))
    iqrSigma = np.subtract.reduce(np.percentile(array, [75, 25])) / (scipy.stats.norm.ppf(0.75)*2)
    return rmsSigma, iqrSigma


def sphDist(ra1, dec1, ra2, dec2):
    """Calculate distance on the surface of a unit sphere.

    Input and Output are in radians.

    Notes
    -----
    Uses the Haversine formula to preserve accuracy at small angles.

    Law of cosines approach doesn't work well for the typically very small
    differences that we're looking at here.
    """
    # Haversine
    dra = ra1-ra2
    ddec = dec1-dec2
    a = np.square(np.sin(ddec/2)) + \
        np.cos(dec1)*np.cos(dec2)*np.square(np.sin(dra/2))
    dist = 2 * np.arcsin(np.sqrt(a))

    # This is what the law of cosines would look like
#    dist = np.arccos(np.sin(dec1)*np.sin(dec2) + np.cos(dec1)*np.cos(dec2)*np.cos(ra1 - ra2))

    # Could use afwCoord.angularSeparation()
    #  but (a) that hasn't been made accessible through the Python interface
    #  and (b) I'm not sure that it would be faster than the numpy interface.
    #    dist = afwCoord.angularSeparation(ra1-ra2, dec1-dec2, np.cos(dec1), np.cos(dec2))

    return dist


def matchVisitComputeDistance(visit_obj1, ra_obj1, dec_obj1,
                              visit_obj2, ra_obj2, dec_obj2):
    """Calculate obj1-obj2 distance for each visit in which both objects are seen.

    For each visit shared between visit_obj1 and visit_obj2,
    calculate the spherical distance between the obj1 and obj2.

    Parameters
    ----------
    visit_obj1 : scalar, list, or numpy.array of int or str
        List of visits for object 1.
    ra_obj1 : scalar, list, or numpy.array of float
        List of RA in each visit for object 1.
    dec_obj1 : scalar, list or numpy.array of float
        List of Dec in each visit for object 1.
    visit_obj2 : list or numpy.array of int or str
        List of visits for object 2.
    ra_obj2 : list or numpy.array of float
        List of RA in each visit for object 2.
    dec_obj2 : list or numpy.array of float
        List of Dec in each visit for object 2.

    Results
    -------
    list of float
        spherical distances (in radians) for matching visits.
    """
    distances = []
    for i in range(len(visit_obj1)):
        for j in range(len(visit_obj2)):
            if (visit_obj1[i] == visit_obj2[j]):
                if np.isfinite([ra_obj1[i], dec_obj1[i],
                                ra_obj2[j], dec_obj2[j]]).all():
                    distances.append(sphDist(ra_obj1[i], dec_obj1[i],
                                             ra_obj2[j], dec_obj2[j]))
    return distances


def arcminToRadians(arcmin):
    return np.deg2rad(arcmin/60)

def radiansToMilliarcsec(rad):
    return np.rad2deg(rad)*3600*1000


def calcAM1(*args, **kwargs):
    """Calculate the SRD definition of astrometric performance for AM1

    See `calcAMx` for more details."""
    return calcAMx(*args, x=1, D=srdSpec.D1, width=2, **kwargs)

def calcAM2(*args, **kwargs):
    """Calculate the SRD definition of astrometric performance for AM2

    See `calcAMx` for more details."""
    return calcAMx(*args, x=2, D=srdSpec.D2, width=2, **kwargs)

def calcAM3(*args, **kwargs):
    """Calculate the SRD definition of astrometric performance for AM3

    See `calcAMx` for more details."""
    return calcAMx(*args, x=3, D=srdSpec.D3, width=2, **kwargs)

def calcAMx(groupView, D=5, width=2, magRange=None,
            x=None, level="design", 
            verbose=False,
           ):
    """Calculate the SRD definition of astrometric performance

    Parameters
    ----------
    groupView : lsst.afw.table.GroupView
         GroupView object of matched observations from MultiMatch.
    D : float
        Fiducial distance between two objects to consider. [arcmin]
    width : float
        Width around fiducial distance to include. [arcmin]
    magRange : 2-element list or tuple
        brighter, fainter limits of the magnitude range to include.
        E.g., `magRange=[17.5, 21.0]`
    x : int
        Which of AM1, AM2, AM3.  One of [1,2,3].
    level : str
        One of "minimum", "design", "stretch" indicating the level of the specification desired.

    Returns
    -------
    pipeBase.Struct
        rmsDistMas, annulus, magRange

    Raises
    ------
    ValueError if `x` isn't in `getAstrometricSpec` values of [1,2,3]

    Notes
    -----
    This table below is provided in this package in the `srdSpec.py` file.

    LPM-17 dated 2011-07-06

    *The relative astrometry*
    Specification: The rms of the astrometric distance distribution for
        stellar pairs with separation of D arcmin (repeatability)
        will not exceed AMx milliarcsec (median distribution for a large number
        of sources). No more than AFx % of the sample will deviate by more than
        ADx milliarcsec from the median. AMx, AFx, and ADx are specified for
        D=5, 20 and 200 arcmin for x= 1, 2, and 3, in the same order (Table 18).

    The three selected characteristic distances reflect the size of an
    individual sensor, a raft, and the camera. The required median astrometric
    precision is driven by the desire to achieve a proper motion accuracy of
    0.2 mas/yr and parallax accuracy of 1.0 mas over the course of the survey.
    These two requirements correspond to relative astrometric precision for a
    single image of 10 mas (per coordinate).

    ================== =========== ============ ============
         Quantity      Design Spec Minimum Spec Stretch Goal
    ------------------ ----------- ------------ ------------
    AM1 (milliarcsec)        10          20            5
    AF1 (%)                  10          20            5
    AD1 (milliarcsec)        20          40           10

    AM2 (milliarcsec)        10          20            5
    AF2 (%)                  10          20            5
    AD2 (milliarcsec)        20          40           10

    AM3 (milliarcsec)        15          30           10
    AF3 (%)                  10          20            5
    AD3 (milliarcsec)        30          50           20
    =================  =========== ============ ============
    Table 18: The specifications for astrometric precision.
    The three blocks of values correspond to D=5, 20 and 200 arcmin,
    and to astrometric measurements performed in the r and i bands.
    """

    AMx_spec, AFx_spec, ADx_spec = getAstrometricSpec(x=x, level=level)

    annulus = D + (width/2)*np.array([-1, +1])

    rmsDistances, annulus, magRange = \
        calcRmsDistances(groupView, annulus, magRange=magRange, verbose=verbose)

    if not list(rmsDistances):
        raise ValidateErrorNoStars('No stars found that are %.1f--%.1f arcmin apart.' %
                                   (annulus[0], annulus[1]))

    rmsDistMas = radiansToMilliarcsec(rmsDistances)
    AMx = np.median(rmsDistMas)
    fractionOver = np.mean(np.asarray(rmsDistMas) > AMx_spec+ADx_spec)
    percentOver = 100*fractionOver

    return pipeBase.Struct(
        name='AM%d' % x,
        AMx=AMx,
        amxUnits='mas',
        rmsDistMas=rmsDistMas,
        rmsUnits='mas',
        fractionOver=fractionOver,
        AFx=percentOver,
        D=D,
        DUnits='arcmin',
        annulus=annulus,
        annulusUnits='arcmin',
        magRange=magRange,
        magRangeUnits='mag',
        x=x,
        level=level,
        AMx_spec=AMx_spec,
        AFx_spec=AFx_spec,
        ADx_spec=ADx_spec,
        afxUnits='%',
        adxUnits='mas',
        )


def calcRmsDistances(groupView, annulus, magRange=None, verbose=False):
    """Calculate the RMS distance of a set of matched objects over visits.

    Parameters
    ----------
    groupView : lsst.afw.table.GroupView
        GroupView object of matched observations from MultiMatch.
    annulus : 2-element list or tuple of float
        Distance range in which to compare object.  [arcmin]
        E.g., `annulus=[19, 21]` would consider all objects
        separated from each other between 19 and 21 arcminutes.
    magRange : 2-element list or tuple of float, optional
        Magnitude range from which to select objects.
        Default of `None` will result in all objects being considered.
    verbose : bool, optional
        Output additional information on the analysis steps.

    Returns
    -------
    list
        rmsDistMas

    """

    # Default is specified here separately because defaults that are mutable
    # get overridden by previous calls of the function.
    if magRange is None:
        magRange = [17.0, 21.5]

    # First we make a list of the keys that we want the fields for
    importantKeys = [groupView.schema.find(name).key for
                     name in ['id', 'coord_ra', 'coord_dec',
                              'object', 'visit', 'base_PsfFlux_mag']]

    # Includes magRange through closure
    def magInRange(cat):
        mag = cat.get('base_PsfFlux_mag')
        w, = np.where(np.isfinite(mag))
        medianMag = np.median(mag[w])
        return magRange[0] <= medianMag and medianMag < magRange[1]

    groupViewInMagRange = groupView.where(magInRange)

    # List of lists of id, importantValue
    matchKeyOutput = [obj.get(key) for key in importantKeys for obj in groupViewInMagRange.groups]

    jump = len(groupViewInMagRange)

    ra = matchKeyOutput[1*jump:2*jump]
    dec = matchKeyOutput[2*jump:3*jump]
    visit = matchKeyOutput[4*jump:5*jump]

    # Calculate the mean position of each object from its constituent visits
    # `aggregate` calulates a quantity for each object in the groupView.
    meanRa = groupViewInMagRange.aggregate(averageRaFromCat)
    meanDec = groupViewInMagRange.aggregate(averageDecFromCat)

    annulusRadians = arcminToRadians(annulus)

    rmsDistances = list()
    for obj1, (ra1, dec1, visit1) in enumerate(zip(meanRa, meanDec, visit)):
        dist = sphDist(ra1, dec1, meanRa[obj1+1:], meanDec[obj1+1:])
        objectsInAnnulus, = np.where((annulusRadians[0] <= dist) & (dist < annulusRadians[1]))
        for obj2 in objectsInAnnulus:
            distances = matchVisitComputeDistance(visit[obj1], ra[obj1], dec[obj1],
                                                  visit[obj2], ra[obj2], dec[obj2])
            if not distances:
                if verbose:
                    print("No matching visits found for objs: %d and %d" % (obj1, obj2))
                continue

            finiteEntries, = np.where(np.isfinite(distances))
            if len(finiteEntries) > 0:
                rmsDist = np.std(np.array(distances)[finiteEntries])
                rmsDistances.append(rmsDist)

    return rmsDistances, annulus, magRange

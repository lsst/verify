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

import os.path
import sys

import numpy as np

import lsst.daf.persistence as dafPersist
import lsst.pipe.base as pipeBase
from lsst.afw.table import SourceCatalog, SchemaMapper, Field
from lsst.afw.table import MultiMatch, SourceRecord, GroupView

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
# import lsst.afw.coord as afwCoord

from .base import ValidateError
from .util import averageRaDec
from .plotAstrometryPhotometry import plotAstrometry, plotPhotometry, plotPA1, plotAM1, plotAM2, plotAM3
from .calcSrd import computeWidths, getRandomDiff, calcPA1, calcPA2, calcAM1, calcAM2, calcAM3
from .srdSpec import srdSpec, getAstrometricSpec


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
    N = len(mag)
    normDiff = (mag - mag_avg) / magerr
    

def positionDiff(cat):
    """Calculate the diff RA, Dec from the mean for a set of observations an object for each observation.

    @param[in]  cat -- Collection with a .get method 
         for 'coord_ra', 'coord_dec' that returns radians.

    @param[out]  pos_median -- median diff of positions in milliarcsec.  Float.
    """
    ra_avg, dec_avg = averageRaDec(cat)
    ra, dec = cat.get('coord_ra'), cat.get('coord_dec')
    # Approximating that the cos(dec) term is roughly the same
    #   for all observations of this object.
    ra_diff  = (ra - ra_avg) * np.cos(dec)**2
    dec_diff = dec - dec_avg
    pos_diff = np.sqrt(ra_diff**2 + dec_diff**2)  # radians
    pos_diff = [afwGeom.radToMas(p) for p in pos_diff]  # milliarcsec

    return pos_diff


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
    ra_avg, dec_avg = averageRaDec(cat)
    ra, dec = cat.get('coord_ra'), cat.get('coord_dec')
    # Approximating that the cos(dec) term is roughly the same
    #   for all observations of this object.
    ra_var = np.var(ra) * np.cos(dec_avg)**2
    dec_var = np.var(dec)
    pos_rms = np.sqrt(ra_var + dec_var)  # radians
    pos_rms = afwGeom.radToMas(pos_rms)  # milliarcsec

    return pos_rms


def loadAndMatchData(repo, visitDataIds,
                     matchRadius=afwGeom.Angle(1, afwGeom.arcseconds)):
    """Load data from specific visit.  Match with reference.

    Inputs
    ------
    repo : string
        The repository.  This is generally the directory on disk
        that contains the repository and mapper.
    visitDataIds : list of dict
        List of `butler` data IDs of Image catalogs to compare to reference.
        The `calexp` cpixel image is needed for the photometric calibration.
    matchRadius :  afwGeom.Angle().
        Radius for matching. 

    Returns
    -------
    afw.table.GroupView
        An object of matched catalog.
    """

    # Following 
    # https://github.com/lsst/afw/blob/tickets/DM-3896/examples/repeatability.ipynb
    butler = dafPersist.Butler(repo)
    dataset = 'src'

    dataRefs = [dafPersist.ButlerDataRef(butler, vId) for vId in visitDataIds]

    ccdKeyName = getCcdKeyName(visitDataIds[0])

    schema = butler.get(dataset + "_schema", immediate=True).schema
    mapper = SchemaMapper(schema)
    mapper.addMinimalSchema(schema)
    mapper.addOutputField(Field[float]('base_PsfFlux_mag', "PSF magnitude"))
    mapper.addOutputField(Field[float]('base_PsfFlux_magerr', "PSF magnitude uncertainty"))
    newSchema = mapper.getOutputSchema()

    # Create an object that can match multiple catalogs with the same schema
    mmatch = MultiMatch(newSchema, 
                        dataIdFormat = {'visit': int, ccdKeyName: int},
                        radius=matchRadius,
                        RecordClass=SourceRecord)

    # create the new extented source catalog
    srcVis = SourceCatalog(newSchema)

    for vId in visitDataIds:
        calib = afwImage.Calib(butler.get("calexp_md", vId, immediate=True))
        calib.setThrowOnNegativeFlux(False)
        oldSrc = butler.get('src', vId, immediate=True)
        print(len(oldSrc), "sources in ccd: ", vId[ccdKeyName])

        # create temporary catalog
        tmpCat = SourceCatalog(SourceCatalog(newSchema).table)
        tmpCat.extend(oldSrc, mapper=mapper)
        (tmpCat['base_PsfFlux_mag'][:],
         tmpCat['base_PsfFlux_magerr'][:]) = \
             calib.getMagnitude(tmpCat['base_PsfFlux_flux'],
                                tmpCat['base_PsfFlux_fluxSigma'])
        srcVis.extend(tmpCat, False)
        mmatch.add(catalog=tmpCat, dataId=vId)

    # Complete the match, returning a catalog that includes all matched sources with object IDs that can be used to group them.
    matchCat = mmatch.finish()

    # Create a mapping object that allows the matches to be manipulated as a mapping of object ID to catalog of sources.
    allMatches = GroupView.build(matchCat)
    
    return allMatches


def analyzeData(allMatches, good_mag_limit=19.5):
    """Calculate summary statistics for each star.

    Inputs
    ------
    allMatches : afw.table.GroupView 
        GroupView object with matches.
    good_mag_limit : float, optional
        Minimum average brightness (in magnitudes) for a star to be considered.

    Returns
    ------- 
    pipeBase.Struct 
        Containing mag, magerr, magrms, dist, and number of matches.
    """

    # Filter down to matches with at least 2 sources and good flags
    flagKeys = [allMatches.schema.find("base_PixelFlags_flag_%s" % flag).key
                for flag in ("saturated", "cr", "bad", "edge")]
    nMatchesRequired = 2

    psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
    psfMagErrKey = allMatches.schema.find("base_PsfFlux_magerr").key
    extendedKey = allMatches.schema.find("base_ClassificationExtendedness_value").key

    def goodFilter(cat):
        if len(cat) < nMatchesRequired:
            return False
        for flagKey in flagKeys:
            if cat.get(flagKey).any():
                return False
        if not np.isfinite(cat.get(psfMagKey)).all():
            return False
        return True

    goodMatches = allMatches.where(goodFilter)

    # Filter further to a limited range in magnitude and extendedness 
    # to select bright stars.  
    safeMaxMag = good_mag_limit
    safeMaxExtended = 1.0

    def safeFilter(cat):
        psfMag = np.mean(cat.get(psfMagKey))
        extended = np.max(cat.get(extendedKey))
        return psfMag <= safeMaxMag and extended < safeMaxExtended

    safeMatches = goodMatches.where(safeFilter)

    # Pass field=psfMagKey so np.mean just gets that as its input
    goodPsfMag = goodMatches.aggregate(np.mean, field=psfMagKey)
    goodPsfMagRms = goodMatches.aggregate(np.std, field=psfMagKey)
    goodPsfMagErr = goodMatches.aggregate(np.median, field=psfMagErrKey)
    goodPsfMagNormDiff = goodMatches.aggregate(magNormDiff)
    # positionRms knows how to query a group so we give it the whole thing
    #   by going with the default `field=None`.
    dist = goodMatches.aggregate(positionRms)

    # We calculate differences for 50 different random realizations of the measurement pairs, 
    # to provide some estimate of the uncertainty on our RMS estimates due to the random shuffling 
    # This estimate could be stated and calculated from a more formally derived motivation
    #   but in practice 50 should be sufficient.
    numRandomShuffles = 50
    pa1_samples = [calcPA1(safeMatches, psfMagKey) 
                   for n in range(numRandomShuffles)]
    rmsPA1 = np.array([pa1.rms for pa1 in pa1_samples])
    iqrPA1 = np.array([pa1.iqr for pa1 in pa1_samples])

    print("PA1(RMS) = %4.2f+-%4.2f mmag" % (rmsPA1.mean(), rmsPA1.std()))
    print("PA1(IQR) = %4.2f+-%4.2f mmag" % (iqrPA1.mean(), iqrPA1.std()))

    info_struct = pipeBase.Struct(
        mag = goodPsfMag,
        magerr = goodPsfMagErr,
        magrms = goodPsfMagRms,
        dist = dist,
        match = len(dist)
    )

    return info_struct, safeMatches


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
        print("Median photometric scatter %.3f %s is larger than reference : %.3f %s " % (photoScatter, "mmag", medianRef, "mag"))
    if match < matchRef:
        print("Number of matched sources %d is too small (shoud be > %d)" % (match, matchRef))

    return photoScatter


def printPA2(gv, magKey):
    """Calculate and print the calculated PA2 from the LSST SRD from a groupView."""

    pa2 = calcPA2(gv, magKey)
    print("minimum: PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" % 
          (pa2.PF1['minimum'], pa2.minimum))
    print("design:  PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" % 
          (pa2.PF1['design'], pa2.design))
    print("stretch: PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 10 mmag)" % 
          (pa2.PF1['stretch'], pa2.stretch))


def printAM1(*args, **kwargs):
    return printAMx(*args, x=1, **kwargs)

def printAM2(*args, **kwargs):
    return printAMx(*args, x=2, **kwargs)

def printAM3(*args, **kwargs):
    return printAMx(*args, x=3, **kwargs)

def printAMx(rmsDistMAS, annulus, magrange,
             x=None, level="design"):
    """Print the Astrometric performance.

    @param[in]  rmsDistMAS -- list of RMS variation of relative distance 
       between stars across a series of visits.
    @param[in]  annulus -- inner and outer radius of comparison annulus [arcmin]
    @param[in]  magrange -- lower and upper magnitude range
    @param[in]  level -- One of "minimum", "design", "stretch"
       indicating the level of the specification desired.

    @param[in]  x -- int in [1,2,3].  Which of AM1, AM2, AM3.

    Raises:
    -------
    ValidateError if `x` isn't in `getAstrometricSpec`

    Note:
    -----
    The use of 'annulus' below isn't properly tied to the SRD
     in the same way that srdSpec.AM1, sprdSpec.AF1, srdSpec.AD1 are
     because the rmsDistMAS has already assumed a D.
    """
    AMx, AFx, ADx = getAstrometricSpec(x=x, level=level)

    magBinLow, magBinHigh = magrange

    rmsRelSep = np.median(rmsDistMAS)
    pCentOver = 100*np.mean(np.asarray(rmsDistMAS) > AMx+ADx)

    print("Median of distribution of RMS of distance of stellar pairs.")
    print("%s goals" % level.upper())
    print("For stars from %.2f < mag < %.2f" % (magrange[0], magrange[1]))
    print("from D = [%.2f, %.2f] arcmin, is %.2f mas (target is <= %.2f mas)." % 
          (annulus[0], annulus[1], rmsRelSep, AMx))
    print("  %.2f%% of sample is > %.2f mas from AM%d=%.2f mas (target is <= %.2f%%)" %
          (pCentOver, ADx, x, AMx, AFx))



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


def run(repo, visitDataIds, good_mag_limit, 
        medianAstromscatterRef=25, medianPhotoscatterRef=25, matchRef=500):
    """Main executable.

    Inputs
    ------
    repo : string
        The repository.  This is generally the directory on disk
        that contains the repository and mapper.
    visitDataIds : list of dict
        List of `butler` data IDs of Image catalogs to compare to reference.
        The `calexp` cpixel image is needed for the photometric calibration.
    good_mag_limit : float
        Minimum average brightness (in magnitudes) for a star to be considered.
    """

    plotbase = repoNameToPrefix(repo)

    allMatches = loadAndMatchData(repo, visitDataIds)
    struct, safeMatches = analyzeData(allMatches, good_mag_limit)
    magavg = struct.mag
    magerr = struct.magerr
    magrms = struct.magrms
    dist = struct.dist
    match = struct.match

    mmagerr = 1000*magerr
    mmagrms = 1000*magrms

    checkAstrometry(magavg, mmagrms, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianAstromscatterRef, matchRef=matchRef)
    checkPhotometry(magavg, mmagrms, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianPhotoscatterRef, matchRef=matchRef)
    plotAstrometry(magavg, mmagerr, mmagrms, dist, match, good_mag_limit=good_mag_limit, plotbase=plotbase)
    plotPhotometry(magavg, mmagerr, mmagrms, dist, match, good_mag_limit=good_mag_limit, plotbase=plotbase)

    magKey = allMatches.schema.find("base_PsfFlux_mag").key
    plotPA1(safeMatches, magKey, plotbase=plotbase)
    printPA2(safeMatches, magKey)

    args = calcAM1(safeMatches)
    printAM1(*args)
    plotAM1(*args)

    args = calcAM2(safeMatches)
    printAM2(*args)
    plotAM2(*args)


def defaultData(repo):
    """Example of loading dataIds for use by checkAstrometry.

    This example is based on the CFHT data in validation_data_cfht
    and is provided here for reference.
    For general usage, write your own equivalent to defaultData 
    and then pass to the `checkAstrometry.run` method.
    See the same `__main___` below for an example.
    """
    # List of visits to be considered
    visits = [176837, 176846, 176850]

    # List of CCD to be considered (source catalogs will be concateneted)
    ccd = [10]  # , 12, 14, 18]
    filter = 'z'

    # Reference values for the median astrometric scatter and the number of matches
    good_mag_limit = 21
    medianAstromscatterRef = 25  # mas
    medianPhotoscatterRef = 25  # mmag
    matchRef = 5000

    visitDataIds = [{'visit': v, 'filter': filter, 'ccdnum': c} for v in visits
                    for c in ccd]

    return (visitDataIds, good_mag_limit, 
            medianAstromscatterRef, medianPhotoscatterRef, matchRef)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("""Usage: check_astrometry repo
where repo is the path to a repository containing the output of processCcd
""")
        sys.exit(1)

    repo = sys.argv[1]
    if not os.path.isdir(repo):
        print("Could not find repo %r" % (repo,))
        sys.exit(1)

    args = defaultData(repo)
    run(repo, *args)

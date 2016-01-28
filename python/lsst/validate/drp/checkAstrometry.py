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

import matplotlib.pylab as plt
import numpy as np
import scipy.stats

import lsst.daf.persistence as dafPersist
import lsst.pipe.base as pipeBase
from lsst.afw.table import SourceCatalog, SchemaMapper, Field
from lsst.afw.table import MultiMatch, SimpleRecord, GroupView

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
import lsst.afw.coord as afwCoord

# Plotting defaults
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['font.size'] = 20
plt.rcParams['axes.labelsize'] = 20
# plt.rcParams['figure.titlesize'] = 30

def getCcdKeyName(dataid):
    """Return the key in a dataId that's referring to the CCD or moral equivalent.

    @param dataid  A dictionary that will be searched for a key that matches
        an entry in the hardcoded list of possible names for the CCD field.

    Different camera mappings use different keys
      to indicate the different amps/ccds in the same exposure.
    We here look through the reference dataId to determine which one this.
    """
    possibleCcdFieldNames = ['ccd', 'ccdnum', 'camcol']

    for name in possibleCcdFieldNames:
        if name in dataid:
            return name
    else:
        return None


def isExtended(source, extendedKey, extendedThreshold=1.0):
    """Is the source extended attribute above the threshold.

    Higher values of extendedness indicate a resolved object
    that is larger than a point source.
    """
    return source.get(extendedKey) >= extendedThreshold

def averageRaDec(cat):
    """Calculate the RMS for RA, Dec for a set of observations an object."""
    ra = np.mean(cat.get('coord_ra'))
    dec = np.mean(cat.get('coord_dec'))
    return ra, dec

# Some thoughts from Paul Price on how to do the coordinate differences correctly:
#    mean = sum([afwGeom.Extent3D(coord.toVector()) 
#                for coord in coordList, afwGeom.Point3D(0, 0, 0)])
#    mean /= len(coordList)
#    mean = afwCoord.IcrsCoord(mean)

def positionDiff(cat):
    """Calculate the diff RA, Dec from the mean for a set of observations an object for each observation.

    @param[in]  cat -- Collection with a .get method 
         for 'coord_ra', 'coord_dec' that returns radians.

    @param[out]  pos_median -- median diff of positions in milliarcsec.  Float.

    This is WRONG!
    Doesn't do wrap-around
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

    @param[in]  cat -- Collection with a .get method 
         for 'coord_ra', 'coord_dec' that returns radians.

    @param[out]  pos_rms -- RMS of positions in milliarcsecond.  Float.

    This is WRONG!
    Doesn't do wrap-around
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

    @param repo  The repository.  This is generally the directory on disk
                    that contains the repository and mapper.
    @param visitDataIds   Butler Data ID of Image catalogs to compare to reference.
           The actual pixel image is also needed for now for the photometric calibration.
           List.

    @param matchRadius    Radius for matching.  afwGeom.Angle().

    Return a afw.table.GroupView object of matched catalog.
    """

    # Following 
    # https://github.com/lsst/afw/blob/tickets/DM-3896/examples/repeatability.ipynb
    butler = dafPersist.Butler(repo)
    dataset = 'src'

    dataRefs = [dafPersist.ButlerDataRef(butler, vId) for vId in visitDataIds]

    # retrieve the schema of the source catalog and extend it in order to add a field to record the ccd number
    ccdKeyName = getCcdKeyName(visitDataIds[0])

    schema = butler.get(dataset + "_schema", immediate=True).schema
    mapper = SchemaMapper(schema)
    mapper.addMinimalSchema(schema)
#    mapper.addOutputField(Field[int](ccdKeyName, "CCD number"))
    mapper.addOutputField(Field[float]('base_PsfFlux_mag', "PSF magnitude"))
    mapper.addOutputField(Field[float]('base_PsfFlux_magerr', "PSF magnitude uncertainty"))
    newSchema = mapper.getOutputSchema()

    # Create an object that can match multiple catalogs with the same schema
    mmatch = MultiMatch(newSchema, 
                        dataIdFormat = {'visit': int, ccdKeyName: int},
                        radius=matchRadius,
                        RecordClass=SimpleRecord)

    if False:
        # Create visit catalogs by merging those from constituent CCDs. We also convert from BaseCatalog to SimpleCatalog, but in the future we'll probably want to have the source transformation tasks generate SimpleCatalogs (or SourceCatalogs) directly.
        byVisit = {}
        for dataRef in dataRefs:
            catalog = byVisit.setdefault(dataRef.dataId["visit"], SimpleRecord.Catalog(schema))
            catalog.extend(dataRef.get(dataset, immediate=True), deep=True)

        # Loop over visits, adding them to the match.
        for visit, catalog in byVisit.iteritems():
            mmatch.add(catalog, dict(visit=visit))

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


# The SRD recommends computing repeatability from a histogram of magnitude differences for the same star measured on two visits (using a median over the diffs to reject outliers). Since our dataset includes N>2 measurements for each star, we select a random pair of visits for each star.
# We also divide each difference by sqrt(2), because we want the RMS about the (unknown) mean magnitude, not the RMS difference, and convert from mags to mmag.
def getRandomDiff(array):
    # not the most efficient way to extract a pair, but it's the easiest to write
    copy = array.copy()
    np.random.shuffle(copy)
    return 1000*(copy[0] - copy[1])/(2**0.5)

# We estimate the width of the histogram in two ways: using a simple RMS, and using the interquartile range (scaled by the IQR/RMS ratio for a Gaussian). We do this for 50 different random realizations of the measurement pairs, to provide some estimate of the uncertainty on our RMS estimates due to the random shuffling (we could probably turn this into a more formal estimate somehow, but I'm not going to bother with that at the moment).
# While the SRD specifies that we should just compute the RMS directly, we haven't limited our sample to nonvariable stars as carefully as the SRD specifies, so using a more robust estimator like IQR will allow us to reject some outliers. It is also less sensitive some realistic sources of scatter the metric should include, however, such as bad zero points.

def computeWidths(diffs):
    rmsSigma = np.mean(diffs**2)**0.5
    iqrSigma = np.subtract.reduce(np.percentile(diffs, [75, 25])) / (scipy.stats.norm.ppf(0.75)*2)
    return rmsSigma, iqrSigma


def analyzeData(allMatches):
    """Calculate summary statistics for each star.

    @param[in] allMatches  -- afw.table.GroupView object with matches.

    Return a pipeBase.Struct with mag, dist, and number of matches.
    """

    # Filter down to matches with at least 2 sources and good flags
    flagKeys = [allMatches.schema.find("base_PixelFlags_flag_%s" % flag).key
                for flag in ("saturated", "cr", "bad", "edge")]
    nMatchesRequired = 2

    psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
#    apMagKey = allMatches.schema.find("base_CircularApertureFlux_12_0_mag").key
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

    # Filter further to a limited range in magnitude and extendedness to select bright stars (plotted below). The upturn at the bright end is due to the brighter-fatter effect on the sensors, but shouldn't matter for this test because it will affect all visits in approximately the same way (since they all have the same exposure time).
    safeMinMag = 16.5
#    safeMaxMag = 18.0
    safeMaxMag = 21.0
    safeMaxExtended = 1.0
    def safeFilter(cat):
        psfMag = np.mean(cat.get(psfMagKey))
        extended = np.max(cat.get(extendedKey))
        return psfMag >= safeMinMag and extended < safeMaxExtended

    safeMatches = goodMatches.where(safeFilter)

#    SUMMARY_STATISTICS = False
    SUMMARY_STATISTICS = True
    if SUMMARY_STATISTICS:
        # Pass field=psfMagKey so np.mean just gets that as its input
        goodPsfMag = goodMatches.aggregate(np.mean, field=psfMagKey)  # mag
        goodPsfMagRms = goodMatches.aggregate(np.std, field=psfMagKey)  # mag
        # positionRms knows how to query a group so we give it the whole thing
        #   by going with the default `field=None`.
        dist = goodMatches.aggregate(positionRms)
    else:
        goodPsfMag = goodMatches.apply(lambda x: x, field=psfMagKey)
        dist = goodMatches.apply(positionDiff)

    rmsPA1 = []
    iqrPA1 = []
    for i in range(50):
#        diffs = safeMatches.aggregate(getRandomDiff, field=apMagKey)
        diffs = safeMatches.aggregate(getRandomDiff, field=psfMagKey)
        rmsSigma, iqrSigma = computeWidths(diffs)
        rmsPA1.append(rmsSigma)
        iqrPA1.append(iqrSigma)

    rmsPA1 = np.array(rmsPA1)
    iqrPA1 = np.array(iqrPA1)
    print("PA1(RMS)=%4.2f+-%4.2f" % (rmsPA1.mean(), rmsPA1.std()))
    print("PA1(IQR)=%4.2f+-%4.2f" % (iqrPA1.mean(), iqrPA1.std()))

    info_struct = pipeBase.Struct(
        mag = goodPsfMag,
        mmagrms = 1000*goodPsfMagRms,  # mag -> mmag
        dist = dist,
        match = len(dist)
    )

    return info_struct, safeMatches


def plot_medians(ax, x1, x2, x1_color='blue', x2_color='red'):
    ax.axhline(x1, color='white', linewidth=4)
    ax.axhline(x2, color='white', linewidth=4)
    ax.axhline(x1, color=x1_color, linewidth=3)
    ax.axhline(x2, color=x2_color, linewidth=3)


def plotAstrometry(mag, mmagrms, dist, match, good_mag_limit=19.5):
    """Plot angular distance between matched sources from different exposures.

    @param[in] mag    Magnitude.  List or numpy.array.
    @param[in] mmagrms    Magnitude RMS.  List or numpy.array.
    @param[in] dist   Separation from reference.  List of numpy.array
    @param[in] match  Number of stars matched.  Integer.
    """

    bright, = np.where(np.asarray(mag) < good_mag_limit)

    dist_median = np.median(dist) 
    bright_dist_median = np.median(np.asarray(dist)[bright])

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(18, 12))

    ax[0].hist(dist, bins=100, color='blue',
               histtype='stepfilled', orientation='horizontal')
    ax[0].hist(np.asarray(dist)[bright], bins=100, color='red',
               histtype='stepfilled', orientation='horizontal',
               label='mag < %.1f' % good_mag_limit)

    ax[0].set_ylim([0., 500.])
    ax[0].set_ylabel("Distance in mas")
    ax[0].set_title("Median : %.1f, %.1f mas" % 
                       (bright_dist_median, dist_median),
                       x=0.55, y=0.88)
    plot_medians(ax[0], dist_median, bright_dist_median)

    ax[1].scatter(mag, dist, s=10, color='blue', label='All')
    ax[1].scatter(np.asarray(mag)[bright], np.asarray(dist)[bright], s=10, 
                  color='red', 
                  label='mag < %.1f' % good_mag_limit)
    ax[1].set_xlabel("Magnitude")
    ax[1].set_ylabel("Distance in mas")
    ax[1].set_xlim([17, 24])
    ax[1].set_ylim([0., 500.])
    ax[1].set_title("# of matches : %d, %d" % (len(bright), match))
    ax[1].legend(loc='upper left')
    plot_medians(ax[1], dist_median, bright_dist_median)

    plt.suptitle("Astrometry Check", fontsize=30)
    plotPath = "check_astrometry.png"
    plt.savefig(plotPath, format="png")


def checkAstrometry(mag, mmagrms, dist, match,
                    good_mag_limit=19.5,
                    medianRef=100, matchRef=500):
    """Print out the astrometric scatter for all stars, and for good stars.
    @param[in] mag    Magnitude.  List or numpy.array.
    @param[in] mmagrms    Magnitude RMS.  List or numpy.array.
    @param[in] dist   Separation from reference.  List of numpy.array
    @param[in] match  Number of stars matched.  Integer.

    @param medianRef  Median reference astrometric scatter in milliarcseconds.
    @param matchRef   Should match at least matchRef stars.

    Return the astrometric scatter (RMS, milliarcsec) for all good stars.

    Notes:
       The scatter and match defaults are appropriate to SDSS are stored here.
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
    @param[in] mag    Magnitude.  List or numpy.array.
    @param[in] mmagrms    Magnitude RMS.  List or numpy.array.
    @param[in] dist   Separation from reference.  List of numpy.array
    @param[in] match  Number of stars matched.  Integer.

    @param medianRef  Median reference photometric scatter in millimagnitudes.
    @param matchRef   Should match at least matchRef stars.

    Return the photometry scatter (RMS, millimag) for all good stars.

    Notes:
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

def plotPhotometryRms(mag, mmagrms, dist, match, good_mag_limit=19.5):
    """Plot photometric RMS for matched sources.

    @param[in] mag    Magnitude.  List or numpy.array.
    @param[in] mmagrms    Magnitude RMS.  List or numpy.array.
    @param[in] dist   Separation from reference.  List of numpy.array
    @param[in] match  Number of stars matched.  Integer.
    """

    bright, = np.where(np.asarray(mag) < good_mag_limit)

    mmagrms_median = np.median(mmagrms) 
    bright_mmagrms_median = np.median(np.asarray(mmagrms)[bright])

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(18, 12))
    ax[0].hist(mmagrms, bins=100, range=(0, 500), color='blue', label='All',
                  histtype='stepfilled', orientation='horizontal')
    ax[0].hist(np.asarray(mmagrms)[bright], bins=100, range=(0, 500), color='red', 
                  label='mag < %.1f' % good_mag_limit,
                  histtype='stepfilled', orientation='horizontal')
    ax[0].set_ylim([0, 500])
    ax[0].set_ylabel("RMS in mmag")
    ax[0].set_title("Median : %.1f, %.1f mmag" % 
                    (bright_mmagrms_median, mmagrms_median),
                    x=0.55, y=0.88)
    plot_medians(ax[0], mmagrms_median, bright_mmagrms_median)

    ax[1].scatter(mag, mmagrms, s=10, color='blue', label='All')
    ax[1].scatter(np.asarray(mag)[bright], np.asarray(mmagrms)[bright], 
                     s=10, color='red', 
                     label='mag < %.1f' % good_mag_limit)

    ax[1].set_xlabel("Magnitude")
    ax[1].set_ylabel("RMS [mmag]")
    ax[1].set_xlim([17, 24])
    ax[1].set_ylim([0, 500])
    ax[1].set_title("# of matches : %d, %d" % (len(bright), match))
    ax[1].legend(loc='upper left')
    plot_medians(ax[1], mmagrms_median, bright_mmagrms_median)

    plt.suptitle("Photometry Check", fontsize=30)
    plotPath = "check_photometry.png"
    plt.savefig(plotPath, format="png")


# To validate these width estimates, we can plot a single random realization (re-evaluate the cell or call the function again to get a new one).
def plotPA1(gv, psfMagKey):
#    diffs = gv.aggregate(getRandomDiff, field=apMagKey)
#    means = gv.aggregate(np.mean, field=apMagKey)
    diffs = gv.aggregate(getRandomDiff, field=psfMagKey)
    means = gv.aggregate(np.mean, field=psfMagKey)
    rmsPA1, iqrPA1 = computeWidths(diffs)
    fig = plt.figure(figsize=(18,12))
    ax1 = fig.add_subplot(1,2,1)
    ax1.scatter(means, diffs, s=8, linewidth=0, alpha=0.4)
    ax1.axhline(rmsPA1, color='r')
    ax1.axhline(-rmsPA1, color='r')
    ax1.axhline(iqrPA1, color='g')
    ax1.axhline(-iqrPA1, color='g')
    ax2 = fig.add_subplot(1,2,2, sharey=ax1)
    ax2.hist(diffs, bins=50, orientation='horizontal', normed=True, alpha=0.5)
    yv = np.linspace(-100, 100, 100)
    ax2.plot(scipy.stats.norm.pdf(yv, scale=rmsPA1), yv, 'r-', label="PA1(RMS)=%4.2f mmag" % rmsPA1)
    ax2.plot(scipy.stats.norm.pdf(yv, scale=iqrPA1), yv, 'g-', label="PA1(IQR)=%4.2f mmag" % iqrPA1)
    ax2.set_ylim(-100, 100)
    ax2.legend()
#    ax1.set_ylabel(u"12-pixel aperture magnitude diff (mmag)")
#    ax1.set_xlabel(u"12-pixel aperture magnitude")
    ax1.set_xlabel("psf aperture magnitude")
    ax1.set_ylabel("psf magnitude diff (mmag)")
    for label in ax2.get_yticklabels(): label.set_visible(False)

    plt.savefig("PA1.png")


# The PF1/PA2 puts a limit on the fraction of outliers in the above plot. Below, we compute the values of PA2 for the minimum, design, and stretch specification values of PF1 in the SRD.
def printPA2(gv, psfMagKey):
#    diffs = gv.aggregate(getRandomDiff, field=apMagKey)
    diffs = gv.aggregate(getRandomDiff, field=psfMagKey)
    minPA2, designPA2, stretchPA2 = np.percentile(np.abs(diffs), [80, 90, 95])
    print("minimum: PF1=20%% of diffs more than PA2=%4.2f mmag (target is PA2 < 15 mmag)" % minPA2)
    print("design: PF1=10%% of diffs more than PA2=%4.2f mmag (target is PA2 < 15 mmag)" % designPA2)
    print("stretch: PF1=5%% of diffs more than PA2=%4.2f mmag (target is PA2 < 10 mmag)" % stretchPA2)

####
def run(repo, visitDataIds, good_mag_limit, 
        medianAstromscatterRef=25, medianPhotoscatterRef=25, matchRef=500):
    """Main executable.
    """

    allMatches = loadAndMatchData(repo, visitDataIds)
    struct, safeMatches = analyzeData(allMatches)
    magavg = struct.mag
    mmagrms = struct.mmagrms
    dist = struct.dist
    match = struct.match

    checkAstrometry(magavg, mmagrms, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianAstromscatterRef, matchRef=matchRef)
    checkPhotometry(magavg, mmagrms, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianPhotoscatterRef, matchRef=matchRef)
    plotAstrometry(magavg, mmagrms, dist, match, good_mag_limit=good_mag_limit)
    plotPhotometryRms(magavg, mmagrms, dist, match, good_mag_limit=good_mag_limit)
#    plotPhotometryRms(magavg, delta_mag, dist, match, good_mag_limit=good_mag_limit)

    psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
    plotPA1(safeMatches, psfMagKey)
    printPA2(safeMatches, psfMagKey)



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

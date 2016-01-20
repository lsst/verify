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

from __future__ import print_function

import os.path
import sys

import matplotlib.pylab as plt
import numpy as np

import lsst.daf.persistence as dafPersist
import lsst.pipe.base as pipeBase
import lsst.afw.table as afwTable
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage


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


def isExtended(source, extRefKey, extendedThreshold=1.0):
    return source.get(extRefKey) >= extendedThreshold


def loadAndMatchData(repo, visitDataIds, refDataIds,
                     matchRadius=afwGeom.Angle(1, afwGeom.arcseconds)):
    """Load data from specific visit.  Match with reference.

    @param repo  The repository.  This is generally the directory on disk
                    that contains the repository and mapper.
    @param visitDataIds   Butler Data ID of Image catalogs to compare to reference.
           List of Lists.
           Should have dimensions of (N, len(refDataId));
           for a series of N visits.
    @param refDataIds       Butler Data ID of reference catalog.
           The actual pixel image is also needed for now.  List.

    @param matchRadius    Radius for matching.  afwGeom.Angle().

    Return a pipeBase.Struct with mag, dist, and number of matches.
    """

    flags = ["base_PixelFlags_flag_saturated", "base_PixelFlags_flag_cr", "base_PixelFlags_flag_interpolated",
             "base_PsfFlux_flag_edge"]

    # setup butler
    butler = dafPersist.Butler(repo)

    # retrieve the schema of the source catalog and extend it in order to add a field to record the ccd number
    ccdKeyName = getCcdKeyName(refDataIds[0])

    oldSrc = butler.get('src', refDataIds[0], immediate=True)
    oldSchema = oldSrc.getSchema()
    mapper = afwTable.SchemaMapper(oldSchema)
    mapper.addMinimalSchema(oldSchema)
    mapper.addOutputField(afwTable.Field[int](ccdKeyName, "CCD number"))
    newSchema = mapper.getOutputSchema()

    # create the new extented source catalog
    srcRef = afwTable.SourceCatalog(newSchema)

    for rId in refDataIds:
        oldSrc = butler.get('src', rId, immediate=True)
        print(len(oldSrc), "sources in ccd:", rId[ccdKeyName])

        # create temporary catalog
        tmpCat = afwTable.SourceCatalog(srcRef.table)
        tmpCat.extend(oldSrc, mapper=mapper)
        # fill in the ccd information in numpy mode in order to be efficient
        tmpCat[ccdKeyName][:] = rId[ccdKeyName]
        # add on the temporary catalog to the extended source catalog
        srcRef.extend(tmpCat, deep=False)

    print(len(srcRef), "total sources in reference visit.")

    mag = []
    dist = []
    matchNum = []
    # Calibration for each 'ccd' in the reference data Id list.
    # Here ccdKeyName values must be unique.
    # This is why we need the calibrated images for the ref source catalogs.
    calib = {rId[ccdKeyName]: afwImage.Calib(butler.get("calexp_md", rId, immediate=True))
             for rId in refDataIds}

    for v_set in visitDataIds:
        srcVis = butler.get('src', v_set[0], immediate=True)
        for vId in v_set[1:]:
            srcVis.extend(butler.get('src', vId, immediate=True), False)
            print(len(srcVis), "sources in ccd: ", vId[ccdKeyName])

        match = afwTable.matchRaDec(srcRef, srcVis, matchRadius)

        matchNum.append(len(match))
        print("Visits :", v_set, matchNum[-1], "matches found")

        schemaRef = srcRef.getSchema()
        schemaVis = srcVis.getSchema()
        extRefKey = schemaRef["base_ClassificationExtendedness_value"].asKey()
        extVisKey = schemaVis["base_ClassificationExtendedness_value"].asKey()
        flagKeysRef = [schemaRef[fl].asKey() for fl in flags]
        flagKeysVis = [schemaVis[fl].asKey() for fl in flags]

        for m in match:
            mRef = m.first
            mVis = m.second

            for fl in flagKeysRef:
                if mRef.get(fl):
                    continue
            for fl in flagKeysVis:
                if mVis.get(fl):
                    continue

            # Keep only decent star-like objects
            if isExtended(mRef, extRefKey) or isExtended(mVis, extVisKey):
                continue

            # Skip sources with non-positive flux in reference
            if mRef.get('base_PsfFlux_flux') <= 0:
                continue

            ang = afwGeom.radToMas(m.distance)

            # retrieve the CCD corresponding to the reference source
            ccdRef = mRef.get(ccdKeyName)
            refMag = calib[ccdRef].getMagnitude(mRef.get('base_PsfFlux_flux'))

            mag.append(refMag)
            dist.append(ang)

    # 2016-01-14 MWV <wmwv@pitt.edu>:
    # Need to re-think tracking of MatchNum
    # Presently, all of the magnitudes and distances are just stored
    # in one 1D array that serializes all visits.
    # What should matchNum be?
    # For now, I'm fixing to the number of matches in the first visit.

    return pipeBase.Struct(
        mag=mag,
        dist=dist,
        match=sum(matchNum)
    )


def plotAstrometry(mag, dist, match, good_mag_limit=19.5):
    """Plot angular distance between matched sources from different exposures."""

    plt.rcParams['axes.linewidth'] = 2
    plt.rcParams['mathtext.default'] = 'regular'

    fig, ax = plt.subplots(ncols=2, nrows=3, figsize=(18, 22))
    ax[0][0].hist(dist, bins=80)
    ax[0][1].scatter(mag, dist, s=10, color='b')
    ax[0][0].set_xlim([0., 900.])
    ax[0][0].set_xlabel("Distance in mas", fontsize=20)
    ax[0][0].tick_params(labelsize=20)
    ax[0][0].set_title("Median : %.1f mas" % (np.median(dist)), fontsize=20, x=0.6, y=0.88)
    ax[0][1].set_xlabel("Magnitude", fontsize=20)
    ax[0][1].set_ylabel("Distance in mas", fontsize=20)
    ax[0][1].set_ylim([0., 900.])
    ax[0][1].tick_params(labelsize=20)
    ax[0][1].set_title("Number of matches : %d" % match, fontsize=20)

    ax[1][0].hist(dist, bins=150)
    ax[1][0].set_xlim([0., 400.])
    ax[1][1].scatter(mag, dist, s=10, color='b')
    ax[1][1].set_ylim([0., 400.])
    ax[1][0].set_xlabel("Distance in mas", fontsize=20)
    ax[1][1].set_xlabel("Magnitude", fontsize=20)
    ax[1][1].set_ylabel("Distance in mas", fontsize=20)
    ax[1][0].tick_params(labelsize=20)
    ax[1][1].tick_params(labelsize=20)

    idxs = np.where(np.asarray(mag) < good_mag_limit)

    ax[2][0].hist(np.asarray(dist)[idxs], bins=100)
    ax[2][0].set_xlabel("Distance in mas - mag < %.1f" % good_mag_limit, fontsize=20)
    ax[2][0].set_xlim([0, 200])
    ax[2][0].set_title("Median (mag < %.1f) : %.1f mas" %
                       (good_mag_limit, np.median(np.asarray(dist)[idxs])),
                       fontsize=20, x=0.6, y=0.88)
    ax[2][1].scatter(np.asarray(mag)[idxs], np.asarray(dist)[idxs], s=10, color='b')
    ax[2][1].set_xlabel("Magnitude", fontsize=20)
    ax[2][1].set_ylabel("Distance in mas - mag < %.1f" % good_mag_limit, fontsize=20)
    ax[2][1].set_ylim([0., 200.])
    ax[2][0].tick_params(labelsize=20)
    ax[2][1].tick_params(labelsize=20)

    plt.suptitle("Astrometry Check", fontsize=30)
    plotPath = "check_astrometry.png"
    plt.savefig(plotPath, format="png")


def checkAstrometry(mag, dist, match,
                    good_mag_limit=19.5,
                    medianRef=100, matchRef=500):
    """Print out the astrometric scatter for all stars, and for good stars.

    @param medianRef  Median reference astrometric scatter in arcseconds.
    @param matchRef   Should match at least matchRef stars.

    Return the astrometric scatter (RMS, arcsec) for all good stars.

    Notes:
       The scatter and match defaults are appropriate to SDSS are stored here.
    For SDSS, stars with mag < 19.5 should be completely well measured.
    """

    print("Median value of the astrometric scatter - all magnitudes:",
          np.median(dist), "mas")

    idxs = np.where(np.asarray(mag) < good_mag_limit)
    astromScatter = np.median(np.asarray(dist)[idxs])
    print("Astrometric scatter (median) - mag < %.1f : %.1f %s" %
          (good_mag_limit, astromScatter, "mas"))

    if astromScatter > medianRef:
        print("Median astrometric scatter %.1f %s is larger than reference : %.1f %s " %
              (astromScatter, "mas", medianRef, "mas"))
    if match < matchRef:
        print("Number of matched sources %d is too small (shoud be > %d)" % (match, matchRef))

    return astromScatter


def run(repo, visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef):
    """Main executable.
    """

    struct = loadAndMatchData(repo, visitDataIds, refDataIds)
    mag = struct.mag
    dist = struct.dist
    match = struct.match
    checkAstrometry(mag, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianRef, matchRef=matchRef)
    plotAstrometry(mag, dist, match, good_mag_limit=good_mag_limit)


def defaultData(repo):
    # List of visits to be considered
    visits = [176846, 176850]

    # Reference visit ('visits' will be compared to this one)
    ref = 176837

    # List of CCD to be considered (source catalogs will be concateneted)
    ccd = [10]  # , 12, 14, 18]
    filter = 'z'

    # Reference values for the median astrometric scatter and the number of matches
    good_mag_limit = 21
    medianRef = 25
    matchRef = 5600

    visitDataIds = [{'visit': v, 'filter': filter, 'ccdnum': c} for v in visits
                    for c in ccd]
    refDataIds = [{'visit': ref, 'filter': filter, 'ccdnum': c} for c in ccd]

    return visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef


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

    visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef = defaultData(repo)
    run(repo, visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef)

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

from __future__ import print_function, absolute_import

import numpy as np

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.afw.table import SourceCatalog, SchemaMapper, Field
from lsst.afw.table import MultiMatch, SimpleRecord, GroupView
import lsst.daf.persistence as dafPersist
import lsst.pipe.base as pipeBase

from .base import ValidateErrorNoStars
from .calcSrd import calcAM1, calcAM2, calcAM3, calcPA1, calcPA2
from .check import checkAstrometry, checkPhotometry, positionRms
from .plot import plotAstrometry, plotPhotometry, plotPA1, plotAMx
from .print import printPA1, printPA2, printAMx
from .util import getCcdKeyName, repoNameToPrefix, calcOrNone
from .io import saveKpmToJson

from lsst.obs.cfht import MegacamMapper

mapper = MegacamMapper(root=".") # Annoying that we have to do this
def objIdToCcdId(objId):
    objId = np.array(objId, dtype='int64')
    nBitsId = mapper.bypass_ccdExposureId_bits(None, None, None, None)
    obj = np.bitwise_and(objId, nBitsId - 1)
    objId >>= nBitsId

    visit = objId // 36
    ccd = objId % 36

    return visit, ccd, obj

def loadAndMatchData(repo, visitDataIds,
                     matchRadius=afwGeom.Angle(1, afwGeom.arcseconds)):
    """Load data from specific visit.  Match with reference.

    Parameters
    ----------
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

    # 2016-02-08 MWV:
    # I feel like I could be doing something more efficient with
    # something along the lines of the following:
    #    dataRefs = [dafPersist.ButlerDataRef(butler, vId) for vId in visitDataIds]

    ccdKeyName = getCcdKeyName(visitDataIds[0])

    schema = butler.get(dataset + "_schema", immediate=True).schema
    mapper = SchemaMapper(schema)
    mapper.addMinimalSchema(schema)
    mapper.addOutputField(Field[float]('base_PsfFlux_mag', "PSF magnitude"))
    mapper.addOutputField(Field[float]('base_PsfFlux_magerr', "PSF magnitude uncertainty"))
    newSchema = mapper.getOutputSchema()

    # Create an object that can match multiple catalogs with the same schema
    mmatch = MultiMatch(newSchema,
                        dataIdFormat={'visit': int, ccdKeyName: int},
                        radius=matchRadius,
                        RecordClass=SimpleRecord)

    # create the new extented source catalog
    srcVis = SourceCatalog(newSchema)

    for vId in visitDataIds:
        calib = afwImage.Calib(butler.get("calexp_md", vId, immediate=True))
        calib.setThrowOnNegativeFlux(False)
        oldSrc = butler.get('src', vId, immediate=True)
        print(len(oldSrc), "sources in ccd %s  visit %s" % (vId[ccdKeyName], vId["visit"]))

        # create temporary catalog
        tmpCat = SourceCatalog(SourceCatalog(newSchema).table)
        tmpCat.extend(oldSrc, mapper=mapper)
        (tmpCat['base_PsfFlux_mag'][:], tmpCat['base_PsfFlux_magerr'][:]) = \
         calib.getMagnitude(tmpCat['base_PsfFlux_flux'],
                            tmpCat['base_PsfFlux_fluxSigma'])
        srcVis.extend(tmpCat, False)
        mmatch.add(catalog=tmpCat, dataId=vId)

    # Complete the match, returning a catalog that includes
    # all matched sources with object IDs that can be used to group them.
    matchCat = mmatch.finish()

    # Create a mapping object that allows the matches to be manipulated
    # as a mapping of object ID to catalog of sources.
    allMatches = GroupView.build(matchCat)

    return allMatches


def analyzeData(allMatches, good_mag_limit=19.5):
    """Calculate summary statistics for each star.

    Parameters
    ----------
    allMatches : afw.table.GroupView
        GroupView object with matches.
    good_mag_limit : float, optional
        Minimum average brightness (in magnitudes) for a star to be considered.

    Returns
    -------
    pipeBase.Struct containing:
    - mag: mean PSF magnitude for good matches
    - magerr: median of PSF magnitude for good matches
    - magrms: standard deviation of PSF magnitude for good matches
    - dist: RMS RA/Dec separation, in milliarcsecond
    - goodMatches: all good matches, as an afw.table.GroupView;
        good matches contain sources that have a finite (non-nan) PSF magnitude
        and do not have flags set for bad, cosmic ray, edge or saturated
    - safeMatches: safe matches, as an afw.table.GroupView;
        safe matches are good matches that are sufficiently bright and sufficiently compact
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
    goodPsfMag = goodMatches.aggregate(np.mean, field=psfMagKey)  # mag
    goodPsfMagRms = goodMatches.aggregate(np.std, field=psfMagKey)  # mag
    goodPsfMagErr = goodMatches.aggregate(np.median, field=psfMagErrKey)
    # positionRms knows how to query a group so we give it the whole thing
    #   by going with the default `field=None`.
    dist = goodMatches.aggregate(positionRms)

    def badBrightFilter(cat):
        return positionRms(cat) > 150 and np.mean(cat[psfMagKey]) < 21
    brightFar = goodMatches.where(badBrightFilter)
    print("Found %s bad, bright matches" % (len(brightFar,)))
    print("visit0 ccd0 x0 y0 mag0  visit1 ccd1 x1 y1 mag1  sep")
    for cat in brightFar.groups:
        src0 = cat[0]
        objId0 = src0.getId()
        x0 = src0.get("base_SdssCentroid_x")
        y0 = src0.get("base_SdssCentroid_y")
        mag0 = src0.get("base_PsfFlux_mag")
        visit0, ccd0, obj0 = objIdToCcdId(objId0)

        src1 = cat[1]
        objId1 = src1.getId()
        x1 = src1.get("base_SdssCentroid_x")
        y1 = src1.get("base_SdssCentroid_y")
        mag1 = src1.get("base_PsfFlux_mag")
        visit1, ccd1, obj1 = objIdToCcdId(objId1)

        sep = positionRms(cat)

        print("%s %s %0.2f %0.2f %0.2f   %s %s %0.2f %0.2f %0.2f   %0.2f" % (
            visit0, ccd0, x0, y0, mag0,  visit1, ccd1, x1, y1, mag1,  sep))

    return pipeBase.Struct(
        mag = goodPsfMag,
        magerr = goodPsfMagErr,
        magrms = goodPsfMagRms,
        dist = dist,
        goodMatches = goodMatches,
        safeMatches = safeMatches,
    )


####
def run(repo, visitDataIds, good_mag_limit=21.0,
        medianAstromscatterRef=25, medianPhotoscatterRef=25, matchRef=500,
        makePrint=True, makePlot=True, makeJson=True,
        outputPrefix=None):
    """Main executable.

    Plot files and JSON files are generated in the local directory
        prefixed with the repository name (where '_' replace path separators),
    unless overriden by specifying `outputPrefix`.
    E.g., Analyzing a repository "CFHT/output"
        will result in filenames that start with "CFHT_output_".

    Parameters
    ----------
    repo : string
        The repository.  This is generally the directory on disk
        that contains the repository and mapper.
    visitDataIds : list of dict
        List of `butler` data IDs of Image catalogs to compare to reference.
        The `calexp` cpixel image is needed for the photometric calibration.
    good_mag_limit : float, optional
        Minimum average brightness (in magnitudes) for a star to be considered.
    medianAstromscatterRef : float, optional
        Expected astrometric RMS [mas] across visits.
    medianPhotoscatterRef : float, optional
        Expected photometric RMS [mmag] across visits.
    matchRef : int, optional
        Expectation of the number of stars that should be matched across visits.
    makePrint : bool, optional
        Print calculated quantities (to stdout).
    makePlot : bool, optional
        Create plots for metrics.  Saved to current working directory.
    makeJson : bool, optional
        Create JSON output file for metrics.  Saved to current working directory.
    outputPrefix : str
        Specify the beginning filename for output files.

    """

    if outputPrefix is None:
        outputPrefix = repoNameToPrefix(repo)

    allMatches = loadAndMatchData(repo, visitDataIds)
    struct = analyzeData(allMatches, good_mag_limit)
    magavg = struct.mag
    magerr = struct.magerr
    magrms = struct.magrms
    dist = struct.dist
    match = len(struct.goodMatches)
    safeMatches = struct.safeMatches

    mmagerr = 1000*magerr
    mmagrms = 1000*magrms

    checkAstrometry(magavg, mmagrms, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianAstromscatterRef, matchRef=matchRef)
    checkPhotometry(magavg, mmagrms, dist, match,
                    good_mag_limit=good_mag_limit,
                    medianRef=medianPhotoscatterRef, matchRef=matchRef)
    if makePlot:
        plotAstrometry(magavg, mmagerr, mmagrms, dist, match,
                       good_mag_limit=good_mag_limit, outputPrefix=outputPrefix)
        plotPhotometry(magavg, mmagerr, mmagrms, dist, match,
                       good_mag_limit=good_mag_limit, outputPrefix=outputPrefix)

    magKey = allMatches.schema.find("base_PsfFlux_mag").key

    AM1, AM2, AM3 = [calcOrNone(func, safeMatches, ValidateErrorNoStars)
                     for func in (calcAM1, calcAM2, calcAM3)]
    PA1, PA2 = [func(safeMatches, magKey) for func in (calcPA1, calcPA2)]

    if makePrint:
        printPA1(PA1)
        printPA2(PA2)
        for metric in (AM1, AM2, AM3):
            if metric:
                printAMx(metric)

    if makePlot:
        plotPA1(PA1, outputPrefix=outputPrefix)
        for metric in (AM1, AM2, AM3):
            if metric:
                plotAMx(metric, outputPrefix=outputPrefix)

    if makeJson:
        for metric in (AM1, AM2, AM3, PA1, PA2):
            if metric:
                outfile = outputPrefix + "%s.json" % metric.name
                saveKpmToJson(metric, outfile)

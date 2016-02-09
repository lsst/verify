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

from __future__ import print_function, absolute_import

import numpy as np

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.afw.table import SourceCatalog, SchemaMapper, Field
from lsst.afw.table import MultiMatch, SimpleRecord, GroupView
import lsst.daf.persistence as dafPersist
import lsst.pipe.base as pipeBase

from .calcSrd import calcAM1, calcAM2
from .check import checkAstrometry, checkPhotometry, positionRms
from .print import printPA1, printPA2, printAM1, printAM2
from .plot import plotAstrometry, plotPhotometry, plotPA1, plotAM1, plotAM2
from .util import getCcdKeyName, repoNameToPrefix, loadDataIdsAndParameters, constructDataIds, loadRunList, constructRunList 
from .io import saveAmxToJson


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
        print(len(oldSrc), "sources in ccd: ", vId[ccdKeyName])

        # create temporary catalog
        tmpCat = SourceCatalog(SourceCatalog(newSchema).table)
        tmpCat.extend(oldSrc, mapper=mapper)
        (tmpCat['base_PsfFlux_mag'][:], tmpCat['base_PsfFlux_magerr'][:]) = \
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
    goodPsfMag = goodMatches.aggregate(np.mean, field=psfMagKey)  # mag
    goodPsfMagRms = goodMatches.aggregate(np.std, field=psfMagKey)  # mag
    goodPsfMagErr = goodMatches.aggregate(np.median, field=psfMagErrKey)
    # positionRms knows how to query a group so we give it the whole thing
    #   by going with the default `field=None`.
    dist = goodMatches.aggregate(positionRms)

    info_struct = pipeBase.Struct(
        mag=goodPsfMag,
        magerr=goodPsfMagErr,
        magrms=goodPsfMagRms,
        dist=dist,
        match=len(dist)
    )

    return info_struct, safeMatches


####
def run(repo, visitDataIds, good_mag_limit=21.0,
        medianAstromscatterRef=25, medianPhotoscatterRef=25, matchRef=500,
        makePrint=True, makePlot=True, makeJson=True,
        outputPrefix=None):
    """Main executable.

    Inputs
    ------
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

    Outputs
    -------
    Names of plot files or JSON file are generated based on repository name,  
    unless overriden by specifying `plotBase`.
    E.g., Analyzing a repository "CFHT/output"
        will result in filenames that start with "CFHT_output_".
    """

    if outputPrefix is None:
        outputPrefix = repoNameToPrefix(repo)

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
    if makePlot:
        plotAstrometry(magavg, mmagerr, mmagrms, dist, match,
                       good_mag_limit=good_mag_limit, plotBase=outputPrefix)
        plotPhotometry(magavg, mmagerr, mmagrms, dist, match,
                       good_mag_limit=good_mag_limit, plotBase=outputPrefix)

    magKey = allMatches.schema.find("base_PsfFlux_mag").key
    AM1 = calcAM1(safeMatches)
    AM2 = calcAM2(safeMatches)
    if makePrint:
        printPA1(safeMatches, magKey)
        printPA2(safeMatches, magKey)
        printAM1(AM1.AM1, AM1.AD1_annulus, AM1.magRange)
        printAM2(AM2.AM2, AM2.AD2_annulus, AM2.magRange)

    if makePlot:
        plotPA1(safeMatches, magKey, plotBase=outputPrefix)
        plotAM1(AM1.AM1, AM1.AD1_annulus, AM1.magRange, plotBase=outputPrefix)
        plotAM2(AM2.AM2, AM2.AD2_annulus, AM2.magRange, plotBase=outputPrefix)

    if makeJson:
        outfileAM1 = outputPrefix+"AM1.json"
        saveAmxToJson(AM1, outfileAM1)
        outfileAM2 = outputPrefix+"AM2.json"
        saveAmxToJson(AM2, outfileAM2)

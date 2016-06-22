# LSST Data Management System
# Copyright 2016 AURA/LSST.
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
from scipy.optimize import curve_fit

import numpy as np

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
import lsst.afw.image.utils as afwImageUtils
import lsst.daf.persistence as dafPersist
from lsst.afw.table import (SourceCatalog, SchemaMapper, Field,
                            MultiMatch, SimpleRecord, GroupView)
from lsst.afw.fits.fitsLib import FitsError

from .util import (getCcdKeyName, averageRaDecFromCat)
from .base import BlobBase, Datum


class MatchedMultiVisitDataset(BlobBase):
    """Container for matched star catalogs from multple visits, with filtering,
    summary statistics, and modelling.

    `MatchedMultiVisitDataset` instances are serializable to JSON.

    Parameters
    ----------
    repo : string
        The repository.  This is generally the directory on disk
        that contains the repository and mapper.
    dataIds : list of dict
        List of `butler` data IDs of Image catalogs to compare to reference.
        The `calexp` cpixel image is needed for the photometric calibration.
    matchRadius :  afwGeom.Angle(), optional
        Radius for matching. Default is 1 arcsecond.
    safeSnr : float, optional
        Minimum median SNR for a match to be considered "safe".
    verbose : bool, optional
        Output additional information on the analysis steps.

    Attributes
    ----------
    filterName
    mag
    magerr
    magrms
    snr
    dist
    goodMatches
        all good matches, as an afw.table.GroupView;
        good matches contain only objects whose detections all have

        1. a PSF Flux measurement with S/N > 1
        2. a finite (non-nan) PSF magnitude. This separate check is largely
           to reject failed zeropoints.
        3. and do not have flags set for bad, cosmic ray, edge or saturated

    safeMatches
        safe matches, as an afw.table.GroupView. Safe matches
        are good matches that are sufficiently bright and sufficiently
        compact.
    magKey
        Key for `"base_PsfFlux_mag"` in the `goodMatches` and `safeMatches`
        catalog tables.
    """
    def __init__(self, repo, dataIds, matchRadius=None, safeSnr=50.,
                 verbose=False):
        BlobBase.__init__(self)

        self.verbose = verbose
        if not matchRadius:
            matchRadius = afwGeom.Angle(1, afwGeom.arcseconds)

        # Extract single filter
        self._doc['filter_name'] = set([dId['filter']
                                        for dId in dataIds]).pop()

        # Match catalogs across visits
        self._matchedCatalog = self._loadAndMatchCatalogs(
            repo, dataIds, matchRadius)
        self.magKey = self._matchedCatalog.schema.find("base_PsfFlux_mag").key
        # Reduce catalogs into summary statistics.
        # These are the serialiable attributes of this class.
        self._reduceStars(self._matchedCatalog, safeSnr)

    @property
    def schema(self):
        return 'multi-visit-star-blob-v1.0.0'

    @property
    def filterName(self):
        """Name of the filter observations. All observations are taken with
        a single filter, by design. (`str`).
        """
        return self._doc['filter_name']

    @property
    def mag(self):
        """Mean PSF magnitude for good matches."""
        return self._doc['mag'].value

    @property
    def magerr(self):
        """Median of PSF magnitude for good matches."""
        return self._doc['mag_err'].value

    @property
    def magrms(self):
        """Standard deviation of PSF magnitude for good matches."""
        return self._doc['mag_rms'].value

    @property
    def snr(self):
        """Median PSF flux SNR for good matches."""
        return self._doc['snr'].value

    @property
    def dist(self):
        """RMS RA/Dec separation, in milliarcsecond."""
        return self._doc['dist'].value

    def _loadAndMatchCatalogs(self, repo, dataIds, matchRadius):
        """Load data from specific visit. Match with reference.

        Parameters
        ----------
        repo : string
            The repository.  This is generally the directory on disk
            that contains the repository and mapper.
        dataIds : list of dict
            List of `butler` data IDs of Image catalogs to compare to
            reference. The `calexp` cpixel image is needed for the photometric
            calibration.
        matchRadius :  afwGeom.Angle(), optional
            Radius for matching. Default is 1 arcsecond.

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
        #    dataRefs = [dafPersist.ButlerDataRef(butler, vId) for vId in dataIds]

        ccdKeyName = getCcdKeyName(dataIds[0])

        schema = butler.get(dataset + "_schema", immediate=True).schema
        mapper = SchemaMapper(schema)
        mapper.addMinimalSchema(schema)
        mapper.addOutputField(Field[float]('base_PsfFlux_snr',
                                           'PSF flux SNR'))
        mapper.addOutputField(Field[float]('base_PsfFlux_mag',
                                           'PSF magnitude'))
        mapper.addOutputField(Field[float]('base_PsfFlux_magerr',
                                           'PSF magnitude uncertainty'))
        newSchema = mapper.getOutputSchema()

        # Create an object that matches multiple catalogs with same schema
        mmatch = MultiMatch(newSchema,
                            dataIdFormat={'visit': int, ccdKeyName: int},
                            radius=matchRadius,
                            RecordClass=SimpleRecord)

        # create the new extented source catalog
        srcVis = SourceCatalog(newSchema)

        for vId in dataIds:
            try:
                calexpMetadata = butler.get("calexp_md", vId, immediate=True)
            except FitsError as fe:
                print(fe)
                print("Could not open calibrated image file for ", vId)
                print("Skipping %s " % repr(vId))
                continue
            except TypeError as te:
                # DECam images that haven't been properly reformatted
                # can trigger a TypeError because of a residual FITS header
                # LTV2 which is a float instead of the expected integer.
                # This generates an error of the form:
                #
                # lsst::pex::exceptions::TypeError: 'LTV2 has mismatched type'
                #
                # See, e.g., DM-2957 for details.
                print(te)
                print("Calibration image header information malformed.")
                print("Skipping %s " % repr(vId))
                continue

            calib = afwImage.Calib(calexpMetadata)

            oldSrc = butler.get('src', vId, immediate=True)
            print(len(oldSrc), "sources in ccd %s  visit %s" %
                  (vId[ccdKeyName], vId["visit"]))

            # create temporary catalog
            tmpCat = SourceCatalog(SourceCatalog(newSchema).table)
            tmpCat.extend(oldSrc, mapper=mapper)
            tmpCat['base_PsfFlux_snr'][:] = tmpCat['base_PsfFlux_flux'] \
                / tmpCat['base_PsfFlux_fluxSigma']
            with afwImageUtils.CalibNoThrow():
                _ = calib.getMagnitude(tmpCat['base_PsfFlux_flux'],
                                       tmpCat['base_PsfFlux_fluxSigma'])
                tmpCat['base_PsfFlux_mag'][:] = _[0]
                tmpCat['base_PsfFlux_magerr'][:] = _[1]

            srcVis.extend(tmpCat, False)
            mmatch.add(catalog=tmpCat, dataId=vId)

        # Complete the match, returning a catalog that includes
        # all matched sources with object IDs that can be used to group them.
        matchCat = mmatch.finish()

        # Create a mapping object that allows the matches to be manipulated
        # as a mapping of object ID to catalog of sources.
        allMatches = GroupView.build(matchCat)

        return allMatches

    def _reduceStars(self, allMatches, safeSnr=50.0):
        """Calculate summary statistics for each star. These are persisted
        as object attributes.

        Parameters
        ----------
        allMatches : afw.table.GroupView
            GroupView object with matches.
        safeSnr : float, optional
            Minimum median SNR for a match to be considered "safe".
        """
        # Filter down to matches with at least 2 sources and good flags
        flagKeys = [allMatches.schema.find("base_PixelFlags_flag_%s" % flag).key
                    for flag in ("saturated", "cr", "bad", "edge")]
        nMatchesRequired = 2

        psfSnrKey = allMatches.schema.find("base_PsfFlux_snr").key
        psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
        psfMagErrKey = allMatches.schema.find("base_PsfFlux_magerr").key
        extendedKey = allMatches.schema.find("base_ClassificationExtendedness_value").key

        def goodFilter(cat, goodSnr=3):
            if len(cat) < nMatchesRequired:
                return False
            for flagKey in flagKeys:
                if cat.get(flagKey).any():
                    return False
            if not np.isfinite(cat.get(psfMagKey)).all():
                return False
            psfSnr = np.median(cat.get(psfSnrKey))
            # Note that this also implicitly checks for psfSnr being non-nan.
            return psfSnr >= goodSnr

        goodMatches = allMatches.where(goodFilter)

        # Filter further to a limited range in S/N and extendedness
        # to select bright stars.
        safeMaxExtended = 1.0

        def safeFilter(cat):
            psfSnr = np.median(cat.get(psfSnrKey))
            extended = np.max(cat.get(extendedKey))
            return psfSnr >= safeSnr and extended < safeMaxExtended

        safeMatches = goodMatches.where(safeFilter)

        # Pass field=psfMagKey so np.mean just gets that as its input
        goodPsfSnr = goodMatches.aggregate(np.median, field=psfSnrKey)  # SNR
        goodPsfMag = goodMatches.aggregate(np.mean, field=psfMagKey)  # mag
        goodPsfMagRms = goodMatches.aggregate(np.std, field=psfMagKey)  # mag
        goodPsfMagErr = goodMatches.aggregate(np.median, field=psfMagErrKey)
        # positionRms knows how to query a group so we give it the whole thing
        # by going with the default `field=None`.
        dist = goodMatches.aggregate(positionRms)

        # Persist results in a serializable-form
        self._doc['mag'] = Datum(
            goodPsfMag,
            'mag',
            label='{band}'.format(band=self.filterName),
            description='Mean PSF magnitudes of stars over multiple visits')
        self._doc['mag_rms'] = Datum(
            goodPsfMagRms,
            'mag',
            label='RMS({band})'.format(band=self.filterName),
            description='RMS of PSF magnitudes over multiple visits')
        self._doc['mag_err'] = Datum(
            goodPsfMagErr,
            'mag',
            label='sigma({band})'.format(band=self.filterName),
            description='Median 1-sigma uncertainty of PSF magnitudes over '
                        'multiple visits')
        self._doc['snr'] = Datum(
            goodPsfSnr,
            None,
            label='SNR({band})'.format(band=self.filterName),
            description='Median signal-to-noise ratio of PSF magnitudes over '
                        'multiple visits')
        self._doc['dist'] = Datum(
            dist,
            'milliarcsecond',
            label='d',
            description='RMS of sky coordinates of stars over multiple visits')

        self.goodMatches = goodMatches
        self.safeMatches = safeMatches


class AnalyticPhotometryModel(BlobBase):
    """Serializable analytic photometry error model for multi-visit catalogs.

    Parameters
    ----------
    matchedMultiVisitDataset : `MatchedMultiVisitDataset`
        A dataset containing matched statistics for stars across multiple
        visits.
    brightSnr : float, optional
        Minimum SNR for a star to be considered "bright".
    medianRef : float, optional
        Median reference astrometric scatter in millimagnitudes
    matchRef : int, optional
        Should match at least matchRef stars.

    Attributes
    ----------
    sigmaSys
    gamma
    m5
    photRms

    Notes
    -----
    The scatter and match defaults are appropriate to SDSS are stored here.
    For SDSS, stars with mag < 19.5 should be completely well measured.
    This limit is a band-dependent statement most appropriate to r.
    """
    def __init__(self, matchedMultiVisitDataset, brightSnr=100, medianRef=100,
                 matchRef=500):
        BlobBase.__init__(self)

        self._doc['doc'] \
            = "Photometric uncertainty model from " \
              "http://arxiv.org/abs/0805.2366v4 (Eq 4, 5): " \
              "sigma_1^2 = sigma_sys^2 + sigma_rand^2, " \
              "sigma_rand^2 = (0.04 - gamma) * x + gamma * x^2 [mag^2] " \
              "where x = 10**(0.4*(m-m_5))"

        self._compute(
            matchedMultiVisitDataset.snr,
            matchedMultiVisitDataset.mag,
            matchedMultiVisitDataset.magerr * 1000.,
            matchedMultiVisitDataset.magrms * 1000.,
            matchedMultiVisitDataset.dist,
            brightSnr,
            medianRef,
            matchRef)

    @property
    def schema(self):
        return 'multi-visit-photometry-model-v1.0.0'

    @property
    def sigmaSys(self):
        return self._doc['sigmaSys'].value

    @property
    def gamma(self):
        return self._doc['gamma'].value

    @property
    def m5(self):
        return self._doc['m5'].value

    @property
    def photRms(self):
        return self._doc['phot_rms'].value

    def _compute(self, snr, mag, mmagErr, mmagrms, dist, match,
                 brightSnr=100,
                 medianRef=100, matchRef=500):
        bright = np.where(np.asarray(snr) > brightSnr)
        photScatter = np.median(np.asarray(mmagrms)[bright])
        print("Photometric scatter (median) - SNR > %.1f : %.1f %s" %
              (brightSnr, photScatter, "mmag"))

        fit_params = fitPhotErrModel(mag[bright], mmagErr[bright])

        if photScatter > medianRef:
            print('Median photometric scatter %.3f %s is larger than '
                  'reference : %.3f %s '
                  % (photScatter, "mmag", medianRef, "mag"))
        if match < matchRef:
            print("Number of matched sources %d is too small (shoud be > %d)"
                  % (match, matchRef))

        self._doc['bright_snr'] = Datum(
            brightSnr,
            '',
            label='Bright SNR',
            description='Threshold in SNR for bright sources used in this '
                        'model')
        self._doc['sigmaSys'] = Datum(
            fit_params['sigmaSys'],
            'mag',
            label='sigma(sys)',
            description='Systematic error floor')
        self._doc['gamma'] = Datum(
            fit_params['gamma'],
            None,
            label='gamma',
            description='Proxy for sky brightness and read noise')
        self._doc['m5'] = Datum(
            fit_params['m5'],
            'mag',
            label='m5',
            description='5-sigma depth')
        self._doc['phot_rms'] = Datum(
            photScatter,
            'mmag',
            label='RMS',
            description='RMS photometric scatter for good stars')


class AnalyticAstrometryModel(BlobBase):
    """Serializable model of astronometry errors across multiple visits.

    Parameters
    ----------
    matchedMultiVisitDataset : `MatchedMultiVisitDataset`
        A dataset containing matched statistics for stars across multiple
        visits.
    brightSnr : float, optional
        Minimum SNR for a star to be considered "bright".
    medianRef : float, optional
        Median reference astrometric scatter in millimagnitudes
    matchRef : int, optional
        Should match at least matchRef stars.

    Notes
    -----
    The scatter and match defaults are appropriate to SDSS are the defaults
      for `medianRef` and `matchRef`
    For SDSS, stars with mag < 19.5 should be completely well measured.
    """
    def __init__(self, matchedMultiVisitDataset, brightSnr=100,
                 medianRef=100, matchRef=500):
        BlobBase.__init__(self)

        self._doc['doc'] \
            = "Astrometric astrometry model: mas = C*theta/SNR + sigmaSys"

        self._compute(
            matchedMultiVisitDataset.snr,
            matchedMultiVisitDataset.dist,
            len(matchedMultiVisitDataset.goodMatches))

    @property
    def schema(self):
        return 'multi-visit-photometry-model-v1.0.0'

    def _compute(self, snr, dist, match,
                 brightSnr=100,
                 medianRef=100, matchRef=500):
        print('Median value of the astrometric scatter - all magnitudes: '
              '%.3f %s' % (np.median(dist), "mas"))

        bright = np.where(np.asarray(snr) > brightSnr)
        astromScatter = np.median(np.asarray(dist)[bright])
        print("Astrometric scatter (median) - snr > %.1f : %.1f %s" %
              (brightSnr, astromScatter, "mas"))

        fit_params = fitAstromErrModel(snr[bright], dist[bright])

        if astromScatter > medianRef:
            print('Median astrometric scatter %.1f %s is larger than '
                  'reference : %.1f %s ' %
                  (astromScatter, "mas", medianRef, "mas"))
        if match < matchRef:
            print("Number of matched sources %d is too small (shoud be > %d)" % (match, matchRef))

        self._doc['bright_snr'] = Datum(
            brightSnr,
            '',
            label='Bright SNR',
            description='Threshold in SNR for bright sources used in this '
                        'model')
        self._doc['C'] = Datum(
            fit_params['C'],
            None,
            label='C',
            description='Scaling factor')
        self._doc['theta'] = Datum(
            fit_params['theta'],
            'milliarcsecond',
            label='theta',
            description='Seeing')
        self._doc['sigmaSys'] = Datum(
            fit_params['sigmaSys'],
            'milliarcsecond',
            label='sigma(sys)',
            description='Systematic error floor')
        self._doc['astrom_rms'] = Datum(
            astromScatter,
            'milliarcsecond',
            label='RMS',
            description='Astrometric scatter (RMS) for good stars')


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


def expModel(x, a, b, norm):
    return a * np.exp(x/norm) + b


def magerrModel(x, a, b):
    return expModel(x, a, b, norm=5)


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

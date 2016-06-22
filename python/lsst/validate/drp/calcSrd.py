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

import numpy as np

import lsst.pipe.base as pipeBase

from .base import ValidateErrorNoStars
from .srdSpec import srdSpec, getAstrometricSpec
from .io import ParametersSerializerBase, MetricSerializer, DatumSerializer
from .utils import (
    getRandomDiffRmsInMas, computeWidths, radiansToMilliarcsec)


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

    PA1 = np.mean(iqrPA1)
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


class PA1ParamSerializer(ParametersSerializerBase):
    """Serialize parameters used by PA1 metric measurement."""

    def __init__(self, num_random_shuffles):
        # FIXME note that num_random_shuffles is hidden as a default param
        # of calcPA1. We need a better of exposing full provenance
        ParametersSerializerBase.__init__(self)
        self._doc['num_random_shuffles'] = num_random_shuffles

    @property
    def schema_id(self):
        return 'PA1-parameters-v1.0.0'


class PA1Serializer(MetricSerializer):
    """Serializer for PA1 metric definition."""
    def __init__(self):
        MetricSerializer.__init__(
            self,
            name='PA1',
            reference='LPM-17',
            description='Median RMS of visit-to-visit relative photometry.')


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


class PA2ParamSerializer(ParametersSerializerBase):
    """Serialize parameters used by PA1 metric measurement."""

    def __init__(self, num_random_shuffles=None, PF1=None):
        ParametersSerializerBase.__init__(self)
        assert isinstance(num_random_shuffles, int)
        assert isinstance(PF1, DatumSerializer)
        self._doc['num_random_shuffles'] = num_random_shuffles
        self._doc['PF1'] = PF1

    @property
    def schema_id(self):
        return 'PA2-parameters-v1.0.0'


class PA2Serializer(MetricSerializer):
    """Serializer for PA2 metric definition."""
    def __init__(self, spec_level):
        MetricSerializer.__init__(
            self,
            name='PA2',
            spec_level=spec_level,
            reference='LPM-17',
            description='Mags from mean relative photometric RMS that '
                        'encompasses PF1 of measurements.')


class PF1ParamSerializer(ParametersSerializerBase):
    """Serialize parameters used by PA1 metric measurement."""

    def __init__(self, PA2=None):
        ParametersSerializerBase.__init__(self)
        assert isinstance(PA2, DatumSerializer)
        self._doc['PA2'] = PA2

    @property
    def schema_id(self):
        return 'PF1-parameters-v1.0.0'


class PF1Serializer(MetricSerializer):
    """Serializer for PF1 metric definition."""
    def __init__(self, spec_level):
        MetricSerializer.__init__(
            self,
            name='PF1',
            spec_level=spec_level,
            reference='LPM-17',
            description='Fraction of measurements more than PA2')


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
            verbose=False):
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


class AMxParamSerializer(ParametersSerializerBase):
    """Serialize parameters used by AMx metric measurement."""

    def __init__(self, D=None, annulus=None, mag_range=None):
        ParametersSerializerBase.__init__(self)
        assert isinstance(D, DatumSerializer)
        assert isinstance(annulus, DatumSerializer)
        assert isinstance(mag_range, DatumSerializer)
        self._doc['D'] = D
        self._doc['annulus'] = annulus
        self._doc['mag_range'] = mag_range

    @property
    def schema_id(self):
        return 'AMx-parameters-v1.0.0'


class AMxSerializer(MetricSerializer):
    """Serializer for AMx metric definition."""
    def __init__(self, x):
        MetricSerializer.__init__(
            self,
            name='AM{0:d}'.format(int(x)),
            reference='LPM-17',
            description='Median RMS of the astrometric distance distribution '
                        'for stellar pairs with separation of D arcmin '
                        '(repeatability)')


class AFxParamSerializer(ParametersSerializerBase):
    """Serialize parameters used by AFx metric measurement."""

    def __init__(self, AMx=None, ADx=None,
                 D=None, annulus=None, mag_range=None):
        ParametersSerializerBase.__init__(self)
        assert isinstance(AMx, DatumSerializer)
        assert isinstance(ADx, DatumSerializer)
        assert isinstance(D, DatumSerializer)
        assert isinstance(annulus, DatumSerializer)
        assert isinstance(mag_range, DatumSerializer)
        self._doc['AMx'] = AMx
        self._doc['ADx'] = ADx
        self._doc['D'] = D
        self._doc['annulus'] = annulus
        self._doc['mag_range'] = mag_range

    @property
    def schema_id(self):
        return 'AFx-parameters-v1.0.0'


class AFxSerializer(MetricSerializer):
    """Serializer for AFx metric definition."""
    def __init__(self, x=None, level=None):
        MetricSerializer.__init__(
            self,
            name='AF{0:d}'.format(int(x)),
            spec_level=level,
            reference='LPM-17',
            description='Fraction of pairs that deviate by AD{0:d} '
                        'from median AM{0:d} ({1})'.format(x, level))

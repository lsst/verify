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

import lsst.pipe.base as pipeBase

from ..base import MeasurementBase, Metric, Datum, BlobBase
from ..util import getRandomDiffRmsInMas, computeWidths


class PA1Measurement(MeasurementBase):
    """Measurement of the PA1 metric: photometric repeatability of
    measurements across a set of observations.

    Parameters
    ----------
    matchedDataset : lsst.validate.drp.matchreduce.MatchedMultiVisitDataset
    bandpass : str
        Bandpass (filter name) used in this measurement (e.g., `'r'`)
    numRandomShuffles : int
        Number of times to draw random pairs from the different observations.
    verbose : bool, optional
        Output additional information on the analysis steps.
    job : :class:`lsst.validate.drp.base.Job`, optional
        If provided, the measurement will register itself with the Job
        object.
    linkedBlobs : list, optional
        A `list` of additional blobs (subclasses of BlobSerializerBase) that
        can provide additional context to the measurement, though aren't
        direct dependencies of the computation (e.g., `matchedDataset).

    Attributes
    ----------
    rms : ndarray
        Photometric repeatability RMS of stellar pairs for each random
        sampling.
    iqr : ndarray
       Photometric repeatability IQR of stellar pairs for each random sample.
    magDiff : ndarray
        Magnitude differences of stars between visits, for each random sample.
    magMean : ndarray
        Mean magnitude of stars seen across visits, for each random sample.
    blob : PA1Blob
        Blob with by-products from this measurement.

    Notes
    -----
    We calculate differences for 50 different random realizations of the
    measurement pairs, to provide some estimate of the uncertainty on our RMS
    estimates due to the random shuffling.  This estimate could be stated and
    calculated from a more formally derived motivation but in practice 50
    should be sufficient.

    The LSST Science Requirements Document (LPM-17), or SRD, characterizes the
    photometric repeatability by putting a requirement on the median RMS of
    measurements of non-variable bright stars.  This quantity is PA1, with a
    design, minimum, and stretch goals of (5, 8, 3) millimag following LPM-17
    as of 2011-07-06, available at http://ls.st/LPM-17.

    This present routine calculates this quantity in two different ways:

    1. RMS
    2. interquartile range (IQR)

    and also returns additional quantities of interest:

    - the pair differences of observations of stars,
    - the mean magnitude of each star

    While the SRD specifies that we should just compute the RMS directly, the
    current filter doesn't screen out variable stars as carefully as the SRD
    specifies, so using a more robust estimator like the IQR allows us to
    reject some outliers.  However, the IRQ is also less sensitive some
    realistic sources of scatter such as bad zero points, that the metric
    should include.
    """

    metric = None
    value = None
    units = 'mmag'
    label = 'PA1'
    schema = 'pa1-1.0.0'

    def __init__(self, matchedDataset, bandpass,
                 numRandomShuffles=50, verbose=False, job=None,
                 linkedBlobs=None, metricYamlDoc=None, metricYamlPath=None):
        MeasurementBase.__init__(self)
        self.bandpass = bandpass
        self.metric = Metric.fromYaml(self.label,
                                      yamlDoc=metricYamlDoc,
                                      yamlPath=metricYamlPath)

        # register input parameters for serialization
        # note that matchedDataset is treated as a blob, separately
        self.registerParameter('num_random_shuffles', numRandomShuffles,
                               units='', label='shuffles',
                               description='Number of random shuffles')

        self.matchedDataset = matchedDataset

        # Add external blob so that links will be persisted with
        # the measurement
        if linkedBlobs is not None:
            for blob in linkedBlobs:
                self.linkBlob(blob)
        self.linkBlob(self.matchedDataset)

        matches = matchedDataset.safeMatches
        magKey = matchedDataset.magKey
        pa1Samples = [self._calc_PA1_sample(matches, magKey)
                      for n in range(numRandomShuffles)]

        self.rms = np.array([pa1.rms for pa1 in pa1Samples])
        rmsDatum = Datum(self.rms, units='mmag',
                         label='RMS',
                         description='Photometric repeatability RMS of '
                                     'stellar pairs for each random sampling')

        self.iqr = np.array([pa1.iqr for pa1 in pa1Samples])
        iqrDatum = Datum(self.iqr, units='mmag',
                         label='IQR',
                         description='Photometric repeatability IQR of '
                                     'stellar pairs for each random sample')

        self.magDiff = np.array([pa1.magDiffs for pa1 in pa1Samples])
        magDiffDatum = Datum(self.magDiff, units='mmag',
                             label='Delta mag',
                             description='Photometric repeatability '
                                         'differences magnitudes for stellar '
                                         'pairs for each random sample')

        self.magMean = np.array([pa1.magMean for pa1 in pa1Samples])
        magMeanDatum = Datum(self.magMean, units='mag',
                             label='mag',
                             description='Mean magnitude of pairs of stellar '
                                         'sources matched across visits, for '
                                         'each random sample.')

        self.value = np.mean(self.iqr)

        self.blob = PA1Blob(rmsDatum, iqrDatum, magDiffDatum, magMeanDatum)
        self.linkBlob(self.blob)

        if job:
            job.registerMeasurement(self)

    def _calc_PA1_sample(self, groupView, magKey):
        magDiffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
        magMean = groupView.aggregate(np.mean, field=magKey)
        rmsPA1, iqrPA1 = computeWidths(magDiffs)
        return pipeBase.Struct(rms=rmsPA1, iqr=iqrPA1,
                               rmsUnits='mmag', iqrUnits='mmag',
                               magDiffs=magDiffs, magMean=magMean,
                               magDiffsUnits='mmag', magMeanUnits='mag')


class PA1Blob(BlobBase):
    """Blob container associated with PA1 measurements.

    Parameters
    ----------
    rmsDatum : Datum
        Datum with arrays of RMS measurements for each PA1 measurement sample.
    iqrDatum : Datum
        Datum with arrays of [25%, 75%] interquartile range measurements for
        each PA1 measurement sample.
    magDiffDatum : Datum
        Datum with arrays of magnitude differences for each PA1 measurement
        sample.
    magMeanDatum : Datum
        Datum with arrays of mean magnitudes for each PA1 measurement
        sample.
    """

    schema = 'pa1-blob-v1.0.0'

    def __init__(self, rmsDatum, iqrDatum, magDiffDatum, magMeanDatum):
        BlobBase.__init__(self)
        self._doc['rms'] = rmsDatum
        self._doc['iqr'] = iqrDatum
        self._doc['mag_diff'] = magDiffDatum
        self._doc['mag_mean'] = magMeanDatum

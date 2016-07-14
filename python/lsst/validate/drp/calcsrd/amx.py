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

import numpy as np

from ..base import MeasurementBase, Metric, Datum, BlobBase
from ..util import radiansToMilliarcsec, calcRmsDistances


class AMxMeasurement(MeasurementBase):
    """Measurement of AMx (x=1,2,3): The maximum rms of the astrometric
    distance distribution for stellar pairs with separations of D arcmin
    (repeatability).

    Parameters
    ----------
    x : int
        Variant of AMx metric (x=1, 2, 3), which in turn sets the radius
        of the annulus for selecting pairs of stars.
    matchedDataset : lsst.validate.drp.matchreduce.MatchedMultiVisitDataset
    bandpass : str
        Bandpass (filter name) used in this measurement (e.g., `'r'`).
    specName : str
        Name of a specification level to measure against (e.g., design,
        minimum, stretch).
    width : float
        Width around fiducial distance to include. [arcmin]
    magRange : 2-element list or tuple
        brighter, fainter limits of the magnitude range to include.
        E.g., `magRange=[17.5, 21.0]`
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
    rmsDistMas : ndarray
        RMS of distance repeatability between stellar pairs.
    blob : AMxBlob
        Blob with by-products from this measurement.

    Raises
    ------
    ValueError
        If `x` isn't in [1, 2, 3].

    Notes
    -----
    This table below is provided ``validate_drp``\ 's :file:`metrics.yaml`.

    LPM-17 dated 2011-07-06

    Specification:
        The rms of the astrometric distance distribution for
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

    metric = None
    value = None
    units = 'milliarcsecond'
    label = 'AMx'

    def __init__(self, x, matchedDataset, bandpass, width=2., magRange=None,
                 verbose=False, job=None,
                 linkedBlobs=None, metricYamlDoc=None, metricYamlPath=None):
        MeasurementBase.__init__(self)

        if x not in [1, 2, 3]:
            raise ValueError('AMx x should be 1, 2, or 3.')
        self.label = 'AM{0:d}'.format(x)
        self.metric = Metric.fromYaml(self.label,
                                      yamlDoc=metricYamlDoc,
                                      yamlPath=metricYamlPath)
        DSpec = self.metric.D

        # Register measurement parameters for serialization
        self.registerParameter('D', datum=DSpec)
        self.registerParameter('width', units='arcsecond',
                               label='Width', description='Width of annulus')
        self.registerParameter('annulus', units='arcsecond',
                               label='annulus radii',
                               description='Inner and outer radii of '
                                           'selection annulus.')
        self.registerParameter('magRange', units='mag',
                               description='Stellar magnitude selection '
                                           'range.')

        # Register measurement extras
        self.registerExtra('rmsDistMas', label='RMS', units='milliarcsecond')

        self.bandpass = bandpass
        self.magRange = magRange
        self.width = width

        self.matchedDataset = matchedDataset

        # Add external blob so that links will be persisted with
        # the measurement
        if linkedBlobs is not None:
            for blob in linkedBlobs:
                self.linkBlob(blob)
        self.linkBlob(self.matchedDataset)

        matches = matchedDataset.safeMatches

        self.annulus = self.D + (self.width/2)*np.array([-1, +1])

        rmsDistances, self.annulus, self.magRange = \
            calcRmsDistances(matches, self.annulus, magRange=self.magRange,
                             verbose=verbose)

        if not list(rmsDistances):
            # raise ValidateErrorNoStars(
            #     'No stars found that are %.1f--%.1f arcmin apart.' %
            #     (annulus[0], annulus[1]))
            # FIXME should we still report that this measurement was
            # attempted instead of just crashing.
            print('No stars found that are %.1f--%.1f arcmin apart.' %
                  (self.annulus[0], self.annulus[1]))
            self.rmsDistMas = None
            self.value = None
        else:
            self.rmsDistMas = np.asarray(radiansToMilliarcsec(rmsDistances))
            self.value = np.median(self.rmsDistMas)

        if job:
            job.registerMeasurement(self)

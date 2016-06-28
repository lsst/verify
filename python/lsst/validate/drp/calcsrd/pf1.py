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

from ..base import MeasurementBase, Metric
from ..util import getRandomDiffRmsInMas


class PF1Measurement(MeasurementBase):
    """Measurement of PF1: fraction of samples between median RMS (PA1) and
    PA2 specification.

    Parameters
    ----------
    matchedDataset : lsst.validate.drp.matchreduce.MatchedMultiVisitDataset
    pa1 : PA1Measurement
        A PA1 measurement instance.
    bandpass : str
        Bandpass (filter name) used in this measurement (e.g., `'r'`).
    specName : str
        Name of a specification level to measure against (e.g., design,
        minimum, stretch).
    verbose : bool, optional
        Output additional information on the analysis steps.
    job : :class:`lsst.validate.drp.base.Job`, optional
        If provided, the measurement will register itself with the Job
        object.
    linkedBlobs : list, optional
        A `list` of additional blobs (subclasses of BlobSerializerBase) that
        can provide additional context to the measurement, though aren't
        direct dependencies of the computation (e.g., `matchedDataset).

    Notes
    -----
    The LSST Science Requirements Document (LPM-17) is commonly referred
    to as the SRD.  The SRD puts a limit that no more than PF1 % of difference
    will vary by more than PA2 millimag.  The design, minimum, and stretch
    goals are PF1 = (10, 20, 5) % at PA2 = (15, 15, 10) millimag following
    LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.
    """

    metric = None
    value = None
    units = 'mmag'
    label = 'PF1'
    schema = 'pf1-1.0.0'

    def __init__(self, matchedDataset, pa1, bandpass, specName, verbose=False,
                 linkedBlobs=None, job=None,
                 metricYamlDoc=None, metricYamlPath=None):
        MeasurementBase.__init__(self)
        self.bandpass = bandpass
        self.specName = specName  # spec-dependent measure because of PF1 dep
        self.metric = Metric.fromYaml(self.label,
                                      yamlDoc=metricYamlDoc,
                                      yamlPath=metricYamlPath)

        self.matchedDataset = matchedDataset

        # Add external blob so that links will be persisted with
        # the measurement
        if linkedBlobs is not None:
            for blob in linkedBlobs:
                self.linkBlob(blob)
        self.linkBlob(self.matchedDataset)

        # Use first random sample from original PA1 measurement
        magDiffs = pa1.magDiff[0, :]

        pa2Val = self.metric.getSpec(specName, bandpass=self.bandpass).\
            PA2.getSpec(specName, bandpass=self.bandpass).value
        # FIXME should this be np.abs(magDiffs) (see pa2)?
        self.value = 100 * np.mean(np.asarray(magDiffs) > pa2Val)

        if job:
            job.registerMeasurement(self)

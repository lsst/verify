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


class AFxMeasurement(MeasurementBase):
    """Measurement of AFx (x=1,2,3): The maximum fraction of astrometric
    distances which deviate by more than ADx milliarcsec (see AMx) (%).

    Parameters
    ----------
    x : int
        Variant of AMx metric (x=1, 2, 3), which in turn sets the radius
        of the annulus for selecting pairs of stars.
    matchedDataset : lsst.validate.drp.matchreduce.MatchedMultiVisitDataset
    amx : :class:`lsst.validate.drp.calcsrd.AMxMeasurement`
        And AMx measurement, providing the median astrometric scatter in
        the annulus.
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
    linkedBlobs : dict, optional
        A `dict` of additional blobs (subclasses of BlobBase) that
        can provide additional context to the measurement, though aren't
        direct dependencies of the computation (e.g., `matchedDataset).

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
    units = ''
    label = 'AFx'

    def __init__(self, x, matchedDataset, amx, bandpass, specName,
                 verbose=False, job=None,
                 linkedBlobs=None, metricYamlDoc=None, metricYamlPath=None):
        MeasurementBase.__init__(self)

        if x not in [1, 2, 3]:
            raise ValueError('AFx x should be 1, 2, or 3.')
        self.label = 'AF{0:d}'.format(x)
        self.specName = specName
        self.bandpass = bandpass

        self.metric = Metric.fromYaml(self.label,
                                      yamlDoc=metricYamlDoc,
                                      yamlPath=metricYamlPath)

        # register input parameters for serialization
        # note that matchedDataset is treated as a blob, separately
        self.registerParameter('D', datum=amx.parameters['D'])
        self.registerParameter('annulus', datum=amx.parameters['annulus'])
        self.registerParameter('magRange', datum=amx.parameters['magRange'])
        self.registerParameter('AMx', datum=amx.datum)

        self.matchedDataset = matchedDataset

        # Add external blob so that links will be persisted with
        # the measurement
        if linkedBlobs is not None:
            for name, blob in linkedBlobs.items():
                setattr(self, name, blob)

        adx = getattr(self.metric.getSpec(specName, bandpass=self.bandpass),
                      'AD{0:d}'.format(x))\
            .getSpec(specName, bandpass=self.bandpass)
        self.registerParameter('ADx', datum=adx.datum)

        if amx.value:
            self.value = 100. * np.mean(amx.rmsDistMas > amx.value + self.ADx)
        else:
            # FIXME previously would raise ValidateErrorNoStars
            self.value = None

        if job:
            job.registerMeasurement(self)

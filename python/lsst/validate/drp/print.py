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

import numpy as np

from .base import ValidateError
from .calcSrd import calcPA1, calcPA2
from .srdSpec import getAstrometricSpec


def printPA1(brightMatches, psfMagKey, numRandomShuffles=50):
    """
    Notes
    -----
    We calculate differences for 50 different random realizations
    of the measurement pairs, to provide some estimate of the uncertainty
    on our RMS estimates due to the random shuffling.
    This estimate could be stated and calculated from a more formally
    derived motivation but in practice 50 should be sufficient.
    """
    pa1_samples = [calcPA1(brightMatches, psfMagKey)
                   for n in range(numRandomShuffles)]
    rmsPA1 = np.array([pa1.rms for pa1 in pa1_samples])
    iqrPA1 = np.array([pa1.iqr for pa1 in pa1_samples])
    print("PA1(RMS) = %4.2f+-%4.2f mmag" % (rmsPA1.mean(), rmsPA1.std()))
    print("PA1(IQR) = %4.2f+-%4.2f mmag" % (iqrPA1.mean(), iqrPA1.std()))


def printPA2(brightMatches, magKey):
    """Calculate and print the calculated PA2 from the LSST SRD from a groupView."""

    pa2 = calcPA2(brightMatches, magKey)
    print("minimum: PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" %
          (pa2.PF1['minimum'], pa2.minimum))
    print("design:  PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" %
          (pa2.PF1['design'], pa2.design))
    print("stretch: PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 10 mmag)" %
          (pa2.PF1['stretch'], pa2.stretch))


def printAMx(AMx):
    """Print the Astrometric performance.

    Inputs
    ------
    AMx : pipeBase.Struct
        Must contain:
        AMx, fractionOver, annulus, magRange, x, level,
        AMx_spec, AFx_spec, ADx_spec
    """

    percentOver = 100*AMx.fractionOver

    print("Median of distribution of RMS of distance of stellar pairs.")
    print("%s goals" % AMx.level.upper())
    print("For stars from %.2f < mag < %.2f" % (AMx.magRange[0], AMx.magRange[1]))
    print("from D = [%.2f, %.2f] arcmin, is %.2f mas (target is <= %.2f mas)." %
          (AMx.annulus[0], AMx.annulus[1], AMx.AMx, AMx.AMx_spec))
    print("  %.2f%% of sample is > %.2f mas from AM%d=%.2f mas (target is <= %.2f%%)" %
          (percentOver, AMx.ADx_spec, AMx.x, AMx.AMx_spec, AMx.AFx_spec))

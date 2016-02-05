#!/usr/bin/env python

#
# LSST Data Management System
# Copyright 2012-2016 LSST Corporation.
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
# see <http://www.lsstcorp.org/LegalNotices/>.
#

from __future__ import print_function

import os
import sys

import unittest
import warnings

import numpy as np
from numpy.testing import assert_allclose

import lsst.afw.geom as afwGeom
import lsst.afw.coord as afwCoord
import lsst.pex.exceptions as pexExcept
import lsst.utils.tests as utilsTests



class CoordTestCase(unittest.TestCase):
    """Testing basic coordinate calculations."""

    def setUp(self):
        self.simpleRa = [15, 25]
        self.simpleDec = [30, 45]
        self.zeroDec = np.zeros_like(self.simpleRa)

        self.wrapRa = [359.9999, 0.0001, -0.1, +0.1]
        self.wrapDec = [1, 0, -1, 0]

    def tearDown(self):
        pass

    def testSimpleAverageCoord(self):
        icrs = afwCoord.makeCoordEnum('ICRS')
        angleRa = [afwGeom.Angle(r, afwGeom.degrees) for r in self.simpleRa]
        angleDec = [afwGeom.Angle(d, afwGeom.degrees) for d in self.zeroDec]
        coords = [afwCoord.makeCoord(icrs, ar, ad) for (ar, ad) in zip(angleRa, angleDec)]
        (meanRa, meanDec) = afwCoord.averageCoord(coords)
        assert_allclose([20], meanRa.asDegrees())
        assert_allclose([0], meanDec.asDegrees())
        

def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(CoordTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    if "--display" in sys.argv:
        display = True
    run(True)

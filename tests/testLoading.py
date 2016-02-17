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

import lsst.utils
import lsst.utils.tests as utilsTests

from lsst.validate.drp import util 


class LoadDataTestCase(unittest.TestCase):
    """Testing loading of configuration files and repo."""

    def setUp(self):
        validateDrpDir = lsst.utils.getPackageDir('validate_drp')
        testDataDir = os.path.join(validateDrpDir, 'tests')
        self.configFile = os.path.join(testDataDir, 'runCfht.yaml')
        self.configFileNoDataIds = os.path.join(testDataDir, 'runCfhtParametersOnly.yaml')

    def tearDown(self):
        pass

    def testLoadingOfConfigFileParameters(self):
        dataIds, good_mag_limit, \
            medianAstromscatterRef, medianPhotoscatterRef, matchRef = \
                util.loadDataIdsAndParameters(self.configFile)
        self.assertAlmostEqual(good_mag_limit, 21.0)
        self.assertAlmostEqual(medianAstromscatterRef, 25)
        self.assertAlmostEqual(medianPhotoscatterRef, 25)
        self.assertAlmostEqual(matchRef, 5000)

    def testLoadingOfConfigFileDataIds(self):
        dataIds, good_mag_limit, \
            medianAstromscatterRef, medianPhotoscatterRef, matchRef = \
                util.loadDataIdsAndParameters(self.configFile)
        # Tests of the dict entries require constructing and comparing sets
        self.assertEqual(set(['r']), set([d['filter'] for d in dataIds]))
        self.assertEqual(set([849375, 850587]),
                         set([d['visit'] for d in dataIds]))

    def testLoadingEmptyDataIds(self):
        dataIds, good_mag_limit, \
            medianAstromscatterRef, medianPhotoscatterRef, matchRef = \
                util.loadDataIdsAndParameters(self.configFileNoDataIds)
        # Tests of the dict entries require constructing and comparing sets
        self.assertFalse(dataIds)

def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(LoadDataTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    if "--display" in sys.argv:
        display = True
    run(True)

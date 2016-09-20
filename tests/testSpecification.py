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

import unittest

import lsst.utils.tests as utilsTests

from lsst.validate.base import Specification, Datum


class MetricTestCase(unittest.TestCase):
    """Test Metrics and metrics.yaml functionality."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testDependencyAccess(self):
        deps = {'a': Datum(5, 'mag')}
        s = Specification('design', 0., '', dependencies=deps)
        self.assertEqual(s.a.value, 5)


def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(MetricTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)


if __name__ == "__main__":
    run(True)

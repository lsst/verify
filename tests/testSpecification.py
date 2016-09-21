#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.

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

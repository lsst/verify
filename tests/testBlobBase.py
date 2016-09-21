#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.

from __future__ import print_function

import unittest

import lsst.utils.tests as utilsTests
from lsst.validate.base import BlobBase


class DemoBlob(BlobBase):

    schema = 'demo'

    def __init__(self):
        BlobBase.__init__(self)

        self.registerDatum(
            'mag',
            units='mag',
            value=5,
            description='Magnitude as int')


class BlobBaseTestCase(unittest.TestCase):
    """Test Mesaurement class (via MeasurementBase) functionality."""

    def setUp(self):
        self.blob = DemoBlob()

    def tearDown(self):
        pass

    def testAttribute(self):
        self.assertEqual(self.blob.mag, 5)

    def testJson(self):
        print(dir(self.blob))
        j = self.blob.json

        self.assertEqual(j['data']['mag']['value'], 5)
        self.assertEqual(j['data']['mag']['units'], 'mag')
        self.assertEqual(j['data']['mag']['label'], 'mag')
        self.assertEqual(j['data']['mag']['description'], 'Magnitude as int')


def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(BlobBaseTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)


if __name__ == "__main__":
    run(True)

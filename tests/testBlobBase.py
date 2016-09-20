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

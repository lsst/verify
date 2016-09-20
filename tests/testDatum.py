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

from numpy.testing import assert_almost_equal

import lsst.utils.tests as utilsTests

import astropy.units as u
from lsst.validate.base import Datum


class DatumTestCase(unittest.TestCase):
    """Test Datum functionality"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testProperties(self):
        """Validate basic setters and getters."""
        d = Datum(5., 'mmag', label='millimag', description='Hello world')

        assert_almost_equal(d.value, 5.)

        d.value = 7
        assert_almost_equal(d.value, 7)

        self.assertEqual(d.units, 'mmag')
        self.assertEqual(d.astropy_units, u.mmag)

        d.units = 'mag'
        self.assertEqual(d.astropy_units, u.mag)

        self.assertEqual(d.label, 'millimag')
        d.label = 'magnitudes'
        self.assertEqual(d.label, 'magnitudes')

        self.assertEqual(d.description, 'Hello world')
        d.description = 'Updated description.'
        self.assertEqual(d.description, 'Updated description.')

        self.assertIsInstance(d.quantity, u.Quantity)

    def testBadUnit(self):
        """Ensure that units are being validated by astropy."""
        with self.assertRaises(ValueError):
            Datum(5., 'millimag')

    def testUnitless(self):
        """Ensure that Datums can be unitless too."""
        d = Datum(5., '')
        self.assertEqual(d.units, '')
        self.assertEqual(d.astropy_units, u.dimensionless_unscaled)

    def testJsonOutput(self):
        """Verify content from json property."""
        d = Datum(5., 'mmag', label='millimag', description='Hello world')
        dj = d.json

        fields = ('value', 'units', 'label', 'description')
        for f in fields:
            self.assertIn(f, dj)
            self.assertEqual(getattr(d, f), dj[f])


def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(DatumTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)


if __name__ == "__main__":
    run(True)

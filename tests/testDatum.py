#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.

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

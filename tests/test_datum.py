#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import unittest

import astropy.units as u

from lsst.validate.base import Datum


class DatumTestCase(unittest.TestCase):
    """Test Datum functionality"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_properties(self):
        """Validate basic setters and getters."""
        d = Datum(5., 'mmag', label='millimag', description='Hello world')

        self.assertIsInstance(d.quantity, u.Quantity)

        self.assertEqual(d.quantity.value, 5.)

        d.quantity = 7 * u.mmag
        self.assertEqual(d.quantity.value, 7)

        self.assertEqual(d.unit_str, 'mmag')
        self.assertEqual(d.unit, u.mmag)

        # change units
        d.quantity = 5 * u.mag
        self.assertEqual(d.unit, u.mag)

        self.assertEqual(d.label, 'millimag')
        d.label = 'magnitudes'
        self.assertEqual(d.label, 'magnitudes')

        self.assertEqual(d.description, 'Hello world')
        d.description = 'Updated description.'
        self.assertEqual(d.description, 'Updated description.')

    def test_bad_unit(self):
        """Ensure that units are being validated by astropy."""
        with self.assertRaises(ValueError):
            Datum(5., 'millimag')

    def test_no_units(self):
        """Ensure an exception is raised if not units are provided to Datum.
        """
        with self.assertRaises(ValueError):
            Datum(5.)

    def test_init_with_quantity(self):
        """Ensure a Datum can be build from a Quantity."""
        d = Datum(5 * u.mag)

        self.assertEqual(d.quantity.value, 5.)
        self.assertEqual(d.unit_str, 'mag')

    def test_quantity_update(self):
        """Verify that when a quantity is updated the unit attributes
        are updated.
        """
        d = Datum(5 * u.mag)
        self.assertEqual(d.quantity.value, 5.)
        self.assertEqual(d.unit_str, 'mag')

        d.quantity = 100. * u.mmag
        self.assertEqual(d.quantity.value, 100.)
        self.assertEqual(d.unit_str, 'mmag')

    def test_unitless(self):
        """Ensure that Datums can be unitless too."""
        d = Datum(5., '')
        self.assertEqual(d.unit_str, '')
        self.assertEqual(d.unit, u.dimensionless_unscaled)

        json_data = d.json
        d2 = Datum.from_json(json_data)
        self.assertEqual(d.quantity, d2.quantity)
        self.assertEqual(d.unit, d2.unit)
        self.assertEqual(d.label, d2.label)
        self.assertEqual(d.description, d2.description)

    def test_str_quantity(self):
        """Quantity as a string."""
        d = Datum('Hello world', label='Test string',
                  description='Test description.')
        self.assertEqual(d.quantity, 'Hello world')
        self.assertIsNone(d.unit)
        self.assertEqual(d.unit_str, '')
        self.assertEqual(d.label, 'Test string')
        self.assertEqual(d.description, 'Test description.')

        json_data = d.json
        d2 = Datum.from_json(json_data)
        self.assertEqual(d.quantity, d2.quantity)
        self.assertEqual(d.unit, d2.unit)
        self.assertEqual(d.label, d2.label)
        self.assertEqual(d.description, d2.description)

    def test_bool_quantity(self):
        """Quantity as a boolean."""
        d = Datum(True, label='Test boolean',
                  description='Test description.')
        self.assertTrue(d.quantity)
        self.assertIsNone(d.unit)
        self.assertEqual(d.unit_str, '')
        self.assertEqual(d.label, 'Test boolean')
        self.assertEqual(d.description, 'Test description.')

        json_data = d.json
        d2 = Datum.from_json(json_data)
        self.assertEqual(d.quantity, d2.quantity)
        self.assertEqual(d.unit, d2.unit)
        self.assertEqual(d.label, d2.label)
        self.assertEqual(d.description, d2.description)

    def test_int_quantity(self):
        """Quantity as a unitless int."""
        d = Datum(5, label='Test int',
                  description='Test description.')
        self.assertEqual(d.quantity, 5)
        self.assertIsNone(d.unit)
        self.assertEqual(d.unit_str, '')
        self.assertEqual(d.label, 'Test int')
        self.assertEqual(d.description, 'Test description.')

        json_data = d.json
        d2 = Datum.from_json(json_data)
        self.assertEqual(d.quantity, d2.quantity)
        self.assertEqual(d.unit, d2.unit)
        self.assertEqual(d.label, d2.label)
        self.assertEqual(d.description, d2.description)

    def test_none(self):
        """Quantity as None."""
        d = Datum(None, label='Test None',
                  description='Test description.')
        self.assertIsNone(d.quantity)
        self.assertIsNone(d.unit)
        self.assertEqual(d.unit_str, '')
        self.assertEqual(d.label, 'Test None')
        self.assertEqual(d.description, 'Test description.')

        json_data = d.json
        d2 = Datum.from_json(json_data)
        self.assertEqual(d.quantity, d2.quantity)
        self.assertEqual(d.unit, d2.unit)
        self.assertEqual(d.label, d2.label)
        self.assertEqual(d.description, d2.description)

    def test_json_output(self):
        """Verify content from json property."""
        d = Datum(5., 'mmag', label='millimag', description='Hello world')
        dj = d.json

        self.assertEqual(d.quantity.value, dj['value'])
        self.assertEqual(d.unit_str, dj['unit'])
        self.assertEqual(d.label, dj['label'])
        self.assertEqual(d.description, dj['description'])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import unittest
import astropy.units as u

from lsst.validate.base import BlobBase


class DemoBlob(BlobBase):
    """Example Blob class."""

    name = 'demo'

    def __init__(self):
        BlobBase.__init__(self)

        self.register_datum(
            'mag',
            quantity=5 * u.mag,
            description='Magnitude')

        self.register_datum(
            'updateable_mag',
            quantity=5 * u.mag,
            description='Magnitude')


class BlobBaseTestCase(unittest.TestCase):
    """Test BlobBase functionality."""

    def setUp(self):
        self.blob = DemoBlob()

    def tearDown(self):
        pass

    def test_attribute(self):
        self.assertEqual(self.blob.mag, 5 * u.mag)
        self.assertEqual(self.blob.datums['mag'].quantity, 5 * u.mag)
        self.assertEqual(self.blob.datums['mag'].label, 'mag')
        self.assertEqual(self.blob.datums['mag'].description, 'Magnitude')

    def test_attribute_update(self):
        self.blob.updateable_mag = 10. * u.mag

        self.assertEqual(self.blob.updateable_mag, 10 * u.mag)
        self.assertEqual(self.blob.datums['updateable_mag'].quantity, 10 * u.mag)
        self.assertEqual(self.blob.datums['updateable_mag'].label, 'updateable_mag')
        self.assertEqual(self.blob.datums['updateable_mag'].description, 'Magnitude')

    def test_json(self):
        j = self.blob.json

        self.assertIn('identifier', j)
        self.assertEqual(self.blob.name, 'demo')
        self.assertEqual(j['data']['mag']['value'], 5)
        self.assertEqual(j['data']['mag']['unit'], 'mag')
        self.assertEqual(j['data']['mag']['label'], 'mag')
        self.assertEqual(j['data']['mag']['description'], 'Magnitude')


if __name__ == "__main__":
    unittest.main()

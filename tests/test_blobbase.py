#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.

from __future__ import print_function

import unittest

from lsst.validate.base import BlobBase


class DemoBlob(BlobBase):

    name = 'demo'

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


if __name__ == "__main__":
    unittest.main()

#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
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
# see <https://www.lsstcorp.org/LegalNotices/>.
#
from __future__ import print_function

import unittest

import astropy.units as u

from lsst.verify import Blob, Datum
from lsst.verify.blobset import BlobSet


class BlobSetTestCase(unittest.TestCase):
    """Test BlobSet general usage."""

    def setUp(self):
        mag1 = Datum(
            quantity=5 * u.mag,
            label='mag1',
            description='Magnitude')
        mag2 = Datum(
            quantity=10 * u.mag,
            label='mag2',
            description='Magnitude')
        self.blob1 = Blob('blob1', mag1=mag1, mag2=mag2)

        sep1 = Datum(
            quantity=5 * u.arcsec,
            label='sep1',
            description='Separation')
        sep2 = Datum(
            quantity=10 * u.arcsec,
            label='sep2',
            description='Separation')
        self.blob2 = Blob('blob2', sep1=sep1, sep2=sep2)

    def test_blob_set(self):
        blob_set = BlobSet([self.blob1])

        self.assertIn('blob1', blob_set)
        self.assertIn(self.blob1.identifier, blob_set)
        self.assertEqual(len(blob_set), 1)
        self.assertIs(blob_set['blob1'], self.blob1)

        # add blob with inconsistent identifier
        with self.assertRaises(KeyError):
            blob_set['blob'] = self.blob2

        # add with identifier
        blob_set[self.blob2.identifier] = self.blob2
        self.assertIn('blob2', blob_set)
        self.assertIn(self.blob2.identifier, blob_set)
        self.assertEqual(len(blob_set), 2)
        self.assertIs(blob_set['blob2'], self.blob2)

        # delete blob2
        del blob_set['blob2']
        self.assertNotIn('blob2', blob_set)
        self.assertNotIn(self.blob2.identifier, blob_set)
        self.assertEqual(len(blob_set), 1)

        # insert blob2
        blob_set.insert(self.blob2)
        self.assertIn('blob2', blob_set)
        self.assertIn(self.blob2.identifier, blob_set)
        self.assertEqual(len(blob_set), 2)
        self.assertIs(blob_set['blob2'], self.blob2)

        # iteration
        blobs = [b for k, b in blob_set.items()]
        self.assertEqual(len(blobs), 2)
        for blob in blobs:
            self.assertIsInstance(blob, Blob)

        # serialize
        json_doc = blob_set.json

        # deserialize
        new_blob_set = BlobSet.deserialize(blobs=json_doc)
        self.assertEqual(new_blob_set, blob_set)


if __name__ == "__main__":
    unittest.main()

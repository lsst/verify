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

import unittest
import astropy.units as u

from lsst.verify.blob import Blob
from lsst.verify.datum import Datum


class BlobTestCase(unittest.TestCase):
    """Test Blob functionality."""

    def setUp(self):
        self.mag1 = Datum(
            quantity=5 * u.mag,
            label='mag1',
            description='Magnitude')

        self.mag2 = Datum(
            quantity=10 * u.mag,
            label='mag2',
            description='Magnitude')

        self.blob = Blob('demo', mag1=self.mag1, mag2=self.mag2)

    def test_access(self):
        self.assertEqual(self.blob['mag1'], self.mag1)
        self.assertEqual(self.blob['mag2'], self.mag2)

        with self.assertRaises(KeyError):
            self.blob['magX']

    def test_len(self):
        self.assertEqual(len(self.blob), 2)

    def test_contains(self):
        self.assertTrue('mag1' in self.blob)
        self.assertTrue('mag2' in self.blob)
        self.assertFalse('magX' in self.blob)

    def test_iter(self):
        keys = set([k for k in self.blob])
        self.assertEqual(keys, set(['mag1', 'mag2']))

    def test_name(self):
        self.assertEqual(self.blob.name, 'demo')

    def test_identifier(self):
        new_blob = Blob('demo')
        self.assertNotEqual(new_blob.identifier, self.blob.identifier)

    def test_json(self):
        j = self.blob.json

        self.assertIn('identifier', j)
        self.assertEqual(self.blob.name, 'demo')
        self.assertEqual(j['data']['mag1']['value'], 5)
        self.assertEqual(j['data']['mag1']['unit'], 'mag')
        self.assertEqual(j['data']['mag1']['label'], 'mag1')
        self.assertEqual(j['data']['mag1']['description'], 'Magnitude')

        # Rebuild from blob
        b2 = Blob.deserialize(**j)
        self.assertEqual(self.blob, b2)

    def test_mutation(self):
        blob = Blob('mutable')
        self.assertEqual(len(blob), 0)

        blob['test'] = Datum(quantity=1 * u.arcsec)
        self.assertEqual(len(blob), 1)

        with self.assertRaises(TypeError):
            blob['fails'] = 10
        self.assertEqual(len(blob), 1)

        with self.assertRaises(KeyError):
            blob[10] = Datum(quantity=1 * u.arcsec)
        self.assertEqual(len(blob), 1)

        del blob['test']
        self.assertEqual(len(blob), 0)


if __name__ == "__main__":
    unittest.main()

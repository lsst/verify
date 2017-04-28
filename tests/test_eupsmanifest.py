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

import os
import unittest

from lsst.verify.metadata.eupsmanifest import Manifest


class ManifestTestCase(unittest.TestCase):
    """Test lsst.verify.provsrc.eupsmanifest.Manifest.

    These tests are tied to data in tests/data/lsstsw/build/manifest.txt.
    """

    def setUp(self):
        self.manifest_path = os.path.join(
            os.path.dirname(__file__),
            'data', 'lsstsw', 'build', 'manifest.txt')

    def test_manifest(self):
        with open(self.manifest_path) as f:
            manifest = Manifest(f)

        self.assertEqual(
            len(manifest),
            132)

        self.assertEqual(manifest.build, 'b1988')

        self.assertIn('python', manifest)
        self.assertNotIn('ruby', manifest)

        keys = [k for k in manifest]
        self.assertEqual(len(keys), len(manifest))
        for key in keys:
            self.assertIn(key, manifest)

        afw = manifest['afw']
        self.assertEqual(afw.name, 'afw')
        self.assertEqual(
            afw.git_sha,
            'fc355a99abe3425003b0e5fbe1e13a39644b1e95')
        self.assertEqual(
            afw.version,
            '2.2016.10-22-gfc355a9')
        self.assertEqual(
            afw.dependencies,
            ['daf_base', 'daf_persistence', 'pex_config', 'ndarray',
             'cfitsio', 'wcslib', 'numpy', 'minuit2', 'eigen', 'gsl',
             'fftw', 'utils', 'astropy', 'pyfits', 'matplotlib', 'afwdata']
        )


if __name__ == "__main__":
    unittest.main()

# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import unittest
try:
    import unittest.mock as mock
except ImportError:
    mock = None

import lsst.verify.metadata.lsstsw as lsstsw


class LsstswReposTestCase(unittest.TestCase):
    """Tests for lsst.verify.provsrc.lsstsw.LsstswRepos.

    These tests are tied to data in tests/data/lsstsw/
    """

    def setUp(self):
        self.lsstsw_dirname = os.path.join(
            os.path.dirname(__file__),
            'data', 'lsstsw')

    def test_lsstsw_repos(self):
        lsstsw_repos = lsstsw.LsstswRepos(self.lsstsw_dirname)

        self.assertEqual(
            lsstsw_repos.manifest_path,
            os.path.join(self.lsstsw_dirname, 'build', 'manifest.txt')
        )

        self.assertEqual(
            lsstsw_repos.get_package_repo_path('afw'),
            os.path.join(self.lsstsw_dirname, 'build', 'afw')
        )

        self.assertIn('afw', lsstsw_repos)
        self.assertNotIn('ruby', lsstsw_repos)

        self.assertEqual(len(lsstsw_repos), 196)

        self.assertEqual(
            lsstsw_repos.get_package_repo_url('afw'),
            'https://github.com/lsst/afw.git'
        )

        self.assertEqual(
            lsstsw_repos.get_package_repo_url('xrootd'),
            'https://github.com/lsst/xrootd.git'
        )

    # FIXME not sure how to mock GitPython here. Actually complainst can't
    # lsstsw module.
    # @mock.patch('lsstsw.git.Repo')
    # @unittest.skipIf(mock is None, 'unittest.mock is required.')
    # def test_get_package_branch(self, MockRepo):
    #     # mock git.Repo in lsst.verify.provsrc.lsstsw so that a repo's active
    #     # branch is main and doesn't attempt to actually query the repo in
    #     # the filesystem.
    #     # mock.mocker.patch('lsstsw.verify.provsrc.lsstsw.git.Repo')
    #     MockRepo.return_value.active_branch.name = 'main'

    #     lsstsw_repos = lsstsw.LsstswRepos(self.lsstsw_dirname)
    #     self.assertEqual(
    #         lsstsw_repos.get_package_branch('afw'),
    #         'main')


if __name__ == "__main__":
    unittest.main()

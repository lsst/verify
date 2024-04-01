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

import shutil
import tempfile
import unittest

import lsst.utils.tests
from lsst.dax.apdb import Apdb, ApdbSql

from lsst.verify.tasks import DirectApdbLoader


class DirectApdbLoaderTestSuite(lsst.utils.tests.TestCase):

    def _dummyApdbConfig(self):
        return ApdbSql.init_database(db_url=self.db_url)

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.db_url = f"sqlite:///{self.tempdir}/apdb.sqlite3"
        self.task = DirectApdbLoader()

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def testValidConfig(self):
        result = self.task.run(self._dummyApdbConfig())
        self.assertIsInstance(result.apdb, Apdb)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

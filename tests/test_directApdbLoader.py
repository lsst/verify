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

import unittest

import lsst.utils.tests
from lsst.dax.apdb import Apdb, ApdbSqlConfig

from lsst.verify.tasks import DirectApdbLoader


class DirectApdbLoaderTestSuite(lsst.utils.tests.TestCase):

    @staticmethod
    def _dummyApdbConfig():
        config = ApdbSqlConfig()
        config.db_url = "sqlite://"     # in-memory DB
        return config

    def setUp(self):
        self.task = DirectApdbLoader()

    def testNoConfig(self):
        result = self.task.run(None)
        self.assertIsNone(result.apdb)

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

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

import unittest.mock

import lsst.utils.tests
from lsst.daf.persistence import ButlerDataRef
from lsst.afw.cameraGeom import Camera
from lsst.verify import Job
from lsst.verify.gen2tasks import SquashMetadataTask


def _makeMockDataref(dataId=None):
    """A dataref-like object that returns a mock camera.
    """
    camera = unittest.mock.NonCallableMock(
        Camera, autospec=True, **{"getName.return_value": "fancyCam"})
    return unittest.mock.NonCallableMock(
        ButlerDataRef, autospec=True, **{"get.return_value": camera},
        dataId=dataId)


class SquashMetadataTestSuite(lsst.utils.tests.TestCase):

    def setUp(self):
        self.testbed = SquashMetadataTask()
        self.job = Job()

    def _checkDataId(self, dataId):
        dataref = _makeMockDataref(dataId)
        self.testbed.run(self.job, dataref=dataref)
        self.assertEqual(set(self.job.meta.keys()),
                         {"instrument", "butler_generation"} | dataId.keys())
        self.assertEqual(self.job.meta["instrument"], "FANCYCAM")
        for key, value in dataId.items():
            self.assertEqual(self.job.meta[key], value)

    def testCcdVisit(self):
        self._checkDataId(dict(visit=42, ccd=27))

    def testTractPatch(self):
        self._checkDataId(dict(tract=76, patch="2,3"))

    def testEmptyId(self):
        self._checkDataId({})


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

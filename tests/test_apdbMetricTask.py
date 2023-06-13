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
import unittest.mock

import astropy.units as u

import lsst.utils.tests
from lsst.pex.config import Config
import lsst.daf.butler.tests as butlerTests
from lsst.pipe.base import Task, Struct, testUtils

from lsst.verify import Measurement
from lsst.verify.tasks import ApdbMetricTask
from lsst.verify.tasks.testUtils import ApdbMetricTestCase


class DummyTask(ApdbMetricTask):
    _DefaultName = "NotARealTask"

    def makeMeasurement(self, _dbHandle, outputDataId):
        if outputDataId:
            nChars = len(outputDataId["instrument"])
            return Measurement(self.config.metricName,
                               nChars * u.dimensionless_unscaled)
        else:
            return Measurement(self.config.metricName,
                               0 * u.dimensionless_unscaled)


class Gen3ApdbTestSuite(ApdbMetricTestCase):
    @classmethod
    def makeTask(cls):
        class MockDbLoader(Task):
            ConfigClass = Config

            def run(self, _):
                return Struct(apdb=unittest.mock.Mock())

        config = DummyTask.ConfigClass()
        config.dbLoader.retarget(MockDbLoader)
        config.connections.package = "verify"
        config.connections.metric = "DummyApdb"
        return DummyTask(config=config)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.CAMERA_ID = "NotACam"
        cls.VISIT_ID = 42
        cls.CHIP_ID = 5

        # makeTestRepo called in setUpClass because it's *very* slow
        cls.root = tempfile.mkdtemp()
        cls.repo = butlerTests.makeTestRepo(cls.root, {
            "instrument": [cls.CAMERA_ID],
            "visit": [cls.VISIT_ID],
            "detector": [cls.CHIP_ID],
        })

        # self.task not visible at class level
        task = cls.makeTask()
        connections = task.config.ConnectionsClass(config=task.config)

        butlerTests.addDatasetType(
            cls.repo,
            connections.measurement.name,
            connections.measurement.dimensions,
            connections.measurement.storageClass)
        butlerTests.addDatasetType(
            cls.repo,
            connections.dbInfo.name,
            connections.dbInfo.dimensions,
            connections.dbInfo.storageClass)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()

        self.connections = self.task.config.ConnectionsClass(
            config=self.task.config)

    def _prepareQuantum(self, task):
        globalId = {
            "instrument": self.CAMERA_ID,
        }
        detectorId = {
            "instrument": self.CAMERA_ID,
            "visit": self.VISIT_ID,
            "detector": self.CHIP_ID,
        }

        butler = butlerTests.makeTestCollection(self.repo)
        # task.config not persistable if it refers to a local class
        # We don't actually use the persisted config, so just make a new one
        info = task.ConfigClass()
        butler.put(info, "apdb_marker", detectorId)

        quantum = testUtils.makeQuantum(
            task, butler, globalId,
            {"dbInfo": [detectorId], "measurement": globalId})

        return (butler, quantum, info)

    def testRunQuantum(self):
        butler, quantum, input = self._prepareQuantum(self.task)

        run = testUtils.runTestQuantum(self.task, butler, quantum)

        # Did output data ID get passed to DummyTask.run?
        expectedId = lsst.daf.butler.DataCoordinate.standardize(
            {"instrument": self.CAMERA_ID},
            universe=butler.dimensions)
        run.assert_called_once_with(
            dbInfo=[input],
            outputDataId=expectedId)

    def testRunQuantumNone(self):
        class NoneTask(DummyTask):
            def run(self, *args, **kwargs):
                return Struct(measurement=None)

        config = NoneTask.ConfigClass()
        config.connections.package = "verify"
        config.connections.metric = "DummyApdb"
        task = NoneTask(config=config)
        butler, quantum, input = self._prepareQuantum(task)

        with unittest.mock.patch.object(
                lsst.pipe.base.ButlerQuantumContext, "put") as put:
            testUtils.runTestQuantum(task, butler, quantum, mockRun=False)
            # Should not attempt to write nonexistent data
            put.assert_not_called()


# Hack around unittest's hacky test setup system
del ApdbMetricTestCase


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

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

import time
import unittest
import warnings

import astropy.units as u

import lsst.utils.tests
import lsst.pipe.base.testUtils
from lsst.pex.config import Config
from lsst.pipe.base import Task
from lsst.utils.timer import timeMethod

from lsst.verify import Measurement, Name
from lsst.verify.gen2tasks.testUtils import MetricTaskTestCase
from lsst.verify.tasks import MetricComputationError, TimingMetricTask, \
    MemoryMetricTask
from lsst.verify.tasks.testUtils import MetadataMetricTestCase


class DummyTask(Task):
    ConfigClass = Config
    _DefaultName = "NotARealTask"
    taskLength = 0.1

    @timeMethod
    def run(self):
        time.sleep(self.taskLength)


class TimingMetricTestSuite(MetadataMetricTestCase):
    @classmethod
    def makeTask(cls):
        return TimingMetricTask(config=cls._standardConfig())

    @staticmethod
    def _standardConfig():
        config = TimingMetricTask.ConfigClass()
        config.connections.labelName = DummyTask._DefaultName
        config.target = DummyTask._DefaultName + ".run"
        config.connections.package = "verify"
        config.connections.metric = "DummyTime"
        return config

    def setUp(self):
        super().setUp()
        self.config = TimingMetricTestSuite._standardConfig()
        self.metric = Name("verify.DummyTime")

        self.scienceTask = DummyTask()
        self.scienceTask.run()

    def testValid(self):
        result = self.task.run(self.scienceTask.getFullMetadata())
        lsst.pipe.base.testUtils.assertValidOutput(self.task, result)
        meas = result.measurement

        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas.metric_name, self.metric)
        self.assertGreater(meas.quantity, 0.0 * u.second)
        self.assertLess(meas.quantity, 2 * DummyTask.taskLength * u.second)

    def testNoMetric(self):
        self.config.connections.package = "foo.bar"
        self.config.connections.metric = "FooBarTime"
        task = TimingMetricTask(config=self.config)
        with self.assertRaises(TypeError):
            task.run(self.scienceTask.getFullMetadata())

    def testMissingData(self):
        result = self.task.run(None)
        lsst.pipe.base.testUtils.assertValidOutput(self.task, result)
        meas = result.measurement
        self.assertIsNone(meas)

    def testRunDifferentMethod(self):
        self.config.target = DummyTask._DefaultName + ".runDataRef"
        task = TimingMetricTask(config=self.config)
        result = task.run(self.scienceTask.getFullMetadata())
        lsst.pipe.base.testUtils.assertValidOutput(task, result)
        meas = result.measurement
        self.assertIsNone(meas)

    def testNonsenseKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        startKeys = [key
                     for key in metadata.paramNames(topLevelOnly=False)
                     if "StartCpuTime" in key]
        for key in startKeys:
            del metadata[key]

        task = TimingMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run(metadata)

    def testBadlyTypedKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        endKeys = [key
                   for key in metadata.paramNames(topLevelOnly=False)
                   if "EndCpuTime" in key]
        for key in endKeys:
            metadata[key] = str(float(metadata[key]))

        task = TimingMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run(metadata)

    def testDeprecated(self):
        with warnings.catch_warnings(record=True):
            self.config.metric = "verify.DummyTime"
        self.config.connections.package = ""
        self.config.connections.metric = ""
        with warnings.catch_warnings(record=True) as emitted:
            self.config.validate()
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0].category, FutureWarning)
        self.assertEqual(self.config.connections.package, "verify")
        self.assertEqual(self.config.connections.metric, "DummyTime")


class MemoryMetricTestSuite(MetadataMetricTestCase):
    @classmethod
    def makeTask(cls):
        return MemoryMetricTask(config=cls._standardConfig())

    @staticmethod
    def _standardConfig():
        config = MemoryMetricTask.ConfigClass()
        config.connections.labelName = DummyTask._DefaultName
        config.target = DummyTask._DefaultName + ".run"
        config.connections.package = "verify"
        config.connections.metric = "DummyMemory"
        return config

    def setUp(self):
        super().setUp()
        self.config = self._standardConfig()
        self.metric = Name("verify.DummyMemory")

        self.scienceTask = DummyTask()
        self.scienceTask.run()

    def testValid(self):
        result = self.task.run(self.scienceTask.getFullMetadata())
        lsst.pipe.base.testUtils.assertValidOutput(self.task, result)
        meas = result.measurement

        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas.metric_name, self.metric)
        self.assertGreater(meas.quantity, 0.0 * u.byte)

    def testNoMetric(self):
        self.config.connections.package = "foo.bar"
        self.config.connections.metric = "FooBarMemory"
        task = MemoryMetricTask(config=self.config)
        with self.assertRaises(TypeError):
            task.run(self.scienceTask.getFullMetadata())

    def testMissingData(self):
        result = self.task.run(None)
        lsst.pipe.base.testUtils.assertValidOutput(self.task, result)
        meas = result.measurement
        self.assertIsNone(meas)

    def testRunDifferentMethod(self):
        self.config.target = DummyTask._DefaultName + ".runDataRef"
        task = MemoryMetricTask(config=self.config)
        result = task.run(self.scienceTask.getFullMetadata())
        lsst.pipe.base.testUtils.assertValidOutput(task, result)
        meas = result.measurement
        self.assertIsNone(meas)

    def testBadlyTypedKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        endKeys = [key
                   for key in metadata.paramNames(topLevelOnly=False)
                   if "EndMaxResidentSetSize" in key]
        for key in endKeys:
            metadata[key] = str(float(metadata[key]))

        task = MemoryMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run(metadata)

    def testOldMetadata(self):
        """Test compatibility with version 0 metadata

        This can't actually test differences in unit handling between version 0
        and version 1, but at least verifies that the code didn't choke on
        old-style metadata.
        """
        newMetadata = self.scienceTask.getFullMetadata()
        oldMetadata = newMetadata.copy()
        for key in newMetadata.names(topLevelOnly=False):
            if "__version__" in key:
                oldMetadata.remove(key)

        result = self.task.run(oldMetadata)
        lsst.pipe.base.testUtils.assertValidOutput(self.task, result)
        meas = result.measurement

        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas.metric_name, self.metric)

        # Since new style is always bytes, old-style will be less or equal
        newResult = self.task.run(newMetadata)
        self.assertGreater(meas.quantity, 0.0 * u.byte)
        self.assertLessEqual(meas.quantity, newResult.measurement.quantity)

    def testDeprecated(self):
        with warnings.catch_warnings(record=True):
            self.config.metric = "verify.DummyMemory"
        self.config.connections.package = ""
        self.config.connections.metric = ""
        with warnings.catch_warnings(record=True) as emitted:
            self.config.validate()
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0].category, FutureWarning)
        self.assertEqual(self.config.connections.package, "verify")
        self.assertEqual(self.config.connections.metric, "DummyMemory")


# Hack around unittest's hacky test setup system
del MetricTaskTestCase
del MetadataMetricTestCase


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

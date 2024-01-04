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

import astropy.units as u

import lsst.utils.tests
import lsst.pipe.base.testUtils
from lsst.pex.config import Config
from lsst.pipe.base import Task
from lsst.utils.timer import timeMethod

from lsst.verify import Measurement, Name
from lsst.verify.tasks import MetricComputationError, TimingMetricTask, \
    CpuTimingMetricTask, MemoryMetricTask
from lsst.verify.tasks.testUtils import MetricTaskTestCase, MetadataMetricTestCase


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

    def testRunDifferentMethod(self):
        config = self._standardConfig()
        config.target = DummyTask._DefaultName + ".runDataRef"
        task = TimingMetricTask(config=config)
        try:
            result = task.run(self.scienceTask.getFullMetadata())
        except lsst.pipe.base.NoWorkFound:
            # Correct behavior
            pass
        else:
            # Alternative correct behavior
            lsst.pipe.base.testUtils.assertValidOutput(task, result)
            meas = result.measurement
            self.assertIsNone(meas)

    def testNonsenseKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        startKeys = [key
                     for key in metadata.paramNames(topLevelOnly=False)
                     if "StartUtc" in key]
        for key in startKeys:
            del metadata[key]

        with self.assertRaises(MetricComputationError):
            self.task.run(metadata)

    def testBadlyTypedKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        endKeys = [key
                   for key in metadata.paramNames(topLevelOnly=False)
                   if "EndUtc" in key]
        for key in endKeys:
            metadata[key] = 42

        with self.assertRaises(MetricComputationError):
            self.task.run(metadata)


class CpuTimingMetricTestSuite(MetadataMetricTestCase):
    @classmethod
    def makeTask(cls):
        return CpuTimingMetricTask(config=cls._standardConfig())

    @staticmethod
    def _standardConfig():
        config = CpuTimingMetricTask.ConfigClass()
        config.connections.labelName = DummyTask._DefaultName
        config.target = DummyTask._DefaultName + ".run"
        config.connections.package = "verify"
        config.connections.metric = "DummyCpuTime"
        return config

    def setUp(self):
        super().setUp()
        self.metric = Name("verify.DummyCpuTime")

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

        # CPU time should be less than wall-clock time.
        wallClock = TimingMetricTask(config=TimingMetricTestSuite._standardConfig())
        wallResult = wallClock.run(self.scienceTask.getFullMetadata())
        # Include 0.1% margin for almost-equal values.
        self.assertLess(meas.quantity, 1.001 * wallResult.measurement.quantity)

    def testRunDifferentMethod(self):
        config = self._standardConfig()
        config.target = DummyTask._DefaultName + ".runDataRef"
        task = CpuTimingMetricTask(config=config)
        try:
            result = task.run(self.scienceTask.getFullMetadata())
        except lsst.pipe.base.NoWorkFound:
            # Correct behavior
            pass
        else:
            # Alternative correct behavior
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

        with self.assertRaises(MetricComputationError):
            self.task.run(metadata)

    def testBadlyTypedKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        endKeys = [key
                   for key in metadata.paramNames(topLevelOnly=False)
                   if "EndCpuTime" in key]
        for key in endKeys:
            metadata[key] = str(float(metadata[key]))

        with self.assertRaises(MetricComputationError):
            self.task.run(metadata)


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

    def testRunDifferentMethod(self):
        config = self._standardConfig()
        config.target = DummyTask._DefaultName + ".runDataRef"
        task = MemoryMetricTask(config=config)
        try:
            result = task.run(self.scienceTask.getFullMetadata())
        except lsst.pipe.base.NoWorkFound:
            # Correct behavior
            pass
        else:
            # Alternative correct behavior
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

        with self.assertRaises(MetricComputationError):
            self.task.run(metadata)

    def testOldMetadata(self):
        """Test compatibility with version 0 metadata

        This can't actually test differences in unit handling between version 0
        and version 1, but at least verifies that the code didn't choke on
        old-style metadata.
        """
        newMetadata = self.scienceTask.getFullMetadata()
        oldMetadata = newMetadata.model_copy()
        for key in newMetadata.names():
            if "__version__" in key:
                del oldMetadata[key]

        result = self.task.run(oldMetadata)
        lsst.pipe.base.testUtils.assertValidOutput(self.task, result)
        meas = result.measurement

        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas.metric_name, self.metric)

        # Since new style is always bytes, old-style will be less or equal
        newResult = self.task.run(newMetadata)
        self.assertGreater(meas.quantity, 0.0 * u.byte)
        self.assertLessEqual(meas.quantity, newResult.measurement.quantity)


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

#
# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import time
import unittest

import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose

import lsst.utils.tests
from lsst.pex.config import Config
from lsst.pipe.base import Task, timeMethod

from lsst.verify import Measurement, Name
from lsst.verify.gen2tasks.testUtils import MetricTaskTestCase
from lsst.verify.tasks import MetricComputationError, TimingMetricTask
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
        config.metadata.name = DummyTask._DefaultName + "_metadata"
        config.target = DummyTask._DefaultName + ".run"
        config.metric = "verify.DummyTime"
        return config

    def setUp(self):
        """Create a dummy instance of `FringeTask` so that test cases can
        run and measure it.
        """
        super().setUp()
        self.config = TimingMetricTestSuite._standardConfig()

        self.scienceTask = DummyTask()
        self.scienceTask.run()

    def testValid(self):
        result = self.task.run([self.scienceTask.getFullMetadata()])
        meas = result.measurement

        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas.metric_name, Name(metric=self.config.metric))
        self.assertGreater(meas.quantity, 0.0 * u.second)
        self.assertLess(meas.quantity, 2 * DummyTask.taskLength * u.second)

    def testNoMetric(self):
        self.config.metric = "foo.bar.FooBarTime"
        task = TimingMetricTask(config=self.config)
        with self.assertRaises(TypeError):
            task.run([self.scienceTask.getFullMetadata()])

    def testMissingData(self):
        result = self.task.run([None])
        meas = result.measurement
        self.assertIsNone(meas)

    def testNoDataExpected(self):
        result = self.task.run([])
        meas = result.measurement
        self.assertIsNone(meas)

    def testRunDifferentMethod(self):
        self.config.target = DummyTask._DefaultName + ".runDataRef"
        task = TimingMetricTask(config=self.config)
        result = task.run([self.scienceTask.getFullMetadata()])
        meas = result.measurement
        self.assertIsNone(meas)

    def testNonsenseKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        startKeys = [key
                     for key in metadata.paramNames(topLevelOnly=False)
                     if "StartCpuTime" in key]
        for key in startKeys:
            metadata.remove(key)

        task = TimingMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run([metadata])

    def testBadlyTypedKeys(self):
        metadata = self.scienceTask.getFullMetadata()
        endKeys = [key
                   for key in metadata.paramNames(topLevelOnly=False)
                   if "EndCpuTime" in key]
        for key in endKeys:
            metadata.set(key, str(metadata.getAsDouble(key)))

        task = TimingMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run([metadata])

    def testGetInputDatasetTypes(self):
        types = TimingMetricTask.getInputDatasetTypes(self.config)
        self.assertSetEqual(set(types.keys()), {"metadata"})
        expected = DummyTask._DefaultName + "_metadata"
        self.assertEqual(types["metadata"], expected)

    def testFineGrainedMetric(self):
        metadata = self.scienceTask.getFullMetadata()
        inputData = {"metadata": [metadata]}
        inputDataIds = {"metadata": [{"visit": 42, "ccd": 1}]}
        outputDataId = {"measurement": {"visit": 42, "ccd": 1}}
        measDirect = self.task.run([metadata]).measurement
        measIndirect = self.task.adaptArgsAndRun(
            inputData, inputDataIds, outputDataId).measurement

        assert_quantity_allclose(measIndirect.quantity, measDirect.quantity)

    def testCoarseGrainedMetric(self):
        metadata = self.scienceTask.getFullMetadata()
        nCcds = 3
        inputData = {"metadata": [metadata] * nCcds}
        inputDataIds = {"metadata": [{"visit": 42, "ccd": x}
                                     for x in range(nCcds)]}
        outputDataId = {"measurement": {"visit": 42}}
        measDirect = self.task.run([metadata]).measurement
        measMany = self.task.adaptArgsAndRun(
            inputData, inputDataIds, outputDataId).measurement

        assert_quantity_allclose(measMany.quantity,
                                 nCcds * measDirect.quantity)

    def testGetOutputMetricName(self):
        self.assertEqual(TimingMetricTask.getOutputMetricName(self.config),
                         Name(self.config.metric))


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

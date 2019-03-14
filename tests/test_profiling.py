#
# This file is part of ap_verify.
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

import unittest

import numpy as np
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose

import lsst.utils.tests
import lsst.afw.image as afwImage
from lsst.ip.isr import FringeTask
from lsst.verify import Measurement, Name
from lsst.verify.gen2tasks.testUtils import MetricTaskTestCase
from lsst.verify.tasks import MetricComputationError
from lsst.verify.tasks.testUtils import MetadataMetricTestCase

from lsst.ap.verify.measurements.profiling import TimingMetricTask


def _createFringe(width, height, filterName):
    """Create a fringe frame

    Parameters
    ----------
    width, height: `int`
        Size of image
    filterName: `str`
        name of the filterName to use

    Returns
    -------
    fringe: `lsst.afw.image.ExposureF`
        Fringe frame
    """
    image = afwImage.ImageF(width, height)
    array = image.getArray()
    freq = np.pi / 10.0
    x, y = np.indices(array.shape)
    array[x, y] = np.sin(freq * x) + np.sin(freq * y)
    exp = afwImage.makeExposure(afwImage.makeMaskedImage(image))
    exp.setFilter(afwImage.Filter(filterName))
    return exp


class TimingMetricTestSuite(MetadataMetricTestCase):
    _SCIENCE_TASK_NAME = "fringe"

    @classmethod
    def makeTask(cls):
        return TimingMetricTask(config=cls._standardConfig())

    @staticmethod
    def _standardConfig():
        config = TimingMetricTask.ConfigClass()
        config.metadata.name = TimingMetricTestSuite._SCIENCE_TASK_NAME + "_metadata"
        config.target = TimingMetricTestSuite._SCIENCE_TASK_NAME + ".run"
        config.metric = "ip_isr.IsrTime"
        return config

    def setUp(self):
        """Create a dummy instance of `FringeTask` so that test cases can
        run and measure it.
        """
        super().setUp()
        self.config = TimingMetricTestSuite._standardConfig()

        # Create dummy filter and fringe so that `FringeTask` has short but
        # significant run time.
        # Code adapted from lsst.ip.isr.test_fringes
        size = 128
        dummyFilter = "FILTER"
        afwImage.utils.defineFilter(dummyFilter, lambdaEff=0)
        exp = _createFringe(size, size, dummyFilter)

        # Create and run `FringeTask` itself
        config = FringeTask.ConfigClass()
        config.filters = [dummyFilter]
        config.num = 1000
        config.small = 1
        config.large = size // 4
        config.pedestal = False
        self.scienceTask = FringeTask(name=TimingMetricTestSuite._SCIENCE_TASK_NAME, config=config)

        # As an optimization, let test cases choose whether to run the dummy task
        def runTask():
            self.scienceTask.run(exp, exp)
        self.runTask = runTask

    def tearDown(self):
        del self.scienceTask

    def testValid(self):
        self.runTask()
        result = self.task.run([self.scienceTask.getFullMetadata()])
        meas = result.measurement

        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas.metric_name, Name(metric=self.config.metric))
        self.assertGreater(meas.quantity, 0.0 * u.second)
        # Task normally takes 0.2 s, so this should be a safe margin of error
        self.assertLess(meas.quantity, 10.0 * u.second)

    def testNoMetric(self):
        self.runTask()
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
        self.runTask()
        self.config.target = TimingMetricTestSuite._SCIENCE_TASK_NAME + ".runDataRef"
        task = TimingMetricTask(config=self.config)
        result = task.run([self.scienceTask.getFullMetadata()])
        meas = result.measurement
        self.assertIsNone(meas)

    def testNonsenseKeys(self):
        self.runTask()
        metadata = self.scienceTask.getFullMetadata()
        startKeys = [key for key in metadata.paramNames(topLevelOnly=False) if "StartCpuTime" in key]
        for key in startKeys:
            metadata.remove(key)

        task = TimingMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run([metadata])

    def testBadlyTypedKeys(self):
        self.runTask()
        metadata = self.scienceTask.getFullMetadata()
        endKeys = [key for key in metadata.paramNames(topLevelOnly=False) if "EndCpuTime" in key]
        for key in endKeys:
            metadata.set(key, str(metadata.getAsDouble(key)))

        task = TimingMetricTask(config=self.config)
        with self.assertRaises(MetricComputationError):
            task.run([metadata])

    def testGetInputDatasetTypes(self):
        types = TimingMetricTask.getInputDatasetTypes(self.config)
        # dict.keys() is a collections.abc.Set, which has a narrower interface than __builtins__.set...
        self.assertSetEqual(set(types.keys()), {"metadata"})
        self.assertEqual(types["metadata"], TimingMetricTestSuite._SCIENCE_TASK_NAME + "_metadata")

    def testFineGrainedMetric(self):
        self.runTask()
        metadata = self.scienceTask.getFullMetadata()
        inputData = {"metadata": [metadata]}
        inputDataIds = {"metadata": [{"visit": 42, "ccd": 1}]}
        outputDataId = {"measurement": {"visit": 42, "ccd": 1}}
        measDirect = self.task.run([metadata]).measurement
        measIndirect = self.task.adaptArgsAndRun(inputData, inputDataIds, outputDataId).measurement

        assert_quantity_allclose(measIndirect.quantity, measDirect.quantity)

    def testCoarseGrainedMetric(self):
        self.runTask()
        metadata = self.scienceTask.getFullMetadata()
        nCcds = 3
        inputData = {"metadata": [metadata] * nCcds}
        inputDataIds = {"metadata": [{"visit": 42, "ccd": x} for x in range(nCcds)]}
        outputDataId = {"measurement": {"visit": 42}}
        measDirect = self.task.run([metadata]).measurement
        measMany = self.task.adaptArgsAndRun(inputData, inputDataIds, outputDataId).measurement

        assert_quantity_allclose(measMany.quantity, nCcds * measDirect.quantity)

    def testGetOutputMetricName(self):
        self.assertEqual(TimingMetricTask.getOutputMetricName(self.config), Name(self.config.metric))


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

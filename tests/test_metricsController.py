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

import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose

import lsst.utils.tests
from lsst.daf.persistence import ButlerDataRef
from lsst.afw.cameraGeom import Camera
from lsst.pipe.base import Struct
from lsst.verify import Job, MetricComputationError
from lsst.verify.compatibility import MetricTask, MetricsControllerTask


def _metricName():
    """The metric to be hypothetically measured using the mock task.
    """
    return "misc_tasks.FancyMetric"


# TODO: can be replaced with a vanilla mock after DM-16642
def _makeMockDataref(_datasetType, dataId=None):
    """A dataref-like object that returns a mock camera.
    """
    camera = unittest.mock.NonCallableMock(
        Camera, autospec=True, **{"getName.return_value": "fancyCam"})
    return unittest.mock.NonCallableMock(
        ButlerDataRef, autospec=True, **{"get.return_value": camera},
        dataId=dataId)


def _butlerQuery(_butler, datasetType, _level="", dataId=None):
    """Return a number of datarefs corresponding to a (partial) dataId.
    """
    dataref = _makeMockDataref(datasetType)

    # Simulate a dataset of 3 visits and 2 CCDs
    nRuns = 1
    if "visit" not in dataId:
        nRuns *= 3
    if "ccd" not in dataId:
        nRuns *= 2
    return [dataref] * nRuns


@unittest.mock.patch.object(Job, "load_metrics_package", side_effect=Job)
@unittest.mock.patch("lsst.daf.persistence.searchDataRefs", autospec=True,
                     side_effect=_butlerQuery)
@unittest.mock.patch("lsst.verify.Job.write", autospec=True)
class MetricsControllerTestSuite(lsst.utils.tests.TestCase):

    def setUp(self):
        self.task = MetricsControllerTask()

        self.metricTask = unittest.mock.create_autospec(
            MetricTask, instance=True)
        self.task.measurers = [self.metricTask]
        # For some reason can't set these in create_autospec call
        self.metricTask.config = None
        self.metricTask.getInputDatasetTypes.return_value = \
            {"input": "metadata"}

        def returnMeasurement(inputData, _inputDataIds, _outputDataIds):
            nData = len(inputData["input"])
            return Struct(measurement=lsst.verify.Measurement(
                _metricName(), nData * u.second))
        self.metricTask.adaptArgsAndRun.side_effect = returnMeasurement

    def _checkMetric(self, mockWriter, datarefs, unitsOfWork):
        """Standardized test battery for running a timing metric.

        Parameters
        ----------
        mockWriter : `unittest.mock.CallableMock`
            A queriable placeholder for `lsst.verify.Job.write`.
        datarefs : `list` of `lsst.daf.persistence.ButlerDataRef`
            The inputs to `MetricsControllerTask.runDataRefs`.
        unitsOfWork : `list` of `int`
            The number of science pipeline units of work (i.e., CCD-visit
            pairs) that should be combined to make a metric for each element
            of ``datarefs``.
        """
        if len(datarefs) != len(unitsOfWork):
            raise ValueError("Test requires matching datarefs "
                             "and unitsOfWork")

        jobs = self.task.runDataRefs(datarefs).jobs
        self.assertEqual(len(jobs), len(datarefs))
        for job, dataref, nTimings in zip(jobs, datarefs, unitsOfWork):
            self.assertEqual(len(job.measurements), 1)
            assert_quantity_allclose(
                job.measurements[_metricName()].quantity,
                float(nTimings) * u.second)
            self.assertEqual(job.meta["instrument"], "FANCYCAM")
            for key in dataref.dataId:
                self.assertEqual(job.meta[key], dataref.dataId[key])

        # Exact arguments to Job.write are implementation detail, don't test
        if not jobs:
            mockWriter.assert_not_called()
        elif len(jobs) == 1:
            mockWriter.assert_called_once()
        else:
            mockWriter.assert_called()

    def testCcdGrainedMetric(self, mockWriter, _mockButler,
                             _mockMetricsLoader):
        dataId = {"visit": 42, "ccd": 101, "filter": "k"}
        datarefs = [_makeMockDataref("calexp", dataId=dataId)]
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[1])

    def testVisitGrainedMetric(self, mockWriter, _mockButler,
                               _mockMetricsLoader):
        dataId = {"visit": 42, "filter": "k"}
        datarefs = [_makeMockDataref("calexp", dataId=dataId)]
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[2])

    def testDatasetGrainedMetric(self, mockWriter, _mockButler,
                                 _mockMetricsLoader):
        dataId = {}
        datarefs = [_makeMockDataref("calexp", dataId=dataId)]
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[6])

    def testMultipleMetrics(self, mockWriter, _mockButler,
                            _mockMetricsLoader):
        dataIds = [{"visit": 42, "ccd": 101, "filter": "k"},
                   {"visit": 42, "ccd": 102, "filter": "k"}]
        datarefs = [_makeMockDataref("calexp", dataId=dataId)
                    for dataId in dataIds]
        self._checkMetric(mockWriter, datarefs,
                          unitsOfWork=[1] * len(dataIds))

    def testInvalidMetricSegregation(self, _mockWriter, _mockButler,
                                     _mockMetricsLoader):
        self.metricTask.adaptArgsAndRun.side_effect = (
            MetricComputationError, unittest.mock.DEFAULT)
        self.metricTask.adaptArgsAndRun.return_value = Struct(
            measurement=lsst.verify.Measurement(_metricName(),
                                                1.0 * u.second))

        dataIds = [{"visit": 42, "ccd": 101, "filter": "k"},
                   {"visit": 42, "ccd": 102, "filter": "k"}]
        datarefs = [_makeMockDataref("calexp", dataId=dataId)
                    for dataId in dataIds]

        jobs = self.task.runDataRefs(datarefs).jobs
        self.assertEqual(len(jobs), len(datarefs))

        self.assertEqual(len(jobs[0].measurements), 0)
        for job in jobs:
            self.assertEqual(job.meta["instrument"], "FANCYCAM")
        for job in jobs[1:]:
            self.assertEqual(len(job.measurements), 1)
            assert_quantity_allclose(
                job.measurements[_metricName()].quantity,
                float(1.0) * u.second)

    def testNoData(self, mockWriter, _mockButler, _mockMetricsLoader):
        datarefs = []
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[])


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

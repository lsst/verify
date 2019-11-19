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
from lsst.pex.config import Config, FieldValidationError
from lsst.pipe.base import \
    Task, Struct, PipelineTaskConnections, connectionTypes
from lsst.verify import Job, Name, Measurement
from lsst.verify.tasks import MetricTask, MetricComputationError
from lsst.verify.gen2tasks import \
    MetricsControllerTask, register, registerMultiple


def _metricName():
    return "misc_tasks.FancyMetric"


def _extraMetricName1():
    return "misc_tasks.SuperfluousMetric"


def _extraMetricName2():
    return "misc_tasks.RedundantMetric"


class DemoConnections(
        PipelineTaskConnections,
        dimensions={}):
    inputData = connectionTypes.Input(
        name="metadata",
        storageClass="PropertySet",
    )


class DemoMetricConfig(MetricTask.ConfigClass,
                       pipelineConnections=DemoConnections):
    metric = lsst.pex.config.Field(
        dtype=str,
        default=_metricName(),
        doc="Metric to target")
    multiplier = lsst.pex.config.Field(
        dtype=float,
        default=1.0,
        doc="Arbitrary factor for measurement")


@register("demoMetric")
class _DemoMetricTask(MetricTask):
    """A minimal `lsst.verify.tasks.MetricTask`.
    """

    ConfigClass = DemoMetricConfig
    _DefaultName = "test"

    def run(self, inputData):
        nData = len(inputData)
        return Struct(measurement=Measurement(
            self.getOutputMetricName(self.config),
            self.config.multiplier * nData * u.second))

    @classmethod
    def getInputDatasetTypes(cls, _config):
        return {'inputData': "metadata"}

    @classmethod
    def areInputDatasetsScalar(cls, _config):
        return {'inputData': False}

    @classmethod
    def getOutputMetricName(cls, config):
        return Name(config.metric)


@registerMultiple("repeatedMetric")
class _RepeatedMetricTask(MetricTask):
    """A minimal `lsst.verify.tasks.MetricTask`.
    """

    ConfigClass = DemoMetricConfig
    _DefaultName = "test"

    def run(self, inputData):
        nData = len(inputData)
        return Struct(measurement=Measurement(
            self.getOutputMetricName(self.config),
            self.config.multiplier * nData * u.second))

    @classmethod
    def getInputDatasetTypes(cls, _config):
        return {'inputData': "metadata"}

    @classmethod
    def areInputDatasetsScalar(cls, _config):
        return {'inputData': False}

    @classmethod
    def getOutputMetricName(cls, config):
        return Name(config.metric)


def _makeMockDataref(dataId=None):
    """A dataref-like object with a specific data ID.
    """
    return unittest.mock.NonCallableMock(dataId=dataId)


class _TestMetadataAdder(Task):
    """Simplest valid non-identity metadata adder.
    """
    ConfigClass = Config

    def run(self, job, **kwargs):
        job.meta["tested"] = True
        return Struct(job=job)


def _butlerQuery(_butler, _datasetType, _level="", dataId=None):
    """Return a number of datarefs corresponding to a (partial) dataId.
    """
    dataref = _makeMockDataref()

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
        self.config = MetricsControllerTask.ConfigClass()
        self.config.metadataAdder.retarget(_TestMetadataAdder)
        self.config.measurers = ["demoMetric", "repeatedMetric"]

        self.config.measurers["demoMetric"].multiplier = 2.0
        repeated = self.config.measurers["repeatedMetric"]
        repeated.configs["first"] = DemoMetricConfig()
        repeated.configs["first"].metric = _extraMetricName1()
        repeated.configs["second"] = DemoMetricConfig()
        repeated.configs["second"].metric = _extraMetricName2()
        repeated.configs["second"].multiplier = 3.4

        self.task = MetricsControllerTask(self.config)

    def _allMetricTaskConfigs(self):
        configs = []
        for name, topConfig in zip(self.config.measurers.names,
                                   self.config.measurers.active):
            if name != "repeatedMetric":
                configs.append(topConfig)
            else:
                configs.extend(topConfig.configs.values())
        return configs

    def _checkMetric(self, mockWriter, datarefs, unitsOfWork):
        """Standardized test battery for running a metric.

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
            taskConfigs = self._allMetricTaskConfigs()
            self.assertEqual(len(job.measurements), len(taskConfigs))
            for metricName, metricConfig in zip(job.measurements, taskConfigs):
                self.assertEqual(metricName, Name(metricConfig.metric))
                assert_quantity_allclose(
                    job.measurements[metricConfig.metric].quantity,
                    metricConfig.multiplier * float(nTimings) * u.second)

            self.assertTrue(job.meta["tested"])

        # Exact arguments to Job.write are implementation detail, don't test
        if not jobs:
            mockWriter.assert_not_called()
        elif len(jobs) == 1:
            mockWriter.assert_called_once()
        else:
            self.assertEqual(mockWriter.call_count, len(jobs))

    def testCcdGrainedMetric(self, mockWriter, _mockButler,
                             _mockMetricsLoader):
        dataId = {"visit": 42, "ccd": 101, "filter": "k"}
        datarefs = [_makeMockDataref(dataId)]
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[1])

    def testVisitGrainedMetric(self, mockWriter, _mockButler,
                               _mockMetricsLoader):
        dataId = {"visit": 42, "filter": "k"}
        datarefs = [_makeMockDataref(dataId)]
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[2])

    def testDatasetGrainedMetric(self, mockWriter, _mockButler,
                                 _mockMetricsLoader):
        dataId = {}
        datarefs = [_makeMockDataref(dataId)]
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[6])

    def testMultipleMetrics(self, mockWriter, _mockButler,
                            _mockMetricsLoader):
        dataIds = [{"visit": 42, "ccd": 101, "filter": "k"},
                   {"visit": 42, "ccd": 102, "filter": "k"}]
        datarefs = [_makeMockDataref(dataId) for dataId in dataIds]
        self._checkMetric(mockWriter, datarefs,
                          unitsOfWork=[1] * len(dataIds))

    def testSkippedMetrics(self, mockWriter, _mockButler, _mockMetricsLoader):
        dataIds = [{"visit": 42, "ccd": 101, "filter": "k"},
                   {"visit": 42, "ccd": 102, "filter": "k"}]
        datarefs = [_makeMockDataref(dataId) for dataId in dataIds]

        with unittest.mock.patch("os.path.isfile", side_effect=[True, False]):
            jobs = self.task.runDataRefs(datarefs).jobs
            self.assertEqual(len(jobs), 2)
            self.assertEqual(mockWriter.call_count, 2)

        mockWriter.reset_mock()

        with unittest.mock.patch("os.path.isfile", side_effect=[True, False]):
            jobs = self.task.runDataRefs(datarefs, skipExisting=True).jobs
            self.assertEqual(len(jobs), 1)
            mockWriter.assert_called_once()

    def testInvalidMetricSegregation(self, _mockWriter, _mockButler,
                                     _mockMetricsLoader):
        self.config.measurers = ["demoMetric"]
        self.task = MetricsControllerTask(self.config)
        with unittest.mock.patch.object(_DemoMetricTask,
                                        "adaptArgsAndRun") as mockCall:
            # Run _DemoMetricTask twice, with one failure and one result
            mockCall.side_effect = (MetricComputationError,
                                    unittest.mock.DEFAULT)
            expectedValue = 1.0 * u.second
            mockCall.return_value = Struct(measurement=lsst.verify.Measurement(
                _metricName(), expectedValue))

            dataIds = [{"visit": 42, "ccd": 101, "filter": "k"},
                       {"visit": 42, "ccd": 102, "filter": "k"}]
            datarefs = [_makeMockDataref(dataId) for dataId in dataIds]

            jobs = self.task.runDataRefs(datarefs).jobs
            self.assertEqual(len(jobs), len(datarefs))

            # Failed job
            self.assertEqual(len(jobs[0].measurements), 0)

            # Successful job
            self.assertTrue(jobs[1].meta["tested"])
            self.assertEqual(len(jobs[1].measurements), 1)
            assert_quantity_allclose(
                jobs[1].measurements[_metricName()].quantity,
                expectedValue)

    def testNoData(self, mockWriter, _mockButler, _mockMetricsLoader):
        datarefs = []
        self._checkMetric(mockWriter, datarefs, unitsOfWork=[])

    def testBadMetric(self, _mockWriter, _mockButler, _mockMetricsLoader):
        with self.assertRaises(FieldValidationError):
            self.config.measurers = ["totallyAndDefinitelyNotARealMetric"]

    def testCustomMetadata(self, _mockWriter, _mockButler, _mockMetricsLoader):
        dataIds = [{"visit": 42, "ccd": 101, "filter": "k"},
                   {"visit": 42, "ccd": 102, "filter": "k"}]
        datarefs = [_makeMockDataref(dataId) for dataId in dataIds]
        extraMetadata = {"test_protocol": 42}
        jobs = self.task.runDataRefs(datarefs, extraMetadata).jobs

        for job in jobs:
            self.assertTrue(job.meta["tested"])
            self.assertEqual(job.meta["test_protocol"],
                             extraMetadata["test_protocol"])


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

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

__all__ = ["MetadataMetricTestCase", "ApdbMetricTestCase"]

import abc

import unittest.mock
from unittest.mock import patch

import lsst.utils.tests
import lsst.pex.config as pexConfig
from lsst.pipe.base import TaskMetadata
from lsst.dax.apdb import ApdbConfig

from lsst.verify.tasks import MetricComputationError


class MetricTaskTestCase(lsst.utils.tests.TestCase, metaclass=abc.ABCMeta):
    """Unit test base class for tests of `tasks.MetricTask`.

    This class provides tests of the generic ``MetricTask`` API. Subclasses
    must override `makeTask`, and may add extra tests for class-specific
    functionality. If subclasses override `setUp`, they must call
    `MetricTaskTestCase.setUp`.
    """
    @classmethod
    @abc.abstractmethod
    def makeTask(cls):
        """Construct the task to be tested.

        This overridable method will be called during test setup.

        Returns
        -------
        task : `lsst.verify.tasks.MetricTask`
            A new MetricTask object to test.
        """

    task = None
    """The ``MetricTask`` being tested by this object
    (`tasks.MetricTask`).

    This attribute is initialized automatically.
    """

    taskClass = None
    """The type of `task` (`tasks.MetricTask`-type).

    This attribute is initialized automatically.
    """

    def setUp(self):
        """Setup common to all MetricTask tests.

        Notes
        -----
        This implementation calls `makeTask`, then initializes `task`
        and `taskClass`.
        """
        self.task = self.makeTask()
        self.taskClass = type(self.task)

    def testOutputDatasetName(self):
        config = self.task.config
        connections = config.connections.ConnectionsClass(config=config)
        dataset = connections.measurement.name

        self.assertTrue(dataset.startswith("metricvalue_"))
        self.assertNotIn(".", dataset)

        self.assertIn(config.connections.package, dataset)
        self.assertIn(config.connections.metric, dataset)

    def testConfigValidation(self):
        config = self.task.config
        config.connections.metric = "verify.DummyMetric"
        with self.assertRaises(ValueError):
            config.validate()


class MetadataMetricTestCase(MetricTaskTestCase):
    """Unit test base class for tests of `MetadataMetricTask`.

    Notes
    -----
    Subclasses must override
    `~lsst.verify.tasks.MetricTaskTestCase.makeTask` for the concrete task
    being tested.
    """

    @staticmethod
    def _takesScalarMetadata(task):
        connections = task.config.connections.ConnectionsClass(config=task.config)
        return not connections.metadata.multiple

    def testValidRun(self):
        """Test how run delegates to the abstract methods.
        """
        mockKey = "unitTestKey"
        with patch.object(self.task, "getInputMetadataKeys",
                          return_value={"unused": mockKey}), \
                patch.object(self.task, "makeMeasurement") as mockWorkhorse:
            if self._takesScalarMetadata(self.task):
                metadata1 = TaskMetadata()
                metadata1[mockKey] = 42

                self.task.run(metadata1)
                mockWorkhorse.assert_called_once_with({"unused": 42})
            else:
                metadata1 = TaskMetadata()
                metadata1[mockKey] = 42
                metadata2 = TaskMetadata()
                metadata2[mockKey] = "Sphere"
                self.task.run([metadata1, metadata2])
                mockWorkhorse.assert_called_once_with(
                    [{"unused": value} for value in [42, "Sphere"]])

    def testAmbiguousRun(self):
        mockKey = "unitTestKey"
        with patch.object(self.task, "getInputMetadataKeys",
                          return_value={"unused": mockKey}):
            metadata = TaskMetadata()
            metadata[mockKey + "1"] = 42
            metadata[mockKey + "2"] = "Sphere"
            with self.assertRaises(MetricComputationError):
                if self._takesScalarMetadata(self.task):
                    self.task.run(metadata)
                else:
                    self.task.run([metadata])

    def testPassThroughRun(self):
        with patch.object(self.task, "makeMeasurement",
                          side_effect=MetricComputationError):
            metadata1 = TaskMetadata()
            metadata1["unitTestKey"] = 42
            with self.assertRaises(MetricComputationError):
                if self._takesScalarMetadata(self.task):
                    self.task.run(metadata1)
                else:
                    self.task.run([metadata1])

    def testDimensionsOverride(self):
        config = self.task.config
        expectedDimensions = {"instrument", "visit"}
        config.metadataDimensions = expectedDimensions

        connections = config.connections.ConnectionsClass(config=config)
        self.assertSetEqual(set(connections.dimensions),
                            expectedDimensions)
        self.assertIn(connections.metadata,
                      connections.allConnections.values())
        self.assertSetEqual(set(connections.metadata.dimensions),
                            expectedDimensions)


class ApdbMetricTestCase(MetricTaskTestCase):
    """Unit test base class for tests of `ApdbMetricTask`.

    Notes
    -----
    Subclasses must override
    `~lsst.verify.tasks.MetricTaskTestCase.makeTask` for the concrete task
    being tested. Subclasses that use a custom DbLoader should also
    override `makeDbInfo`.
    """

    @classmethod
    def makeDbInfo(cls):
        """Return an object that can be passed as input to an `ApdbMetricTask`.

        This method is intended for generic tests that simply need to call
        ``run`` on some valid input. If a test depends on specific input, it
        should create that input directly.

        The default implementation creates a `~lsst.pex.config.Config` that
        will be accepted by `~lsst.verify.tasks.DirectApdbLoader`. Test suites
        that use a different loader should override this method.
        """
        return ApdbConfig()

    def testValidRun(self):
        info = self.makeDbInfo()
        with patch.object(self.task, "makeMeasurement") as mockWorkhorse:
            self.task.run([info])
            mockWorkhorse.assert_called_once()

    def testDataIdRun(self):
        info = self.makeDbInfo()
        with patch.object(self.task, "makeMeasurement") as mockWorkhorse:
            dataId = {'visit': 42}
            self.task.run([info], outputDataId=dataId)
            mockWorkhorse.assert_called_once_with(
                unittest.mock.ANY, {'visit': 42})

    def testPassThroughRun(self):
        with patch.object(self.task, "makeMeasurement",
                          side_effect=MetricComputationError):
            info = self.makeDbInfo()
            with self.assertRaises(MetricComputationError):
                self.task.run([info])

    # TODO: remove on DM-43419
    def testConfigApdbRead(self):
        config = self.taskClass.ConfigClass()
        with self.assertWarns(FutureWarning):
            config.doReadMarker = True
            config.freeze()
            config.validate()

    # TODO: remove on DM-43419
    def testConfigApdbFileOk(self):
        config = self.taskClass.ConfigClass()
        config.doReadMarker = False
        config.apdb_config_url = "some/file/path.yaml"
        config.freeze()
        config.validate()

    # TODO: remove on DM-43419
    def testConfigApdbFileInvalid(self):
        config = self.taskClass.ConfigClass()
        config.doReadMarker = False
        # Don't set apdb_config_url
        config.freeze()
        with self.assertRaises(pexConfig.FieldValidationError):
            config.validate()

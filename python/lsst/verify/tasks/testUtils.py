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

__all__ = ["MetadataMetricTestCase", "PpdbMetricTestCase"]

from unittest.mock import patch

from lsst.pex.config import Config, ConfigField
from lsst.daf.base import PropertySet
from lsst.dax.ppdb import PpdbConfig

from lsst.verify.gen2tasks.testUtils import MetricTaskTestCase
from lsst.verify.tasks import MetricComputationError


class MetadataMetricTestCase(MetricTaskTestCase):
    """Unit test base class for tests of `MetadataMetricTask`.

    Notes
    -----
    Subclasses must override
    `~lsst.verify.gen2tasks.MetricTaskTestCase.makeTask` for the concrete task
    being tested.
    """

    def testInputDatasetTypes(self):
        defaultInputs = self.taskClass.getInputDatasetTypes(self.task.config)
        self.assertEqual(defaultInputs.keys(), {"metadata"})

    @staticmethod
    def _takesScalarMetadata(task):
        return task.areInputDatasetsScalar(task.config)['metadata']

    def testValidRun(self):
        """Test how run delegates to the abstract methods.
        """
        mockKey = "unitTestKey"
        with patch.object(self.task, "getInputMetadataKeys",
                          return_value={"unused": mockKey}), \
                patch.object(self.task, "makeMeasurement") as mockWorkhorse:
            if self._takesScalarMetadata(self.task):
                metadata1 = PropertySet()
                metadata1[mockKey] = 42

                self.task.run(metadata1)
                mockWorkhorse.assert_called_once_with({"unused": 42})
                mockWorkhorse.reset_mock()
                self.task.run(None)
                mockWorkhorse.assert_called_once_with({"unused": None})
            else:
                metadata1 = PropertySet()
                metadata1[mockKey] = 42
                metadata2 = PropertySet()
                metadata2[mockKey] = "Sphere"
                self.task.run([metadata1, None, metadata2])
                mockWorkhorse.assert_called_once_with(
                    [{"unused": value} for value in [42, None, "Sphere"]])

    def testAmbiguousRun(self):
        mockKey = "unitTestKey"
        with patch.object(self.task, "getInputMetadataKeys",
                          return_value={"unused": mockKey}):
            metadata = PropertySet()
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
            with self.assertRaises(MetricComputationError):
                if self._takesScalarMetadata(self.task):
                    self.task.run(None)
                else:
                    self.task.run([None])


class DummyConfig(Config):
    ppdb = ConfigField(dtype=PpdbConfig, doc="Mandatory field")


class PpdbMetricTestCase(MetricTaskTestCase):
    """Unit test base class for tests of `PpdbMetricTask`.

    Notes
    -----
    Subclasses must override
    `~lsst.verify.gen2tasks.MetricTaskTestCase.makeTask` for the concrete task
    being tested.
    """

    def testInputDatasetTypes(self):
        defaultInputs = self.taskClass.getInputDatasetTypes(self.task.config)
        self.assertEqual(defaultInputs.keys(), {"dbInfo"})

    def testValidRun(self):
        config = DummyConfig()
        with patch.object(self.task, "makeMeasurement") \
                as mockWorkhorse:
            self.task.run(config)
            mockWorkhorse.assert_called_once()

    def testPassThroughRun(self):
        with patch.object(self.task, "makeMeasurement",
                          side_effect=MetricComputationError):
            config = DummyConfig()
            with self.assertRaises(MetricComputationError):
                self.task.run(config)

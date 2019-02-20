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

__all__ = ["MetricTaskTestCase"]

import abc
import unittest.mock
import inspect

import lsst.utils.tests

from lsst.pipe.base import Struct
from lsst.verify import Measurement


class MetricTaskTestCase(lsst.utils.tests.TestCase, metaclass=abc.ABCMeta):
    """Unit test base class for tests of `gen2tasks.MetricTask`.

    This class provides tests of the generic ``MetricTask`` API. Subclasses
    must override `taskFactory`, and may add extra tests for class-specific
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
        task : `lsst.verify.gen2tasks.MetricTask`
            A new MetricTask object to test.
        """

    task = None
    """The ``MetricTask`` being tested by this object
    (`gen2tasks.MetricTask`).

    This attribute is initialized automatically.
    """

    taskClass = None
    """The type of `task` (`gen2tasks.MetricTask`-type).

    This attribute is initialized automatically.
    """

    def setUp(self):
        """Setup common to all MetricTask tests.

        Notes
        -----
        This implementation calls `taskFactory`, then initializes `task`
        and `taskClass`.
        """
        self.task = self.makeTask()
        self.taskClass = type(self.task)

    # Implementation classes will override run or adaptArgsAndRun. Can't
    # implement most tests if they're mocked, risk excessive runtime if
    # they aren't.

    def testInputDatasetTypesKeys(self):
        defaultInputs = self.taskClass.getInputDatasetTypes(self.task.config)
        runParams = inspect.signature(self.taskClass.run).parameters

        # Only way to check if run has been overridden?
        if runParams.keys() != ['kwargs']:
            self.assertSetEqual(
                set(defaultInputs.keys()).union({'self'}),
                set(runParams.keys()).union({'self'}),
                "getInputDatasetTypes keys do not match run parameters")

    def testAddStandardMetadata(self):
        measurement = Measurement('foo.bar', 0.0)
        dataId = {'tract': 42, 'patch': 3, 'filter': 'Ic'}
        self.task.addStandardMetadata(measurement, dataId)
        # Nothing to test until addStandardMetadata adds something

    def testCallAddStandardMetadata(self):
        dummy = Measurement('foo.bar', 0.0)
        with unittest.mock.patch.multiple(
                self.taskClass, autospec=True,
                run=unittest.mock.DEFAULT,
                addStandardMetadata=unittest.mock.DEFAULT) as mockDict:
            mockDict['run'].return_value = Struct(measurement=dummy)

            inputTypes = self.taskClass.getInputDatasetTypes(self.task.config)
            inputParams = inputTypes.keys()
            # Probably won't satisfy all adaptArgsAndRun specs,
            # but hopefully works with most of them
            dataId = {}
            result = self.task.adaptArgsAndRun(
                {key: [None] for key in inputParams},
                {key: [dataId] for key in inputParams},
                {'measurement': {}})
            mockDict['addStandardMetadata'].assert_called_once_with(
                self.task, result.measurement, dataId)

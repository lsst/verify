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

import unittest

import lsst.utils.tests

from lsst.verify.gen2tasks import register, registerMultiple
from lsst.verify.gen2tasks.metricRegistry import MetricRegistry
from lsst.verify.tasks import MetricTask


class MetricRegistryTestSuite(lsst.utils.tests.TestCase):
    @classmethod
    def setUpClass(cls):
        # Remember the implementation class of the registry for later use
        cls.RegistryClass = type(MetricRegistry.registry)

    def setUp(self):
        # Clear out old registry by replacing it
        MetricRegistry.registry = self.RegistryClass()

    def testRegistration(self):
        @register("foo")
        class DummyMetricTask(MetricTask):
            pass

        self.assertIn("foo", MetricRegistry.registry)
        self.assertEqual(MetricRegistry.registry["foo"], DummyMetricTask)

    def testMultiRegistration(self):
        @registerMultiple("foo")
        class DummyMetricTask(MetricTask):
            pass

        self.assertIn("foo", MetricRegistry.registry)
        # Type of registry entry is implementation detail; functionality better
        # tested in test_metricsController

    def testInvalidRegistration(self):
        with self.assertRaises(ValueError):
            @register("bar")
            class NotAMetricTask:
                pass

    def testInvalidMultiRegistration(self):
        with self.assertRaises(RuntimeError):
            @register("foo")
            @registerMultiple("foo")
            class DummyMetricTask(MetricTask):
                pass


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

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

from lsst.verify import Measurement, Metric, Name
from lsst.verify.timer import time_this_to_measurement


class TimeThisTestSuite(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.metric_name = Name("verify.DummyTime")

    def test_basic(self):
        duration = 0.2
        meas = Measurement(self.metric_name)
        with time_this_to_measurement(meas):
            time.sleep(duration)

        self.assertEqual(meas.metric_name, self.metric_name)  # Should not have changed
        self.assertIsNotNone(meas.quantity)
        self.assertGreater(meas.quantity, duration * u.second)
        self.assertLess(meas.quantity, 2 * duration * u.second)

    def test_unit_checking_ok(self):
        duration = 0.2
        metric = Metric(self.metric_name, "Unconventional metric", u.nanosecond)
        meas = Measurement(metric)
        with time_this_to_measurement(meas):
            time.sleep(duration)

        self.assertEqual(meas.metric_name, self.metric_name)  # Should not have changed
        self.assertIsNotNone(meas.quantity)
        self.assertGreater(meas.quantity, duration * u.second)
        self.assertLess(meas.quantity, 2 * duration * u.second)

    def test_unit_checking_bad(self):
        duration = 0.2
        metric = Metric(self.metric_name, "Non-temporal metric", u.meter / u.second)
        meas = Measurement(metric)
        with self.assertRaises(TypeError):
            with time_this_to_measurement(meas):
                time.sleep(duration)

    def test_exception(self):
        duration = 0.2
        meas = Measurement(self.metric_name)
        try:
            with time_this_to_measurement(meas):
                time.sleep(duration)
                raise RuntimeError("Something went wrong!")
        except RuntimeError:
            pass

        self.assertEqual(meas.metric_name, self.metric_name)  # Should not have changed
        self.assertIsNotNone(meas.quantity)
        self.assertGreater(meas.quantity, duration * u.second)
        self.assertLess(meas.quantity, 2 * duration * u.second)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()

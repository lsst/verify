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

import contextlib
import io
import os
import unittest

import lsst.daf.butler
from lsst.verify import extract_metricvalues


class ExtractMetricvaluesTest(unittest.TestCase):
    """Tests of methods in extract_metricvalues.py that are called by the
    commandline interface.

    These tests use the two repos created by
    ``data/make_metricvalue_butlers.py``
    """
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), "data")
        self.repo1 = os.path.join(path, "metricvalue_repo1")
        self.repo2 = os.path.join(path, "metricvalue_repo2")

    def test_load_from_butler(self):
        butler = lsst.daf.butler.Butler(self.repo1, collections="testrun")

        result = extract_metricvalues.load_from_butler(butler, "metricvalue_verify_other*")
        self.assertEqual(len(result), 2)
        for value in result.values():
            self.assertEqual(value.metric_name.metric, "other")

        # Check that reject_suffix correctly restricts the list.
        result = extract_metricvalues.load_from_butler(butler, "metricvalue_verify_testing*",
                                                       reject_suffix="Time")
        self.assertEqual(len(result), 5)
        for value in result.values():
            self.assertNotIn("Time", value.metric_name.metric)

        # Check that reject suffix behaves correctly with tuples.
        result = extract_metricvalues.load_from_butler(butler, "metricvalue_verify_testing*",
                                                       reject_suffix=("Time", "ing"))
        self.assertEqual(len(result.keys()), 2)
        for value in result.values():
            self.assertNotIn("Time", value.metric_name.metric)
            self.assertNotIn("Objects", value.metric_name.metric)
            self.assertIn("Memory", value.metric_name.metric)

        # Check that we can reject everything.
        result = extract_metricvalues.load_from_butler(butler, "metricvalue_verify_testing*",
                                                       reject_suffix=("Time", "ing", "Memory"))
        self.assertEqual(len(result.keys()), 0)

    def test_load_value(self):
        butler = lsst.daf.butler.Butler(self.repo1, collections="testrun")

        result = extract_metricvalues.load_value(butler)
        self.assertEqual(len(result.keys()), 6)
        for value in result.values():
            self.assertNotIn("Time", value.metric_name.metric)
            self.assertNotIn("Memory", value.metric_name.metric)

    def test_load_timing(self):
        butler = lsst.daf.butler.Butler(self.repo1, collections="testrun")

        result = extract_metricvalues.load_timing(butler)
        self.assertEqual(len(result.keys()), 4)
        for value in result.values():
            self.assertIn("Time", value.metric_name.metric)

    def test_load_memory(self):
        butler = lsst.daf.butler.Butler(self.repo1, collections="testrun")

        result = extract_metricvalues.load_memory(butler)
        self.assertEqual(len(result.keys()), 4)
        for value in result.values():
            self.assertIn("Memory", value.metric_name.metric)

    def test_print_metrics(self):
        """Test what is printed to stdout for various ``print_metrics`` args.
        """
        butler = lsst.daf.butler.Butler(self.repo1, collections="testrun")

        def check_stdout(kind, n, last_line, contained, **kwargs):
            """Test the the correct number of lines are printed, and that
            the last line is as expected.

            Parameters
            ----------
            kind : `str`
                What kind of metrics to load; passed to ``print_metrics()``.
            n : `int`
                How many non-empty lines should have been printed?
            last_line : `str`
                Expected last non-empty line in the printed output.
            contained : `str`
                A full-line string expected to be contained in the output.
            **kwargs
                Other arguments to pass to ``print_metrics()``.
            """
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                extract_metricvalues.print_metrics(butler, kind, **kwargs)
                # Split up the lines, and remove empty ones.
                result = list(filter(None, stdout.getvalue().split("\n")))
                self.assertEqual(len(result), n)
                self.assertEqual(last_line, result[-1])
                self.assertIn(contained, result)

        # default call with no kwargs
        contained = "{instrument: 'TestCam', detector: 25, visit: 54321, ...}"
        last = "verify.testing: 42.0"
        check_stdout("value", 9, last, contained)

        # restrict the number of items returned to only the last detector
        check_stdout("value", 3, last, contained, data_id_restriction={"detector": 25})

        # only print part of the dataIds
        contained = "detector: 25, visit: 54321"
        check_stdout("value", 9, last, contained, data_id_keys=("detector", "visit"))

        # Get the timings instead
        contained = "{instrument: 'TestCam', detector: 25, visit: 54321, ...}"
        last = "verify.testingTime: 19.0 s"
        check_stdout("timing", 6, last, contained)

        # Get the timings and print a partial dataId
        contained = "detector: 25, visit: 54321"
        check_stdout("timing", 6, last, contained, data_id_keys=("detector", "visit"))

        # Get the memory values instead
        contained = "{instrument: 'TestCam', detector: 25, visit: 54321, ...}"
        last = "verify.testingMemory: 190.73 Mibyte"
        check_stdout("memory", 6, last, contained)

        # Get the memory values and print a partial dataId
        contained = "detector: 25, visit: 54321"
        check_stdout("memory", 6, last, contained, data_id_keys=("detector", "visit"))

        with self.assertRaisesRegex(RuntimeError, "Cannot handle kind=blah"):
            extract_metricvalues.print_metrics(butler, "blah")

    def test_print_diff_values(self):
        butler1 = lsst.daf.butler.Butler(self.repo1, collections="testrun")
        butler2 = lsst.daf.butler.Butler(self.repo2, collections="testrun")

        def check_stdout(n, last_line, **kwargs):
            """Test the the correct number of lines are printed, and that
            the last line is as expected.

            Parameters
            ----------
            n : `int`
                How many non-empty lines should have been printed?
            last_line : `str`
                Expected last non-empty line in the printed output.
            **kwargs
                Other arguments to pass to ``print_diff_metrics()``.
            """
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                extract_metricvalues.print_diff_metrics(butler1, butler2, **kwargs)
                # Split up the lines, and remove empty ones.
                result = list(filter(None, stdout.getvalue().split("\n")))
                self.assertEqual(len(result), n)
                self.assertEqual(last_line, result[-1])
            return result

        last_line = "Number of metrics that are the same in both runs: 0 / 6"
        result = check_stdout(10, last_line)
        expect = "{instrument: 'TestCam', detector: 12, visit: 12345, ...}"
        self.assertIn(expect, result)
        expect = "verify.another: 1.0 mas / 3.0 mas"
        self.assertIn(expect, result)

        result = check_stdout(10, last_line, data_id_keys=("detector", "visit"))
        expect = "detector: 12, visit: 12345"
        self.assertIn(expect, result)
        expect = "verify.another: 1.0 mas / 3.0 mas"
        self.assertIn(expect, result)


if __name__ == "__main__":
    unittest.main()

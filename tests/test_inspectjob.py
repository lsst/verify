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

from io import StringIO
import re
import unittest.mock

import astropy.units as u

from lsst.verify import Job, Metric, Measurement, ThresholdSpecification
from lsst.verify.bin.inspectjob import inspect_job


@unittest.mock.patch("sys.stdout", new_callable=StringIO)
class InspectJobTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Do not use re.DOTALL; some tests assume it's not set
        cls.regex_flags = re.IGNORECASE

    def setUp(self):
        self.job = Job()
        self.job.metrics.insert(Metric("foo.boringmetric", "",
                                       u.percent,
                                       tags=["redundant"]))
        self.job.metrics.insert(Metric("foo.fancymetric", "",
                                       u.meter,
                                       tags=["vital"]))
        self.job.measurements.insert(Measurement("foo.fancymetric",
                                                 2.0 * u.meter))
        self.job.measurements.insert(Measurement("foo.fanciermetric",
                                                 3.5 * u.second))
        self.job.measurements["foo.fanciermetric"].notes["fanciness"] \
            = "moderate"
        self.job.measurements.insert(Measurement("foo.fanciestmetric",
                                                 3.1415927 * u.kilogram))
        self.job.meta["bar"] = "high"
        self.job.meta["shape"] = "rotund"
        self.job.specs.insert(ThresholdSpecification("utterly_ridiculous",
                                                     1e10 * u.meter,
                                                     ">"))
        # MUST run inspect_job inside test case to capture output

    def test_metrics(self, mock_stdout):
        """Test that inspect_job only mentions metrics with measurements."
        """
        inspect_job(self.job)
        self.assertNotIn("foo.boringmetric", mock_stdout.getvalue())
        self.assertIn("foo.fancymetric", mock_stdout.getvalue())
        self.assertIn("foo.fanciermetric", mock_stdout.getvalue())
        self.assertIn("foo.fanciestmetric", mock_stdout.getvalue())

    def _check_measurement(self, measurement, output):
        # Test for metric name, followed by value and units
        # None of the examples are dimensionless, so can ignore that case
        regex = r"%s\W+?(?P<value>[\d.-]+ \w+)" % (measurement.metric_name)
        match = re.search(regex, output, flags=self.regex_flags)

        error = "Can't find %s and value on same row." \
            % measurement.metric_name
        self.assertIsNotNone(match, msg=error)

        value = match.group("value")
        try:
            trailing = re.match(r"\d+\.(\d+)", value, flags=self.regex_flags)
            decimals = len(trailing.group(1))
        except TypeError:
            decimals = 0
        # Don't test # of decimal places; trailing zeros may be dropped
        self.assertEqual(str(measurement.quantity.round(decimals)), value)

    def test_measurements(self, mock_stdout):
        """Test that inspect_job dumps measurements with and without metadata.
        """
        inspect_job(self.job)
        output = mock_stdout.getvalue()
        # MeasurementSet.values does not exist
        for _, measurement in self.job.measurements.items():
            self._check_measurement(measurement, output)

    def test_measurement_metadata(self, mock_stdout):
        """Test that inspect_job dumps measurement-level metadata on the same
        line as their measurement.
        """
        inspect_job(self.job)
        output = mock_stdout.getvalue()
        for metric_name, measurement in self.job.measurements.items():
            line = re.search("^.*%s.*$" % metric_name,
                             output,
                             flags=self.regex_flags | re.MULTILINE)
            error = "Can't find measurement %s" % metric_name
            self.assertIsNotNone(line, msg=error)
            line = line.group()

            for key in measurement.notes:
                regex = r"(?P<keyname>[\w\.]+)\W+%s" % (measurement.notes[key])
                match = re.search(regex, line, flags=self.regex_flags)
                self.assertIsNotNone(match,
                                     msg="Can't find metadata %s." % key)
                reportedMetadataName = match.group('keyname')
                fullMetadataName = "%s.%s" % (measurement.metric_name,
                                              reportedMetadataName)
                self.assertEqual(fullMetadataName, key)

    def _check_metadata(self, key, value, output):
        regex = r"%s.+%s" % (key, value)
        match = re.search(regex, output, flags=self.regex_flags)
        self.assertIsNotNone(match, msg="Can't find metadata %s" % key)

    def test_top_metadata(self, mock_stdout):
        """Test that inspect_job dumps top-level metadata.
        """
        inspect_job(self.job)
        output = mock_stdout.getvalue()
        for key, value in [("bar", "high"),
                           ("shape", "rotund")]:
            self._check_metadata(key, value, output)

    def test_specs(self, mock_stdout):
        """Test that inspect_job does not dump specifications."
        """
        self.assertNotIn("utterly_ridiculous", mock_stdout.getvalue())

    def test_empty(self, mock_stdout):
        """Test that inspect_job can handle files with neither metrics nor
        metadata.
        """
        inspect_job(Job())
        # No specific output expected, so test passes if inspect_job
        # didn't raise.

    def test_metadataonly(self, mock_stdout):
        """Test that inspect_job can handle files with metadata but no metrics.
        """
        # Job and its components were not designed to support deletion, so
        # create a new Job from scratch to ensure it's a valid object.
        job = Job()
        job.metrics.insert(Metric("foo.boringmetric", "",
                                  u.percent,
                                  tags=["redundant"]))
        job.metrics.insert(Metric("foo.fancymetric", "",
                                  u.meter,
                                  tags=["vital"]))
        job.meta["bar"] = "high"
        job.meta["shape"] = "rotund"
        job.specs.insert(ThresholdSpecification("utterly_ridiculous",
                                                1e10 * u.meter,
                                                ">"))

        inspect_job(job)
        output = mock_stdout.getvalue()
        for key, value in [("bar", "high"),
                           ("shape", "rotund")]:
            self._check_metadata(key, value, output)

    def test_metricsonly(self, mock_stdout):
        """Test that inspect_job can handle files with metrics but no metadata.
        """
        # Job and its components were not designed to support deletion, so
        # create a new Job from scratch to ensure it's a valid object.
        job = Job()
        job.metrics.insert(Metric("foo.boringmetric", "",
                                  u.percent,
                                  tags=["redundant"]))
        job.metrics.insert(Metric("foo.fancymetric", "",
                                  u.meter,
                                  tags=["vital"]))
        job.measurements.insert(Measurement("foo.fancymetric",
                                            2.0 * u.meter))
        job.measurements.insert(Measurement("foo.fanciermetric",
                                            3.5 * u.second))
        job.measurements["foo.fanciermetric"].notes["fanciness"] = "moderate"
        job.measurements.insert(Measurement("foo.fanciestmetric",
                                            3.1415927 * u.kilogram))

        inspect_job(job)
        output = mock_stdout.getvalue()
        # MeasurementSet.values does not exist
        for _, measurement in job.measurements.items():
            self._check_measurement(measurement, output)


if __name__ == "__main__":
    unittest.main()

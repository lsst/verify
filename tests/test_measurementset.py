#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
from __future__ import print_function

import os
import unittest

import astropy.units as u

from lsst.verify import MeasurementSet, Measurement, MetricSet, Name


class MeasurementSetTestCase(unittest.TestCase):

    def setUp(self):
        """Use YAML in data/metrics for metric definitions."""
        self.metrics_yaml_dirname = os.path.join(
            os.path.dirname(__file__), 'data')
        self.metric_set = MetricSet.load_metrics_package(
            self.metrics_yaml_dirname)

        self.pa1_meas = Measurement(
            self.metric_set['testing.PA1'],
            4. * u.mmag
        )
        self.am1_meas = Measurement(
            self.metric_set['testing.AM1'],
            2. * u.marcsec
        )
        self.pa2_meas = Measurement(
            self.metric_set['testing.PA2'],
            10. * u.mmag
        )

    def test_measurement_set(self):
        meas_set = MeasurementSet([self.pa1_meas])
        self.assertEqual(len(meas_set), 1)
        self.assertIn('testing.PA1', meas_set)
        self.assertIs(self.pa1_meas, meas_set['testing.PA1'])
        self.assertNotIn('testing.AM1', meas_set)

        # add an inconsistently labelled measurement
        with self.assertRaises(KeyError):
            meas_set['testing.AMx'] = self.am1_meas

        # Add measurement by key
        meas_set[self.am1_meas.metric_name] = self.am1_meas
        self.assertEqual(len(meas_set), 2)
        self.assertIn('testing.AM1', meas_set)
        self.assertIs(self.am1_meas, meas_set['testing.AM1'])

        # Insert measurement
        meas_set.insert(self.pa2_meas)
        self.assertEqual(len(meas_set), 3)
        self.assertIn('testing.PA2', meas_set)
        self.assertIs(self.pa2_meas, meas_set['testing.PA2'])

        # Delete measurement
        del meas_set['testing.PA2']
        self.assertNotIn('testing.PA2', meas_set)

        # Iterate
        items = {k: v for k, v in meas_set.items()}
        self.assertEqual(len(items), len(meas_set))

        names = [n for n in meas_set]
        self.assertEqual(len(names), 2)
        for n in names:
            self.assertIsInstance(n, Name)

        # Serialize
        json_doc = meas_set.json
        self.assertIsInstance(json_doc, list)
        self.assertEqual(len(json_doc), 2)
        for meas in json_doc:
            self.assertIn('metric', meas)

        # Deserialize (no blobs/BlobSet to propagate)
        new_meas_set = MeasurementSet.deserialize(
            measurements=json_doc,
            metric_set=self.metric_set)
        self.assertEqual(meas_set, new_meas_set)

    def test_measurement_set_update(self):
        meas_set = MeasurementSet([self.pa1_meas, self.am1_meas])
        meas_set_2 = MeasurementSet([self.am1_meas, self.pa2_meas])

        meas_set.update(meas_set_2)

        self.assertIs(meas_set['testing.PA1'], self.pa1_meas)
        self.assertIs(meas_set['testing.PA2'], self.pa2_meas)
        self.assertIs(meas_set['testing.AM1'], self.am1_meas)

    def test_measurement_iadd(self):
        meas_set = MeasurementSet([self.pa1_meas, self.am1_meas])
        meas_set_2 = MeasurementSet([self.am1_meas, self.pa2_meas])

        meas_set += meas_set_2

        self.assertIs(meas_set['testing.PA1'], self.pa1_meas)
        self.assertIs(meas_set['testing.PA2'], self.pa2_meas)
        self.assertIs(meas_set['testing.AM1'], self.am1_meas)


class MeasurementSetMetricReloadTestCase(unittest.TestCase):
    """Use YAML in data/metrics for metric definitions."""

    def setUp(self):
        self.metrics_yaml_dirname = os.path.join(
            os.path.dirname(__file__), 'data')
        self.metric_set = MetricSet.load_metrics_package(
            self.metrics_yaml_dirname)

    def test_reload(self):
        # Has Metric instance
        pa1_meas = Measurement(
            self.metric_set['testing.PA1'],
            4. * u.mmag
        )

        # Don't have metric instances
        am1_meas = Measurement(
            'testing.AM1',
            2. * u.marcsec
        )
        pa2_meas = Measurement(
            'testing.PA2',
            10. * u.mmag
        )

        measurements = MeasurementSet([pa1_meas, am1_meas, pa2_meas])
        measurements.refresh_metrics(self.metric_set)

        self.assertIs(
            measurements['testing.PA1'].metric,
            self.metric_set['testing.PA1']
        )
        self.assertIs(
            measurements['testing.AM1'].metric,
            self.metric_set['testing.AM1']
        )
        self.assertIs(
            measurements['testing.PA2'].metric,
            self.metric_set['testing.PA2']
        )


if __name__ == "__main__":
    unittest.main()

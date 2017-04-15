# See COPYRIGHT file at the top of the source tree.
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


if __name__ == "__main__":
    unittest.main()

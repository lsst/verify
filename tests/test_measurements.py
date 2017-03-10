#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import unittest

import astropy.units as u

from lsst.validate.base import Measurement, MeasurementSet, Metric, MetricSet


class MeasurementSetTestCase(unittest.TestCase):
    def setUp(self):
        package = 'test'
        self.package = package
        metric1 = Metric("{}.radius".format(package), "some radius", u.arcsec)
        metric2 = Metric("{}.cmodel_mag".format(package), "a magnitude", u.mag)
        metric3 = Metric("{}.unitless".format(package), "no units!", '')
        self.metric_set = MetricSet(package, metric_list=[metric1, metric2, metric3])

        self.good = {"{}.radius".format(package): .5*u.arcmin,
                     "{}.cmodel_mag".format(package): 22*u.mag,
                     "{}.unitless".format(package): 22*u.dimensionless_unscaled,
                     }

    def test_create_measurement_set(self):
        ms = MeasurementSet(self.package, self.good,
                            metric_set = self.metric_set)
        self.assertEqual(len(ms), 3)
        for name in self.good:
            self.assertEqual(ms[name].value, self.good[name])

    def test_create_using_validate_metrics(self):
        with self.assertRaises(NotImplementedError):
            MeasurementSet(self.package, self.good)

    def test_str(self):
        ms = MeasurementSet(self.package, self.good,
                            metric_set = self.metric_set)
        expect = "test: {\ntest.cmodel_mag: 22.0 mag,\ntest.radius: 0.5 arcmin,\ntest.unitless: 22.0\n}"
        self.assertEqual(str(ms), expect)


class MeasurementTestCase(unittest.TestCase):
    def setUp(self):
        # Need a metric set to check against
        package = 'test'
        self.package = package
        metric1 = Metric("{}.radius".format(package), "some radius", u.arcsec)
        metric2 = Metric("{}.cmodel_mag".format(package), "a magnitude", u.mag)
        metric3 = Metric("{}.unitless".format(package), "no units!", '')
        self.metric_set = MetricSet(package, metric_list=[metric1, metric2, metric3])

    def test_create_radius(self):
        metric = 'test.radius'
        value = 1235 * u.arcmin
        measurement = Measurement(metric, value, metric_set=self.metric_set)
        self.assertEqual(measurement.name, metric)
        self.assertEqual(measurement.value, value)
        self.assertEqual(measurement.description, "some radius")

    def test_create_magnitude(self):
        metric = 'test.cmodel_mag'
        value = 1235 * u.mag
        measurement = Measurement(metric, value, metric_set=self.metric_set)
        self.assertEqual(measurement.name, metric)
        self.assertEqual(measurement.value, value)
        self.assertEqual(measurement.description, "a magnitude")

    def test_create_invalid_name(self):
        metric = 'test.not_valid'
        value = 1235 * u.arcsec
        with self.assertRaises(KeyError):
            Measurement(metric, value, metric_set=self.metric_set)

    def test_create_invalid_unit(self):
        metric = 'test.unitless'
        value = 1235 * u.arcsec
        with self.assertRaises(u.UnitTypeError):
            Measurement(metric, value, metric_set=self.metric_set)

    def test_str(self):
        metric = 'test.cmodel_mag'
        value = 1235 * u.mag
        m = Measurement(metric, value, metric_set=self.metric_set)
        self.assertEqual(str(m), "test.cmodel_mag: 1235.0 mag")

if __name__ == "__main__":
    unittest.main()

# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import unittest

import astropy.units as u

from lsst.verify import MeasurementSet, Metric, MetricSet


@unittest.skip('DM-10199: skip while in development')
class MeasurementSetTestCase(unittest.TestCase):

    def setUp(self):
        package = 'test'
        self.package = package
        metric1 = Metric("{}.radius".format(package), "some radius", u.arcsec)
        metric2 = Metric("{}.cmodel_mag".format(package), "a magnitude", u.mag)
        metric3 = Metric("{}.unitless".format(package), "no units!", '')
        self.metric_set = MetricSet([metric1, metric2, metric3])

        self.good = {
            "{}.radius".format(package): .5*u.arcmin,
            "{}.cmodel_mag".format(package): 22*u.mag,
            "{}.unitless".format(package): 22*u.dimensionless_unscaled,
        }

    def test_create_measurement_set(self):
        ms = MeasurementSet(self.package, self.good,
                            metric_set=self.metric_set)
        self.assertEqual(len(ms), 3)
        for name in self.good:
            self.assertEqual(ms[name].value, self.good[name])

    def test_create_using_validate_metrics(self):
        with self.assertRaises(NotImplementedError):
            MeasurementSet(self.package, self.good)

    def test_str(self):
        ms = MeasurementSet(self.package, self.good,
                            metric_set=self.metric_set)
        expect = "test: {\ntest.cmodel_mag: 22.0 mag," \
                 "\ntest.radius: 0.5 arcmin,\ntest.unitless: 22.0\n}"
        self.assertEqual(str(ms), expect)


if __name__ == "__main__":
    unittest.main()

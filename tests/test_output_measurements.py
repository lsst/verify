# See COPYRIGHT file at the top of the source tree.
from __future__ import absolute_import, division, print_function

import json
import unittest
import astropy.units as u

from lsst.validate.base import Metric, MetricSet
import lsst.validate.base


def read_log(filename):
    with open(filename) as logfile:
        result = json.load(logfile)
    return result


class OutputTestCase(unittest.TestCase):
    def setUp(self):
        package = 'testing'
        metric1 = Metric("{}.thing1".format(package), 'thing1', u.arcsec)
        metric2 = Metric("{}.thing2".format(package), 'thing2', u.mag)
        self.metric_set = MetricSet("testing", [metric1, metric2])

    @unittest.skip('FIXME DM-8477 Likely to be removed.')
    def test_output_measurements_example(self):
        data = {'thing1': 10, 'thing2': 5.2}
        self.outfile = lsst.validate.base.output_measurements(
            self._testMethodName, data)
        result = read_log(self.outfile)
        self.assertEqual(data, result)


if __name__ == "__main__":
    unittest.main()

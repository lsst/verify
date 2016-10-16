#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import unittest

import numpy as np
from numpy.testing import assert_almost_equal

from lsst.validate.base import MeasurementBase, Metric, Datum


class DemoMeasurement(MeasurementBase):

    metric = None
    value = None
    units = 'mag'

    def __init__(self):
        MeasurementBase.__init__(self)

        self.metric = Metric('Test', 'Test metric', '<')

        test_datum = Datum(10., units='arcsecond', description='A datum')

        self.register_parameter('str_param', units='',
                                description='A string')
        self.register_parameter('float_param', units='mag',
                                description='A float')
        self.register_parameter('datum_param', datum=test_datum)

        self.register_extra('mags', units='mag', description='Some magnitudes')

        self.str_param = 'hello world'
        self.float_param = 22.

        self.mags = np.array([1., 2., 3.])

        self.value = 5.


class MeasurementBaseTestCase(unittest.TestCase):
    """Test Mesaurement class (via MeasurementBase) functionality."""

    def setUp(self):
        self.meas = DemoMeasurement()

    def tearDown(self):
        pass

    def test_label(self):
        self.assertEqual(self.meas.label, 'Test')

    def test_float_param(self):
        assert_almost_equal(self.meas.float_param, 22.)
        assert_almost_equal(self.meas.parameters['float_param'].value, 22.)
        self.assertEqual(self.meas.parameters['float_param'].units, 'mag')
        self.assertEqual(self.meas.parameters['float_param'].label, 'float_param')
        self.assertEqual(self.meas.parameters['float_param'].description,
                         'A float')

        # update
        self.meas.float_param = 12.
        assert_almost_equal(self.meas.float_param, 12.)
        assert_almost_equal(self.meas.parameters['float_param'].value, 12.)

    def test_str_param(self):
        self.assertEqual(self.meas.str_param, 'hello world')
        self.assertEqual(self.meas.parameters['str_param'].value, 'hello world')
        self.assertEqual(self.meas.parameters['str_param'].units, '')
        self.assertEqual(self.meas.parameters['str_param'].label, 'str_param')
        self.assertEqual(self.meas.parameters['str_param'].description,
                         'A string')

        # update
        self.meas.str_param = 'updated'
        self.assertEqual(self.meas.str_param, 'updated')
        self.assertEqual(self.meas.parameters['str_param'].value, 'updated')

    def test_datum_param(self):
        assert_almost_equal(self.meas.datum_param, 10.)
        self.assertEqual(self.meas.parameters['datum_param'].units, 'arcsecond')
        self.assertEqual(self.meas.parameters['datum_param'].label, 'datum_param')

    def test_extra(self):
        assert_almost_equal(self.meas.mags, np.array([1., 2., 3.]))
        assert_almost_equal(self.meas.extras['mags'].value, np.array([1., 2., 3.]))
        self.assertEqual(self.meas.extras['mags'].label, 'mags')
        self.assertEqual(self.meas.extras['mags'].units, 'mag')
        self.assertEqual(self.meas.extras['mags'].description, 'Some magnitudes')

    def test_json(self):
        j = self.meas.json

        assert_almost_equal(j['value'], 5.)
        self.assertEqual(j['units'], 'mag')
        self.assertEqual(j['parameters']['str_param']['value'], 'hello world')
        self.assertEqual(j['parameters']['str_param']['units'], '')
        self.assertEqual(j['parameters']['str_param']['label'], 'str_param')
        self.assertEqual(j['parameters']['str_param']['description'],
                         'A string')

        assert_almost_equal(j['extras']['mags']['value'][0], self.meas.mags[0])
        self.assertEqual(j['extras']['mags']['units'], 'mag')
        self.assertEqual(j['extras']['mags']['label'], 'mags')
        self.assertEqual(j['extras']['mags']['description'],
                         'Some magnitudes')


if __name__ == "__main__":
    unittest.main()

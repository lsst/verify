#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.

from __future__ import print_function

import unittest

import numpy as np
from numpy.testing import assert_almost_equal

import lsst.utils.tests as utilsTests

from lsst.validate.base import MeasurementBase, Metric, Datum


class DemoMeasurement(MeasurementBase):

    metric = None
    value = None
    units = 'mag'
    label = 'T'
    schema = 't-v1.0.0'

    def __init__(self):
        MeasurementBase.__init__(self)

        self.metric = Metric('Test', 'Test metric', '<')

        testDatum = Datum(10., units='arcsecond', description='A datum')

        self.registerParameter('strParam', units='',
                               description='A string')
        self.registerParameter('floatParam', units='mag',
                               description='A float')
        self.registerParameter('datumParam', datum=testDatum)

        self.registerExtra('mags', units='mag', description='Some magnitudes')

        self.strParam = 'hello world'
        self.floatParam = 22.

        self.mags = np.array([1., 2., 3.])

        self.value = 5.


class MeasurementBaseTestCase(unittest.TestCase):
    """Test Mesaurement class (via MeasurementBase) functionality."""

    def setUp(self):
        self.meas = DemoMeasurement()

    def tearDown(self):
        pass

    def testFloatParam(self):
        assert_almost_equal(self.meas.floatParam, 22.)
        assert_almost_equal(self.meas.parameters['floatParam'].value, 22.)
        self.assertEqual(self.meas.parameters['floatParam'].units, 'mag')
        self.assertEqual(self.meas.parameters['floatParam'].label, 'floatParam')
        self.assertEqual(self.meas.parameters['floatParam'].description,
                         'A float')

        # update
        self.meas.floatParam = 12.
        assert_almost_equal(self.meas.floatParam, 12.)
        assert_almost_equal(self.meas.parameters['floatParam'].value, 12.)

    def testStrParam(self):
        self.assertEqual(self.meas.strParam, 'hello world')
        self.assertEqual(self.meas.parameters['strParam'].value, 'hello world')
        self.assertEqual(self.meas.parameters['strParam'].units, '')
        self.assertEqual(self.meas.parameters['strParam'].label, 'strParam')
        self.assertEqual(self.meas.parameters['strParam'].description,
                         'A string')

        # update
        self.meas.strParam = 'updated'
        self.assertEqual(self.meas.strParam, 'updated')
        self.assertEqual(self.meas.parameters['strParam'].value, 'updated')

    def testDatumParam(self):
        assert_almost_equal(self.meas.datumParam, 10.)
        self.assertEqual(self.meas.parameters['datumParam'].units, 'arcsecond')
        self.assertEqual(self.meas.parameters['datumParam'].label, 'datumParam')

    def testExtra(self):
        assert_almost_equal(self.meas.mags, np.array([1., 2., 3.]))
        assert_almost_equal(self.meas.extras['mags'].value, np.array([1., 2., 3.]))
        self.assertEqual(self.meas.extras['mags'].label, 'mags')
        self.assertEqual(self.meas.extras['mags'].units, 'mag')
        self.assertEqual(self.meas.extras['mags'].description, 'Some magnitudes')

    def testJson(self):
        j = self.meas.json

        assert_almost_equal(j['value'], 5.)
        self.assertEqual(j['parameters']['strParam']['value'], 'hello world')
        self.assertEqual(j['parameters']['strParam']['units'], '')
        self.assertEqual(j['parameters']['strParam']['label'], 'strParam')
        self.assertEqual(j['parameters']['strParam']['description'],
                         'A string')

        assert_almost_equal(j['extras']['mags']['value'][0], self.meas.mags[0])
        self.assertEqual(j['extras']['mags']['units'], 'mag')
        self.assertEqual(j['extras']['mags']['label'], 'mags')
        self.assertEqual(j['extras']['mags']['description'],
                         'Some magnitudes')


def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(MeasurementBaseTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)


if __name__ == "__main__":
    run(True)

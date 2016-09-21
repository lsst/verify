#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.

from __future__ import print_function

import os
import unittest

import yaml

from lsst.utils import getPackageDir
import lsst.utils.tests as utilsTests

from lsst.validate.base import Metric, Specification, Datum


class MetricTestCase(unittest.TestCase):
    """Test Metrics and metrics.yaml functionality."""

    def setUp(self):
        yamlPath = os.path.join(getPackageDir('validate_base'),
                                os.path.join('tests', 'data', 'metrics.yaml'))
        with open(yamlPath) as f:
            self.metricDoc = yaml.load(f)

    def tearDown(self):
        pass

    def testLoadAllYamlMetrics(self):
        """Verify that all metrics from metrics.yaml can be loaded."""
        for metricName in self.metricDoc:
            m = Metric.fromYaml(metricName, yamlDoc=self.metricDoc)
            self.assertIsInstance(m, Metric)

    def testReferenceString(self):
        """Verify reference property for different reference datasets."""
        m1 = Metric('test', 'test', '<=', referenceUrl='example.com',
                    referenceDoc='Doc', referencePage=1)
        self.assertEqual(m1.reference, 'Doc, p. 1, example.com')

        m2 = Metric('test', 'test', '<=', referenceUrl='example.com')
        self.assertEqual(m2.reference, 'example.com')

        m3 = Metric('test', 'test', '<=', referenceUrl='example.com',
                    referenceDoc='Doc')
        self.assertEqual(m3.reference, 'Doc, example.com')

        m4 = Metric('test', 'test', '<=',
                    referenceDoc='Doc', referencePage=1)
        self.assertEqual(m4.reference, 'Doc, p. 1')

        m4 = Metric('test', 'test', '<=',
                    referenceDoc='Doc')
        self.assertEqual(m4.reference, 'Doc')

    def testOperatorConversion(self):
        """Tests for Metric.convertOperatorString."""
        self.assertTrue(Metric.convertOperatorString('>=')(7, 7))
        self.assertTrue(Metric.convertOperatorString('>')(7, 5))
        self.assertTrue(Metric.convertOperatorString('<')(5, 7))
        self.assertTrue(Metric.convertOperatorString('<=')(7, 7))
        self.assertTrue(Metric.convertOperatorString('==')(7, 7))
        self.assertTrue(Metric.convertOperatorString('!=')(7, 5))

    def testAM1GetSpecNames(self):
        """Test getSpecNames against AM1."""
        am1 = Metric.fromYaml('AM1', yamlDoc=self.metricDoc)
        specNamesAll = am1.getSpecNames()
        self.assertTrue(len(specNamesAll) == 3)
        self.assertIn('design', specNamesAll)
        self.assertIn('minimum', specNamesAll)
        self.assertIn('stretch', specNamesAll)

        # No specs for bands other than r and i!
        specNamesG = am1.getSpecNames(bandpass='g')
        self.assertTrue(len(specNamesG) == 0)

    def testGetSpec(self):
        """Test Metric.getSpec() search strategy."""
        a = Specification('a', 0, 'mag')
        b_r = Specification('b', 0, 'mag', bandpasses=['r'])
        b_ug = Specification('b', 0, 'mag', bandpasses=['u', 'g'])

        m = Metric('test', 'test', '==', specs=[a, b_r, b_ug])

        self.assertEqual(m.getSpec('a'), a)
        self.assertEqual(m.getSpec('a', bandpass='r'), a)
        self.assertEqual(m.getSpec('b', bandpass='r'), b_r)
        self.assertEqual(m.getSpec('b', bandpass='u'), b_ug)

        with self.assertRaises(RuntimeError):
            self.assertEqual(m.getSpec('c'))

        with self.assertRaises(RuntimeError):
            self.assertEqual(m.getSpec('b', bandpass='z'))

    def testCheckSpec(self):
        """Test Metric.testSpec()."""
        a = Specification('a', 0, 'mag')
        b_r = Specification('b', 2, 'mag', bandpasses=['r'])
        b_ug = Specification('b', 4, 'mag', bandpasses=['u', 'g'])
        m = Metric('test', 'test', '<', specs=[a, b_r, b_ug])

        self.assertFalse(m.checkSpec(3, 'b', bandpass='r'))
        self.assertTrue(m.checkSpec(3, 'b', bandpass='g'))

    def testJson(self):
        """Simple test of the serialized JSON content of a metric."""
        name = 'T1'
        description = 'Test'
        operatorStr = '=='
        referenceDoc = 'TEST-1'
        referencePage = 1
        referenceUrl = 'example.com'
        deps = {'dep': Datum(5, 'mag')}
        m = Metric(name, description, operatorStr,
                   referenceDoc=referenceDoc,
                   referenceUrl=referenceUrl,
                   referencePage=referencePage,
                   dependencies=deps)

        j = m.json
        self.assertEqual(j['name'], name)
        self.assertEqual(j['description'], description)
        self.assertEqual(j['reference']['doc'], referenceDoc)
        self.assertEqual(j['reference']['page'], referencePage)
        self.assertEqual(j['reference']['url'], referenceUrl)
        self.assertEqual(j['dependencies']['dep']['value'], 5)
        self.assertEqual(j['dependencies']['dep']['units'], 'mag')
        self.assertIsInstance(j['specifications'], list)


def suite():
    """Returns a suite containing all the test cases in this module."""

    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(MetricTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)


if __name__ == "__main__":
    run(True)

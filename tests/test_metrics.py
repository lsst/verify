#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import os
import unittest

import yaml

from lsst.validate.base import Metric, Specification, Datum


class MetricTestCase(unittest.TestCase):
    """Test Metrics and metrics.yaml functionality."""

    def setUp(self):
        yaml_path = os.path.join(os.path.dirname(__file__),
                                 'data', 'metrics.yaml')
        with open(yaml_path) as f:
            self.metric_doc = yaml.load(f)

    def tearDown(self):
        pass

    def test_load_all_yaml_metrics(self):
        """Verify that all metrics from metrics.yaml can be loaded."""
        for metric_name in self.metric_doc:
            m = Metric.from_yaml(metric_name, yaml_doc=self.metric_doc)
            self.assertIsInstance(m, Metric)

    def test_reference_string(self):
        """Verify reference property for different reference datasets."""
        m1 = Metric('test', 'test', '<=', reference_url='example.com',
                    reference_doc='Doc', reference_page=1)
        self.assertEqual(m1.reference, 'Doc, p. 1, example.com')

        m2 = Metric('test', 'test', '<=', reference_url='example.com')
        self.assertEqual(m2.reference, 'example.com')

        m3 = Metric('test', 'test', '<=', reference_url='example.com',
                    reference_doc='Doc')
        self.assertEqual(m3.reference, 'Doc, example.com')

        m4 = Metric('test', 'test', '<=',
                    reference_doc='Doc', reference_page=1)
        self.assertEqual(m4.reference, 'Doc, p. 1')

        m4 = Metric('test', 'test', '<=',
                    reference_doc='Doc')
        self.assertEqual(m4.reference, 'Doc')

    def testOperatorConversion(self):
        """Tests for Metric.convert_operator_str."""
        self.assertTrue(Metric.convert_operator_str('>=')(7, 7))
        self.assertTrue(Metric.convert_operator_str('>')(7, 5))
        self.assertTrue(Metric.convert_operator_str('<')(5, 7))
        self.assertTrue(Metric.convert_operator_str('<=')(7, 7))
        self.assertTrue(Metric.convert_operator_str('==')(7, 7))
        self.assertTrue(Metric.convert_operator_str('!=')(7, 5))

    def testAM1GetSpecNames(self):
        """Test get_spec_names against AM1."""
        am1 = Metric.from_yaml('AM1', yaml_doc=self.metric_doc)
        spec_names_all = am1.get_spec_names()
        self.assertTrue(len(spec_names_all) == 3)
        self.assertIn('design', spec_names_all)
        self.assertIn('minimum', spec_names_all)
        self.assertIn('stretch', spec_names_all)

        # No specs for bands other than r and i!
        spec_names_g = am1.get_spec_names(filter_name='g')
        self.assertTrue(len(spec_names_g) == 0)

    def testGetSpec(self):
        """Test Metric.getSpec() search strategy."""
        a = Specification('a', 0, 'mag')
        b_r = Specification('b', 0, 'mag', filter_names=['r'])
        b_ug = Specification('b', 0, 'mag', filter_names=['u', 'g'])

        m = Metric('test', 'test', '==', specs=[a, b_r, b_ug])

        self.assertEqual(m.get_spec('a'), a)
        self.assertEqual(m.get_spec('a', filter_name='r'), a)
        self.assertEqual(m.get_spec('b', filter_name='r'), b_r)
        self.assertEqual(m.get_spec('b', filter_name='u'), b_ug)

        with self.assertRaises(RuntimeError):
            self.assertEqual(m.get_spec('c'))

        with self.assertRaises(RuntimeError):
            self.assertEqual(m.get_spec('b', filter_name='z'))

    def test_get_spec_dependency(self):
        af1 = Metric.from_yaml('AF1', yaml_doc=self.metric_doc)
        dep = af1.get_spec_dependency('design', 'AD1', filter_name='r')

        ad1 = Metric.from_yaml('AD1', yaml_doc=self.metric_doc)

        self.assertEqual(dep.value,
                         ad1.get_spec('design', filter_name='r').value)

    def test_check_spec(self):
        """Test Metric.check_spec()."""
        a = Specification('a', 0, 'mag')
        b_r = Specification('b', 2, 'mag', filter_names=['r'])
        b_ug = Specification('b', 4, 'mag', filter_names=['u', 'g'])
        m = Metric('test', 'test', '<', specs=[a, b_r, b_ug])

        self.assertFalse(m.check_spec(3, 'b', filter_name='r'))
        self.assertTrue(m.check_spec(3, 'b', filter_name='g'))

    def test_json(self):
        """Simple test of the serialized JSON content of a metric."""
        name = 'T1'
        description = 'Test'
        operator_str = '=='
        reference_doc = 'TEST-1'
        reference_page = 1
        reference_url = 'example.com'
        params = {'p': Datum(5, 'mag')}
        m = Metric(name, description, operator_str,
                   reference_doc=reference_doc,
                   reference_url=reference_url,
                   reference_page=reference_page,
                   parameters=params)

        j = m.json
        self.assertEqual(j['name'], name)
        self.assertEqual(j['description'], description)
        self.assertEqual(j['reference']['doc'], reference_doc)
        self.assertEqual(j['reference']['page'], reference_page)
        self.assertEqual(j['reference']['url'], reference_url)
        self.assertEqual(j['parameters']['p']['value'], 5)
        self.assertEqual(j['parameters']['p']['units'], 'mag')
        self.assertIsInstance(j['specifications'], list)


if __name__ == "__main__":
    unittest.main()

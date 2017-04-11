# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import os
import unittest

import yaml
import astropy.units as u

from lsst.verify import Metric, MetricSet, Name


class MetricsPackageTestCase(unittest.TestCase):
    """Test creating a MetricSet from a mock verification framework
    metric package located at data/ relative test modules.

    These tests are coupled to the data/metrics/*.yaml files.
    """

    def setUp(self):
        self.metrics_yaml_dirname = os.path.join(
            os.path.dirname(__file__), 'data')

        self.metric_set = MetricSet.load_metrics_package(
            self.metrics_yaml_dirname)

    def test_len(self):
        self.assertEqual(len(self.metric_set), 4)

    def test_contains(self):
        for key in ['testing.PA1',
                    'testing.PF1',
                    'testing.PA2',
                    'testing.AM1']:
            self.assertIn(key, self.metric_set, msg=key)

    def test_iter(self):
        """Test __iter__ over keys (Name instances of metrics)."""
        keys = [k for k in self.metric_set]
        self.assertEqual(len(keys), 4)
        for k in keys:
            self.assertIsInstance(k, Name)

    def test_items(self):
        """Test the items iterator."""
        count = 0
        for key, value in self.metric_set.items():
            count += 1
            self.assertIsInstance(key, Name)
            self.assertIsInstance(value, Metric)
        self.assertEqual(count, 4)

    def test_setitem_delitem(self):
        """Test adding and deleting metrics."""
        m1 = Metric('validate_drp.test',
                    'test', '',
                    reference_url='example.com',
                    reference_doc='Doc', reference_page=1)
        metric_set = MetricSet()
        self.assertEqual(len(metric_set), 0)

        metric_set['validate_drp.test'] = m1
        self.assertEqual(len(metric_set), 1)
        self.assertEqual(metric_set['validate_drp.test'], m1)

        with self.assertRaises(KeyError):
            # inconsistent metric names
            metric_set['validate_drp.new_test'] = m1

        with self.assertRaises(TypeError):
            # Not a metric name
            n = Name('validate_drp')
            m2 = Metric(n, 'test', '')
            metric_set[n] = m2

        del metric_set['validate_drp.test']
        self.assertEqual(len(metric_set), 0)

    def test_insert(self):
        """Test MetricSet.insert."""
        m1 = Metric('validate_drp.test',
                    'test', '',
                    reference_url='example.com',
                    reference_doc='Doc', reference_page=1)
        metric_set = MetricSet()

        metric_set.insert(m1)
        self.assertEqual(m1, metric_set['validate_drp.test'])


class VerifyMetricsParsingTestCase(unittest.TestCase):
    """Test parsing metrics from verify_metrics (an EUPS package)."""

    def setUp(self):
        self.metric_set = MetricSet.load_metrics_package('verify_metrics')

    def test_len(self):
        """Just verify that we got metrics without raising an exception"""
        self.assertTrue(len(self.metric_set) > 0)

    def test_nonexistent_package(self):
        """Test handling of non-existing metrics packages/directories."""
        with self.assertRaises(OSError):
            MetricSet.load_metrics_package('nonexistent_metrics')


class MetricTestCase(unittest.TestCase):
    """Test Metrics and metrics.yaml functionality."""

    def setUp(self):
        yaml_path = os.path.join(os.path.dirname(__file__),
                                 'data', 'metrics', 'testing.yaml')
        with open(yaml_path) as f:
            self.metric_doc = yaml.load(f)

    def test_load_all_yaml_metrics(self):
        """Verify that all metrics from testing.yaml can be loaded."""
        for metric_name in self.metric_doc:
            m = Metric.deserialize(metric_name, **self.metric_doc[metric_name])
            self.assertIsInstance(m, Metric)

    def test_reference_string(self):
        """Verify reference property for different reference datasets."""
        m1 = Metric('test', 'test', '', reference_url='example.com',
                    reference_doc='Doc', reference_page=1)
        self.assertEqual(m1.reference, 'Doc, p. 1, example.com')

        m2 = Metric('test', 'test', '', reference_url='example.com')
        self.assertEqual(m2.reference, 'example.com')

        m3 = Metric('test', 'test', '', reference_url='example.com',
                    reference_doc='Doc')
        self.assertEqual(m3.reference, 'Doc, example.com')

        m4 = Metric('test', 'test', '', reference_doc='Doc', reference_page=1)
        self.assertEqual(m4.reference, 'Doc, p. 1')

        m4 = Metric('test', 'test', '', reference_doc='Doc')
        self.assertEqual(m4.reference, 'Doc')

    def test_json(self):
        """Simple test of the serialized JSON content of a metric."""
        name = 'T1'
        description = 'Test'
        unit = u.mag
        reference_doc = 'TEST-1'
        reference_page = 1
        reference_url = 'example.com'
        m = Metric(name, description, unit,
                   reference_doc=reference_doc,
                   reference_url=reference_url,
                   reference_page=reference_page)

        j = m.json
        self.assertEqual(j['name'], name)
        self.assertEqual(j['description'], description)
        self.assertEqual(j['unit'], unit)
        self.assertEqual(j['reference']['doc'], reference_doc)
        self.assertEqual(j['reference']['page'], reference_page)
        self.assertEqual(j['reference']['url'], reference_url)

        # rebuild from json
        m2 = Metric.deserialize(**j)
        self.assertEqual(m, m2)

    def test_str(self):
        m1 = Metric('test', 'test docs', 'arcsec', reference_url='example.com',
                    reference_doc='Doc', reference_page=1)
        self.assertEqual(str(m1), 'test (arcsec): test docs')

        m2 = Metric('test2', 'some words', '')
        self.assertEqual(
            str(m2),
            'test2 (dimensionless_unscaled): some words')

    def test_check_unit(self):
        m = Metric('test', '', 'marcsec')
        self.assertTrue(m.check_unit(5. * u.arcsec))
        self.assertTrue(m.check_unit(5. * u.marcsec))
        self.assertFalse(m.check_unit(5. * u.mag))


if __name__ == "__main__":
    unittest.main()

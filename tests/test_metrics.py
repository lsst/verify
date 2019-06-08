# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import os
import unittest

import yaml
import astropy.units as u

from lsst.verify import Metric


class MetricTestCase(unittest.TestCase):
    """Test Metrics and metrics.yaml functionality."""

    def setUp(self):
        yaml_path = os.path.join(os.path.dirname(__file__),
                                 'data', 'metrics', 'testing.yaml')
        with open(yaml_path) as f:
            self.metric_doc = yaml.safe_load(f)

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
                   tags=['tagA', 'tagB'],
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
        self.assertIn('tagA', j['tags'])
        self.assertIn('tagB', j['tags'])
        self.assertNotIn('tagC', j['tags'])

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

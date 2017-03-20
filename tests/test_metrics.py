#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import os
import unittest

import yaml
import astropy.units as u

from lsst.validate.base import Metric, MetricSet, MetricRepo


class MetricRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.yaml_path = os.path.join(
            os.path.dirname(__file__),
            'data',
            'metrics')

    def test_from_metrics_dir(self):
        metric_repo = MetricRepo.from_metrics_dir(self.yaml_path)
        self.assertEqual(len(metric_repo), 1)
        self.assertIn('testing', metric_repo)
        self.assertEqual(metric_repo['testing'].name, 'testing')

    def test_str(self):
        m1 = Metric('m1', 'm1 docs', u.arcsec)
        m2 = Metric('m2', 'm2 docs', u.mag)
        metric_set = MetricSet(
            'some_metrics',
            metric_dict={'m1': m1, 'm2': m2})
        metric_repo = MetricRepo(
            'some/path/test',
            {metric_set.name: metric_set})
        expect = 'some/path/test: {\nsome_metrics: ' \
                 '{\nm1 (arcsec): "m1 docs",\nm2 (mag): "m2 docs"\n}}'
        self.assertEqual(str(metric_repo), expect)


class MetricSetTestCase(unittest.TestCase):
    def setUp(self):
        yaml_path = os.path.join(os.path.dirname(__file__),
                                 'data', 'metrics', 'testing.yaml')
        with open(yaml_path) as f:
            self.metric_doc = yaml.load(f)

    def test_from_yaml(self):
        metric_set = MetricSet.from_yaml('testing', self.metric_doc)
        self.assertEqual(len(metric_set), 4)
        for key in ['testing.PA1',
                    'testing.PF1',
                    'testing.PA2',
                    'testing.AM1']:
            self.assertIn(key, metric_set, msg=key)
            self.assertEqual(metric_set[key].name, key.split('.')[1])

    def test_str(self):
        m1 = Metric('m1', 'm1 docs', u.arcsec)
        m2 = Metric('m2', 'm2 docs', u.mag)
        metric_set = MetricSet('some_metrics',
                               metric_dict={'m1': m1, 'm2': m2})
        expect = 'some_metrics: {\nm1 (arcsec): "m1 docs",\n' \
                 'm2 (mag): "m2 docs"\n}'
        self.assertEqual(str(metric_set), expect)


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
            m = Metric.from_yaml(metric_name, yaml_doc=self.metric_doc)
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
        m2 = Metric.from_json(j)
        self.assertEqual(m.name, m2.name)
        self.assertEqual(m.description, m2.description)
        self.assertEqual(m.unit, m2.unit)
        self.assertEqual(m.reference_doc, m2.reference_doc)
        self.assertEqual(m.reference_page, m2.reference_page)
        self.assertEqual(m.reference_url, m2.reference_url)

    def test_str(self):
        m1 = Metric('test', 'test docs', 'arcsec', reference_url='example.com',
                    reference_doc='Doc', reference_page=1)
        self.assertEqual(str(m1), 'test (arcsec): "test docs"')
        m2 = Metric('test2', 'some words', '')
        self.assertEqual(
            str(m2),
            'test2 (dimensionless_unscaled): "some words"')


if __name__ == "__main__":
    unittest.main()

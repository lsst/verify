# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import os
import unittest

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

    def test_tags(self):
        """Both single string and tag lists are present in YAML."""
        # Parsing this metric required putting the single tag inside a list
        self.assertEqual(
            len(self.metric_set['testing.PA1'].tags),
            1)
        self.assertIn(
            'photometric',
            self.metric_set['testing.PA1'].tags)

        self.assertEqual(
            len(self.metric_set['testing.AM1'].tags),
            2)
        self.assertIn(
            'astrometric',
            self.metric_set['testing.AM1'].tags)
        self.assertIn(
            'random-tag',
            self.metric_set['testing.AM1'].tags)

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


class MetricSetSubsetTestCase(unittest.TestCase):
    """Test case for MetricSet.subset."""

    def setUp(self):
        self.m1 = Metric('pkgA.m1', 'In pkgA', '', tags='testing')
        self.m2 = Metric('pkgA.m2', 'In pkgA', '', tags='other')
        self.m3 = Metric('pkgB.m3', 'In pkgB', '', tags='testing')
        self.metric_set = MetricSet([self.m1, self.m2, self.m3])

    def test_subset_A(self):
        subset = self.metric_set.subset('pkgA')
        self.assertEqual(len(subset), 2)
        self.assertIn(self.m1.name, subset)
        self.assertIn(self.m2.name, subset)
        self.assertNotIn(self.m3.name, subset)

    def test_subset_B(self):
        subset = self.metric_set.subset('pkgB')
        self.assertEqual(len(subset), 1)
        self.assertNotIn(self.m1.name, subset)
        self.assertNotIn(self.m2.name, subset)
        self.assertIn(self.m3.name, subset)

    def test_subset_testing_tag(self):
        subset = self.metric_set.subset(tag='testing')
        self.assertEqual(len(subset), 2)
        self.assertIn(self.m1.name, subset)
        self.assertNotIn(self.m2.name, subset)
        self.assertIn(self.m3.name, subset)

    def test_subset_A_testing_tag(self):
        subset = self.metric_set.subset(package='pkgA', tag='testing')
        self.assertEqual(len(subset), 1)
        self.assertIn(self.m1.name, subset)
        self.assertNotIn(self.m2.name, subset)
        self.assertNotIn(self.m3.name, subset)


class MetricSetSerializationTestCase(unittest.TestCase):
    """Test JSON serialization and deserialization for MetricSets."""

    def setUp(self):
        self.m1 = Metric('pkgA.m1', 'In pkgA', '', tags='testing')
        self.m2 = Metric('pkgA.m2', 'In pkgA', '', tags='other')
        self.m3 = Metric('pkgB.m3', 'In pkgB', '', tags='testing')
        self.metric_set = MetricSet([self.m1, self.m2, self.m3])

    def test_serialization(self):
        json_doc = self.metric_set.json
        new_metric_set = MetricSet.deserialize(json_doc)
        self.assertEqual(self.metric_set, new_metric_set)

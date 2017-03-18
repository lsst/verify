# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import unittest

from lsst.verify.naming import Name


class FullyQualifiedMetricName(unittest.TestCase):
    """Simple fully-qualified metric name."""

    def setUp(self):
        self.name = Name(package='validate_drp', metric='PA1')

    def test_package_name(self):
        self.assertEqual(self.name.package, 'validate_drp')

    def test_metric_name(self):
        self.assertEqual(self.name.metric, 'PA1')

    def test_spec_name(self):
        self.assertIsNone(self.name.spec)

    def test_fqn(self):
        self.assertEqual(
            self.name.fqn,
            'validate_drp.PA1')

    def test_relative_name(self):
        with self.assertRaises(AttributeError):
            self.name.relative_name

    def test_repr(self):
        self.assertEqual(
            repr(self.name),
            "Name('validate_drp', 'PA1')")

    def test_str(self):
        self.assertEqual(
            str(self.name),
            'validate_drp.PA1'
        )

    def test_eq(self):
        self.assertTrue(
            self.name == Name(package='validate_drp', metric='PA1'))
        self.assertFalse(
            self.name == Name(package='validate_drp',
                              metric='PA1',
                              spec='design'))
        self.assertFalse(
            self.name == Name(package='validate_base',
                              metric='PA1'))

    def test_has_package(self):
        self.assertTrue(self.name.has_package)

    def test_has_metric(self):
        self.assertTrue(self.name.has_metric)

    def test_has_spec(self):
        self.assertFalse(self.name.has_spec)

    def test_has_relative(self):
        self.assertFalse(self.name.has_relative)

    def test_is_package(self):
        self.assertFalse(self.name.is_package)

    def test_is_metric(self):
        self.assertTrue(self.name.is_metric)

    def test_is_spec(self):
        self.assertFalse(self.name.is_spec)

    def test_is_fq(self):
        self.assertTrue(self.name.is_fq)

    def test_is_relative(self):
        self.assertFalse(self.name.is_relative)


class MetricName(unittest.TestCase):
    """Metric name (not fully qualified)."""

    def setUp(self):
        self.name = Name(metric='PA1')

    def test_package_name(self):
        self.assertIsNone(self.name.package)

    def test_metric_name(self):
        self.assertEqual(self.name.metric, 'PA1')

    def test_spec_name(self):
        self.assertIsNone(self.name.spec)

    def test_fqn(self):
        with self.assertRaises(AttributeError):
            self.name.fqn,

    def test_relative_name(self):
        with self.assertRaises(AttributeError):
            self.name.relative_name

    def test_repr(self):
        self.assertEqual(
            repr(self.name),
            "Name(metric='PA1')")

    def test_str(self):
        self.assertEqual(
            str(self.name),
            'PA1'
        )

    def test_eq(self):
        self.assertTrue(
            self.name == Name(metric='PA1'))
        self.assertFalse(
            self.name == Name(package='validate_drp', metric='PA2'))
        self.assertFalse(
            self.name == Name(metric='PA2'))

    def test_has_package(self):
        self.assertFalse(self.name.has_package)

    def test_has_metric(self):
        self.assertTrue(self.name.has_metric)

    def test_has_spec(self):
        self.assertFalse(self.name.has_spec)

    def test_has_relative(self):
        self.assertFalse(self.name.has_relative)

    def test_is_package(self):
        self.assertFalse(self.name.is_package)

    def test_is_metric(self):
        self.assertTrue(self.name.is_metric)

    def test_is_spec(self):
        self.assertFalse(self.name.is_spec)

    def test_is_fq(self):
        self.assertFalse(self.name.is_fq)

    def test_is_relative(self):
        self.assertFalse(self.name.is_relative)


class FullyQualifiedSpecificationName(unittest.TestCase):
    """Simple fully-qualified specification name."""

    def setUp(self):
        self.name = Name(package='validate_drp',
                         metric='PA1',
                         spec='design_gri')

    def test_package_name(self):
        self.assertEqual(self.name.package, 'validate_drp')

    def test_metric_name(self):
        self.assertEqual(self.name.metric, 'PA1')

    def test_spec_name(self):
        self.assertEqual(self.name.spec, 'design_gri')

    def test_fqn(self):
        self.assertEqual(
            self.name.fqn,
            'validate_drp.PA1.design_gri')

    def test_relative_name(self):
        self.assertEqual(
            self.name.relative_name,
            'PA1.design_gri')

    def test_repr(self):
        self.assertEqual(
            repr(self.name),
            "Name('validate_drp', 'PA1', 'design_gri')")

    def test_str(self):
        self.assertEqual(
            str(self.name),
            'validate_drp.PA1.design_gri'
        )

    def test_eq(self):
        self.assertTrue(
            self.name == Name(package='validate_drp',
                              metric='PA1',
                              spec='design_gri'))
        self.assertFalse(
            self.name == Name(package='validate_drp',
                              metric='PA1',
                              spec='minimum'))
        self.assertFalse(
            self.name == Name(metric='PA1',
                              spec='design_gri'))
        self.assertFalse(
            self.name == Name(spec='design_gri'))

    def test_has_package(self):
        self.assertTrue(self.name.has_package)

    def test_has_metric(self):
        self.assertTrue(self.name.has_metric)

    def test_has_spec(self):
        self.assertTrue(self.name.has_spec)

    def test_has_relative(self):
        self.assertTrue(self.name.has_relative)

    def test_is_package(self):
        self.assertFalse(self.name.is_package)

    def test_is_metric(self):
        self.assertFalse(self.name.is_metric)

    def test_is_spec(self):
        self.assertTrue(self.name.is_spec)

    def test_is_fq(self):
        self.assertTrue(self.name.is_fq)

    def test_is_relative(self):
        self.assertFalse(self.name.is_relative)


class RelativeSpecificationName(unittest.TestCase):
    """Metric-relative specification name."""

    def setUp(self):
        self.name = Name(metric='PA1',
                         spec='design_gri')

    def test_package_name(self):
        self.assertIsNone(self.name.package)

    def test_metric_name(self):
        self.assertEqual(self.name.metric, 'PA1')

    def test_spec_name(self):
        self.assertEqual(self.name.spec, 'design_gri')

    def test_fqn(self):
        with self.assertRaises(AttributeError):
            self.name.fqn

    def test_relative_name(self):
        self.assertEqual(
            self.name.relative_name,
            'PA1.design_gri')

    def test_repr(self):
        self.assertEqual(
            repr(self.name),
            "Name(metric='PA1', spec='design_gri')")

    def test_str(self):
        self.assertEqual(
            str(self.name),
            'PA1.design_gri'
        )

    def test_eq(self):
        self.assertTrue(
            self.name == Name(metric='PA1', spec='design_gri'))
        self.assertFalse(
            self.name == Name(package='validate_drp',
                              metric='PA1',
                              spec='design_gri'))
        self.assertFalse(
            self.name == Name(metric='PA1', spec='minimum'))

    def test_has_package(self):
        self.assertFalse(self.name.has_package)

    def test_has_metric(self):
        self.assertTrue(self.name.has_metric)

    def test_has_spec(self):
        self.assertTrue(self.name.has_spec)

    def test_has_relative(self):
        self.assertTrue(self.name.has_relative)

    def test_is_package(self):
        self.assertFalse(self.name.is_package)

    def test_is_metric(self):
        self.assertFalse(self.name.is_metric)

    def test_is_spec(self):
        self.assertTrue(self.name.is_spec)

    def test_is_fq(self):
        self.assertFalse(self.name.is_fq)

    def test_is_relative(self):
        self.assertTrue(self.name.is_relative)


class SpecificationName(unittest.TestCase):
    """A bare specification name."""

    def setUp(self):
        self.name = Name(spec='design_gri')

    def test_package_name(self):
        self.assertIsNone(self.name.package)

    def test_metric_name(self):
        self.assertIsNone(self.name.metric)

    def test_spec_name(self):
        self.assertEqual(self.name.spec, 'design_gri')

    def test_fqn(self):
        with self.assertRaises(AttributeError):
            self.name.fqn

    def test_relative_name(self):
        with self.assertRaises(AttributeError):
            self.name.relative_name

    def test_repr(self):
        self.assertEqual(
            repr(self.name),
            "Name(spec='design_gri')")

    def test_str(self):
        self.assertEqual(
            str(self.name),
            'design_gri'
        )

    def test_eq(self):
        self.assertTrue(
            self.name == Name(spec='design_gri'))
        self.assertFalse(
            self.name == Name(metric='PA1', spec='design_gri'))
        self.assertFalse(
            self.name == Name(spec='minimum'))

    def test_has_package(self):
        self.assertFalse(self.name.has_package)

    def test_has_metric(self):
        self.assertFalse(self.name.has_metric)

    def test_has_spec(self):
        self.assertTrue(self.name.has_spec)

    def test_has_relative(self):
        self.assertFalse(self.name.has_relative)

    def test_is_package(self):
        self.assertFalse(self.name.is_package)

    def test_is_metric(self):
        self.assertFalse(self.name.is_metric)

    def test_is_spec(self):
        self.assertTrue(self.name.is_spec)

    def test_is_fq(self):
        self.assertFalse(self.name.is_fq)

    def test_is_relative(self):
        self.assertFalse(self.name.is_relative)


class PackageName(unittest.TestCase):
    """Package name."""

    def setUp(self):
        self.name = Name(package='validate_drp')

    def test_package_name(self):
        self.assertEqual(self.name.package, 'validate_drp')

    def test_metric_name(self):
        self.assertIsNone(self.name.metric)

    def test_spec_name(self):
        self.assertIsNone(self.name.spec)

    def test_fqn(self):
        self.assertEqual(
            self.name.fqn,
            'validate_drp')

    def test_relative_name(self):
        with self.assertRaises(AttributeError):
            self.name.relative_name

    def test_repr(self):
        self.assertEqual(
            repr(self.name),
            "Name('validate_drp')")

    def test_str(self):
        self.assertEqual(
            str(self.name),
            'validate_drp'
        )

    def test_eq(self):
        self.assertTrue(
            self.name == Name(package='validate_drp'))
        self.assertFalse(
            self.name == Name(package='validate_base'))
        self.assertFalse(
            self.name == Name(package='validate_drp',
                              metric='PA1'))

    def test_has_package(self):
        self.assertTrue(self.name.has_package)

    def test_has_metric(self):
        self.assertFalse(self.name.has_metric)

    def test_has_spec(self):
        self.assertFalse(self.name.has_spec)

    def test_has_relative(self):
        self.assertFalse(self.name.has_relative)

    def test_is_package(self):
        self.assertTrue(self.name.is_package)

    def test_is_metric(self):
        self.assertFalse(self.name.is_metric)

    def test_is_spec(self):
        self.assertFalse(self.name.is_spec)

    def test_is_fq(self):
        self.assertTrue(self.name.is_fq)

    def test_is_relative(self):
        self.assertFalse(self.name.is_relative)


if __name__ == "__main__":
    unittest.main()

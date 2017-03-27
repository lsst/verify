# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import unittest

from lsst.verify.naming import Name


class NameConstructors(unittest.TestCase):
    """Tests for Name constructor patterns."""

    def test_fully_qualified_metric_name(self):
        """Creating a fully-qualified metric name."""
        ref_name = Name(package='validate_drp', metric='PA1')

        self.assertEqual(
            ref_name,
            Name(metric='validate_drp.PA1')
        )

        # Use a Name to specifify metric field
        self.assertEqual(
            ref_name,
            Name(metric=Name(package='validate_drp', metric='PA1'))
        )

        self.assertEqual(
            ref_name,
            Name(metric='validate_drp.PA1', package='validate_drp')
        )

        self.assertEqual(
            ref_name,
            Name('validate_drp.PA1')
        )

        self.assertEqual(
            ref_name,
            Name('validate_drp.PA1', metric='PA1')
        )

        with self.assertRaises(TypeError):
            Name(metric='validate_drp.PA1', package='validate_base')

    def test_metric_name(self):
        """Creating a metric name."""
        # Using a Name as an argument
        self.assertEqual(
            Name(metric='PA1'),
            Name(metric=Name(metric='PA1'))
        )

        # Using the wrong type of name
        with self.assertRaises(TypeError):
            Name(metric=Name(spec='design_gri'))

    def test_fully_qualified_specification_name(self):
        """Creating fully-qualified specification name."""
        ref_name = Name(package='validate_drp',
                        metric='PA1',
                        spec='design_gri')

        self.assertEqual(
            ref_name,
            Name('validate_drp.PA1.design_gri')
        )

        # using a Name
        self.assertEqual(
            ref_name,
            Name(ref_name)
        )

        self.assertEqual(
            ref_name,
            Name('validate_drp.PA1.design_gri',
                 metric='PA1', spec='design_gri')
        )

    def test_relative_spec_name(self):
        """Creating a relative specification name."""
        ref_name = Name(metric='PA1',
                        spec='design_gri')

        self.assertEqual(
            ref_name,
            Name(spec='PA1.design_gri')
        )

        # Use a Name
        self.assertEqual(
            ref_name,
            Name(spec=Name(metric='PA1', spec='design_gri'))
        )

        self.assertEqual(
            ref_name,
            Name(metric='PA1', spec='PA1.design_gri')
        )

        with self.assertRaises(TypeError):
            Name(metric='PA2', spec='PA1.design_gri')

    def test_specification_name(self):
        """Creating a bare specification name."""
        ref_name = Name(spec='design_gri')

        # Ensure that Name can be used in addition to a string
        self.assertEqual(
            ref_name,
            Name(spec=Name(spec='design_gri'))
        )

        # Using the wrong type of Name
        with self.assertRaises(TypeError):
            Name(spec=Name('validate_drp.PA1'))

    def test_package_name(self):
        """Creating a package name."""
        # Ensure that Name can be used in addition to a string
        self.assertEqual(
            Name('validate_drp'),
            Name(package=Name(package='validate_drp'))
        )


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

    def test_contains(self):
        self.assertTrue(
            Name('validate_drp.PA1.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA2.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA2') in self.name
        )
        self.assertFalse(
            Name('validate_drp') in self.name
        )

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

    def test_contains(self):
        self.assertTrue(
            Name(spec='PA1.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA1.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA2.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA2') in self.name
        )
        self.assertFalse(
            Name('validate_drp') in self.name
        )

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

        with self.assertRaises(TypeError):
            Name('validate_drp.PA1.design_gri', spec='minimum')

        with self.assertRaises(TypeError):
            Name('validate_drp.PA1.design_gri', metric='PA2')

        # Can't create a specification with a metric gap
        with self.assertRaises(TypeError):
            Name(package='validate_drp', spec='design')

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

    def test_contains(self):
        self.assertFalse(
            Name(spec='design_gri') in self.name
        )
        self.assertFalse(
            Name(spec='PA1.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA1.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp.PA1') in self.name
        )
        self.assertFalse(
            Name('validate_drp') in self.name
        )

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
            self.name == Name('validate_drp')
        )
        self.assertTrue(
            self.name == Name(package='validate_drp'))
        self.assertFalse(
            self.name == Name(package='validate_base'))
        self.assertFalse(
            self.name == Name(package='validate_drp',
                              metric='PA1'))

    def test_contains(self):
        self.assertFalse(
            Name(spec='PA1.design_gri') in self.name
        )
        self.assertTrue(
            Name('validate_drp.PA1.design_gri') in self.name
        )
        self.assertTrue(
            Name('validate_drp.PA2.design_gri') in self.name
        )
        self.assertFalse(
            Name('validate_drp') in self.name
        )

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

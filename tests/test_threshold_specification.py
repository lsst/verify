# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import unittest
import operator

import astropy.units as u

from lsst.verify import Name
from lsst.verify.spec import ThresholdSpecification


class ThresholdSpecificationTestCase(unittest.TestCase):
    """Test ThresholdSpecification class functionality."""

    def test_init(self):
        """Test initialization patterns."""
        # with a fully-specified Name
        s1 = ThresholdSpecification(
            Name('validate_drp.AM1.design'),
            5. * u.marcsec,
            '<')

        # with a fully-specified string-based name
        s2 = ThresholdSpecification(
            'validate_drp.AM1.design',
            5. * u.marcsec,
            '<')
        self.assertEqual(s1, s2)

        # bad operator
        with self.assertRaises(TypeError):
            ThresholdSpecification(
                'validate_drp.AM1.design',
                5. * u.marcsec,
                '<<')

        # bad quantity
        with self.assertRaises(TypeError):
            ThresholdSpecification(
                'validate_drp.AM1.design',
                5.,
                '<')

        # bad name
        with self.assertRaises(TypeError):
            ThresholdSpecification(
                Name(metric='validate_drp'),
                5. * u.marcsec,
                '<')

    def test_equality(self):
        """test __eq__."""
        s1 = ThresholdSpecification(
            Name('validate_drp.AM1.design'),
            5. * u.marcsec,
            '<')

        # with compatible units
        s3 = ThresholdSpecification(
            Name('validate_drp.AM1.design'),
            5e-3 * u.arcsec,
            '<')
        self.assertEqual(s1, s3)

        # incompatible names
        s4 = ThresholdSpecification(
            Name('validate_drp.AM1.stretch'),
            5. * u.marcsec,
            '<')
        self.assertNotEqual(s1, s4)

        # incompatible threshold
        s5 = ThresholdSpecification(
            Name('validate_drp.AM1.design'),
            5. * u.arcsec,
            '<')
        self.assertNotEqual(s1, s5)

        # incompatible operator
        s6 = ThresholdSpecification(
            Name('validate_drp.AM1.design'),
            5. * u.marcsec,
            '>')
        self.assertNotEqual(s1, s6)

    def test_spec(self):
        """Test creating and accessing a specification from a quantity."""
        s = ThresholdSpecification('design', 5 * u.mag, '<')
        self.assertEqual(s.name, Name(spec='design'))
        self.assertEqual(s.type, 'threshold')
        self.assertEqual(s.threshold.value, 5.)
        self.assertEqual(s.threshold.unit, u.mag)
        self.assertEqual(s.operator_str, '<')
        self.assertEqual(
            repr(s),
            "ThresholdSpecification("
            "Name(spec='design'), <Quantity 5.0 mag>, '<')")

        # Test specification check method
        self.assertTrue(
            s.check(4 * u.mag)
        )
        self.assertTrue(
            s.check(4000 * u.mmag)
        )
        self.assertFalse(
            s.check(6. * u.mag)
        )
        self.assertFalse(
            s.check(6000. * u.mmag)
        )
        with self.assertRaises(u.UnitConversionError):
            s.check(2. * u.arcmin)
        with self.assertRaises(u.UnitsError):
            s.check(2.)

        # test json output
        json_data = s.json
        self.assertEqual(json_data['name'], 'design')
        self.assertEqual(json_data['threshold']['value'], 5.)
        self.assertEqual(json_data['threshold']['unit'], 'mag')
        self.assertEqual(json_data['threshold']['operator'], '<')

        # rebuild from json
        s2 = ThresholdSpecification.from_json(json_data)
        self.assertEqual(s.name, s2.name)
        self.assertEqual(s.threshold, s2.threshold)
        self.assertEqual(s.operator_str, s2.operator_str)

        # test datum output
        d = s.datum
        self.assertEqual(d.quantity, 5. * u.mag)
        self.assertEqual(d.label, 'design')

    def test_convert_operator_str(self):
        """Test that strings can be converted into operators."""
        self.assertEqual(
            ThresholdSpecification.convert_operator_str('<'),
            operator.lt)

        self.assertEqual(
            ThresholdSpecification.convert_operator_str('<='),
            operator.le)

        self.assertEqual(
            ThresholdSpecification.convert_operator_str('>'),
            operator.gt)

        self.assertEqual(
            ThresholdSpecification.convert_operator_str('>='),
            operator.ge)

        self.assertEqual(
            ThresholdSpecification.convert_operator_str('=='),
            operator.eq)

        self.assertEqual(
            ThresholdSpecification.convert_operator_str('!='),
            operator.ne)

        with self.assertRaises(ValueError):
            ThresholdSpecification.convert_operator_str('<<'),


if __name__ == "__main__":
    unittest.main()

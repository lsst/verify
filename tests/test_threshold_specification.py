#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#

import unittest
import operator

import astropy.units as u

from lsst.verify import Name, Job
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
        # Sanity-check repr
        self.assertIn('ThresholdSpecification', repr(s))
        self.assertIn('design', repr(s))
        self.assertIn('Quantity', repr(s))
        self.assertIn('mag', repr(s))
        self.assertIn('5', repr(s))

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
        s3 = ThresholdSpecification.deserialize(**json_data)
        self.assertEqual(s, s3)

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

    def test_query_metadata(self):
        job = Job(meta={'filter_name': 'r',
                        'camera': 'MegaCam'})
        s1 = ThresholdSpecification(
            Name('validate_drp.AM1.design_r'),
            5. * u.marcsec, '<',
            metadata_query={'filter_name': 'r'})
        s2 = ThresholdSpecification(
            Name('validate_drp.AM1.design_i'),
            5. * u.marcsec, '<',
            metadata_query={'filter_name': 'i'})
        s3 = ThresholdSpecification(
            Name('validate_drp.AM1.design_HSC_r'),
            5. * u.marcsec, '<',
            metadata_query={'filter_name': 'r', 'camera': 'HSC'})

        self.assertTrue(s1.query_metadata(job.meta))
        self.assertFalse(s2.query_metadata(job.meta))
        self.assertFalse(s3.query_metadata(job.meta))


if __name__ == "__main__":
    unittest.main()

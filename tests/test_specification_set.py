# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

import unittest

import astropy.units as u

from lsst.verify.naming import Name
from lsst.verify.specset import SpecificationSet
from lsst.verify.spec import ThresholdSpecification


class TestSpecificationSet(unittest.TestCase):
    """Tests for SpecificationSet basic usage."""

    def setUp(self):
        self.spec_PA1_design = ThresholdSpecification(
            'validate_drp.PA1.design', 5. * u.mmag, '<')
        self.spec_PA1_stretch = ThresholdSpecification(
            'validate_drp.PA1.stretch', 3. * u.mmag, '<')
        self.spec_PA2_design = ThresholdSpecification(
            'validate_drp.PA2_design_gri.srd', 15. * u.mmag, '<=')

        specs = [self.spec_PA1_design,
                 self.spec_PA1_stretch,
                 self.spec_PA2_design]

        self.spec_set = SpecificationSet(specifications=specs)

    def test_len(self):
        self.assertEqual(len(self.spec_set), 3)

    def test_contains(self):
        self.assertTrue(self.spec_PA1_design.name in self.spec_set)
        self.assertTrue('validate_drp.PA1.design' in self.spec_set)
        self.assertFalse(
            Name('validate_drp.WeirdMetric.design') in self.spec_set)

        # Metric, not specification
        self.assertFalse(
            'validate_drp.PA1' in self.spec_set)
        self.assertFalse(
            Name('validate_drp.PA1') in self.spec_set)

    def test_getitem(self):
        # get Specifications when given a specification name
        self.assertEqual(
            self.spec_set['validate_drp.PA1.design'],
            self.spec_PA1_design
        )

        # KeyError when requesting a metric (anything not a specification
        with self.assertRaises(KeyError):
            self.spec_set['validate_drp.PA1']


if __name__ == "__main__":
    unittest.main()

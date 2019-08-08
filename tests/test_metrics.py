# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

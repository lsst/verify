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
from __future__ import print_function, division

from collections import OrderedDict
import os
import unittest
try:
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

import astropy.units as u

from lsst.verify.errors import SpecificationResolutionError
from lsst.verify.naming import Name
from lsst.verify.specset import SpecificationSet, SpecificationPartial
from lsst.verify.spec import ThresholdSpecification
from lsst.verify.yamlutils import load_ordered_yaml


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

        partial_PA1_doc = OrderedDict([
            ('id', 'validate_drp.LPM-17-PA1#PA1-Base'),
            ('threshold', OrderedDict([
                ('unit', 'mag')
            ]))
        ])
        partial_PA1 = SpecificationPartial(partial_PA1_doc)

        self.spec_set = SpecificationSet(specifications=specs,
                                         partials=[partial_PA1])

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

    def test_iter(self):
        """Test SpecificationSet key iteration."""
        names = [n for n in self.spec_set]
        self.assertEqual(len(names), len(self.spec_set))
        for name in names:
            self.assertTrue(isinstance(name, Name))

    def test_iadd(self):
        """Test SpecifcationSet.__iadd__."""
        set1 = SpecificationSet([self.spec_PA1_design, self.spec_PA1_stretch])
        set2 = SpecificationSet([self.spec_PA1_design, self.spec_PA2_design])

        set1 += set2

        self.assertIn('validate_drp.PA1.design', set1)
        self.assertIn('validate_drp.PA1.stretch', set1)
        self.assertIn('validate_drp.PA2_design_gri.srd', set1)
        self.assertEqual(len(set1), 3)

    def test_update(self):
        """Test SpecificationSet.update()."""
        set1 = SpecificationSet([self.spec_PA1_design, self.spec_PA1_stretch])
        set2 = SpecificationSet([self.spec_PA1_design, self.spec_PA2_design])

        set1.update(set2)

        self.assertIn('validate_drp.PA1.design', set1)
        self.assertIn('validate_drp.PA1.stretch', set1)
        self.assertIn('validate_drp.PA2_design_gri.srd', set1)
        self.assertEqual(len(set1), 3)

    def test_resolve_document(self):
        """Test specification document inheritance resolution."""
        new_spec_doc = OrderedDict([
            ('name', 'PA1.relaxed'),
            ('base', ['PA1.design', 'validate_drp.LPM-17-PA1#PA1-Base']),
            ('package', 'validate_drp'),
            ('threshold', OrderedDict([
                ('value', 1)
            ]))
        ])

        resolved_doc = self.spec_set.resolve_document(new_spec_doc)

        self.assertEqual(resolved_doc['name'], 'PA1.relaxed')
        self.assertEqual(resolved_doc['threshold']['unit'], 'mag')
        self.assertEqual(resolved_doc['threshold']['value'], 1)
        self.assertEqual(resolved_doc['threshold']['operator'], '<')
        self.assertNotIn('base', resolved_doc)

    def test_unresolvable_document(self):
        """Test that SpecificationResolutionError is raised for unresolveable
        inheritance bases.
        """
        new_spec_doc = OrderedDict([
            ('name', 'PA1.unresolved'),
            ('base', 'PA1.non_existent'),
            ('package', 'validate_drp'),
            ('threshold', OrderedDict([
                ('value', 10)
            ]))
        ])

        with self.assertRaises(SpecificationResolutionError):
            self.spec_set.resolve_document(new_spec_doc)

    def test_serialization(self):
        """Test json and deserialize."""
        json_doc = self.spec_set.json
        new_spec_set = SpecificationSet.deserialize(json_doc)
        self.assertEqual(self.spec_set, new_spec_set)


class TestSpecificationSetGetterSetter(unittest.TestCase):
    """Test __setitem__, __getitem__ and __delitem__."""

    def test_mapping(self):
        spec_PA1_design = ThresholdSpecification(
            'validate_drp.PA1.design', 5. * u.mmag, '<')
        spec_PA1_stretch = ThresholdSpecification(
            'validate_drp.PA1.stretch', 3. * u.mmag, '<')

        spec_set = SpecificationSet()
        self.assertEqual(len(spec_set), 0)

        # This syntax is slightly awkward, which is why we have `insert()` too
        spec_set[spec_PA1_design.name] = spec_PA1_design
        self.assertEqual(len(spec_set), 1)
        self.assertTrue('validate_drp.PA1.design' in spec_set)

        # Insert
        spec_set.insert(spec_PA1_stretch)
        self.assertEqual(len(spec_set), 2)
        self.assertTrue('validate_drp.PA1.stretch' in spec_set)

        # Delete
        del spec_set['validate_drp.PA1.stretch']
        self.assertEqual(len(spec_set), 1)
        self.assertFalse('validate_drp.PA1.stretch' in spec_set)

        # Insert duplicate
        spec_set[spec_PA1_design.name] = spec_PA1_design
        self.assertEqual(len(spec_set), 1)
        self.assertTrue('validate_drp.PA1.design' in spec_set)

        # Insert weird value
        with self.assertRaises(TypeError):
            spec_set['validate_drp.PAX.design'] = 10

        # __setitem__ insert with a conflicting key.
        # This is why insert() is preferred.
        with self.assertRaises(KeyError):
            spec_set['validate_drp.hello.world'] = spec_PA1_design


class TestSpecificationSetLoadYamlFile(unittest.TestCase):
    """Test SpecificationSet._load_yaml_file() and sub-functions."""

    def setUp(self):
        self.test_specs_dir = os.path.join(
            os.path.dirname(__file__),
            'data/specs')

    def test_load_yaml_file(self):
        package = 'validate_drp'
        package_dirname = os.path.join(self.test_specs_dir, package)
        path = os.path.join(package_dirname, 'cfht_gri.yaml')

        spec_docs, partial_docs = SpecificationSet._load_yaml_file(
            path, package_dirname)

        self.assertEqual(len(spec_docs), 9)
        self.assertEqual(len(partial_docs), 1)

        self.assertEqual(partial_docs[0]['id'], 'validate_drp:cfht_gri#base')

    def test_process_bases(self):
        yaml_id = 'dirname/filename'
        package_name = 'package'
        bases = ['PA2_minimum_gri.srd', '#base']
        expected = ['package.PA2_minimum_gri.srd',
                    'package:dirname/filename#base']
        self.assertEqual(
            SpecificationSet._process_bases(bases, package_name, yaml_id),
            expected
        )

    def test_process_bases_known_yaml_id(self):
        """Process bases when a partial already has a yaml path."""
        yaml_id = 'dirname/filename'
        package_name = 'package'
        bases = ['PA2_minimum_gri.srd', 'otherdir/otherfile#base']
        expected = ['package.PA2_minimum_gri.srd',
                    'package:otherdir/otherfile#base']
        self.assertEqual(
            SpecificationSet._process_bases(bases, package_name, yaml_id),
            expected
        )

    def test_normalize_partial_name(self):
        self.assertEqual(
            SpecificationSet._normalize_partial_name(
                'name',
                current_yaml_id='dirname/filename',
                package='package'),
            'package:dirname/filename#name'
        )

        self.assertEqual(
            SpecificationSet._normalize_partial_name(
                'otherdir/otherfile#name',
                current_yaml_id='dirname/filename',
                package='package'),
            'package:otherdir/otherfile#name'
        )

    def test_normalize_spec_name(self):
        self.assertEqual(
            SpecificationSet._normalize_spec_name(
                'metric.spec', package='package'),
            'package.metric.spec'
        )

        # Not resolveable
        with self.assertRaises(TypeError):
            SpecificationSet._normalize_spec_name(
                'spec', package='package'),

    def test_process_specification_yaml_doc_resolved_name(self):
        doc = ("name: 'cfht_gri'\n"
               "package: 'validate_drp'\n"
               "base: ['PA2_design_gri.srd', '#base']\n")
        yaml_doc = load_ordered_yaml(StringIO(doc))
        processed = SpecificationSet._process_specification_yaml_doc(
            yaml_doc, 'cfht_gri')

        # name is unresolved
        self.assertEqual(processed['name'], 'cfht_gri')
        self.assertEqual(
            processed['base'],
            ['validate_drp.PA2_design_gri.srd', 'validate_drp:cfht_gri#base'])

    def test_process_specification_yaml_doc_unresolved_name(self):
        doc = ('name: "design_gri"\n'
               'metric: "PA1"\n'
               'package: "validate_drp"\n'
               'base: "#PA1-base"\n'
               'threshold:\n'
               '  value: 5.0\n')
        yaml_doc = load_ordered_yaml(StringIO(doc))
        processed = SpecificationSet._process_specification_yaml_doc(
            yaml_doc, 'LPM-17-PA1')

        # name is resolved
        self.assertEqual(processed['name'], 'validate_drp.PA1.design_gri')
        self.assertEqual(
            processed['base'],
            ["validate_drp:LPM-17-PA1#PA1-base"])
        self.assertEqual(
            processed['metric'],
            'PA1')
        self.assertEqual(
            processed['package'],
            'validate_drp')

    def test_process_partial_yaml_doc(self):
        doc = ("id: 'PA1-base'\n"
               "metric: 'PA1'\n"
               "package: 'validate_drp'\n"
               "threshold:\n"
               "  unit: 'mmag'\n"
               "  operator: '<='\n")
        yaml_doc = load_ordered_yaml(StringIO(doc))
        processed = SpecificationSet._process_partial_yaml_doc(
            yaml_doc, 'LPM-17-PA1')

        self.assertEqual(
            processed['id'],
            'validate_drp:LPM-17-PA1#PA1-base')
        self.assertEqual(
            processed['metric'],
            'PA1')
        self.assertEqual(
            processed['package'],
            'validate_drp')


class TestSpecificationSetLoadSinglePackage(unittest.TestCase):
    """Test SpecificationSet.load_single_package."""

    def setUp(self):
        self.test_package_dir = os.path.join(
            os.path.dirname(__file__),
            'data/specs/validate_drp')

    def test_load(self):
        spec_set = SpecificationSet.load_single_package(self.test_package_dir)
        self.assertTrue('validate_drp.PA1.design_gri' in spec_set)
        self.assertTrue('validate_drp:cfht_gri#base' in spec_set)


class TestSpecificationSetLoadMetricsPackage(unittest.TestCase):
    """Test SpecificationSet.load_metrics_package()."""

    def setUp(self):
        # defaults to verify_metrics
        self.spec_set = SpecificationSet.load_metrics_package()

    def test_contains(self):
        self.assertTrue('validate_drp.PA1.design_gri' in self.spec_set)
        self.assertTrue('validate_drp:cfht_gri/base#base' in self.spec_set)


class TestSpecificationSetNameSubset(unittest.TestCase):
    """Test creating name-based subsets from a SpecificationSet."""

    def setUp(self):
        # defaults to validate_metrics
        self.spec_set = SpecificationSet.load_metrics_package()

    def test_validate_drp_subset(self):
        package = Name('validate_drp')
        subset = self.spec_set.subset(name='validate_drp')

        self.assertTrue(isinstance(subset, type(self.spec_set)))
        self.assertTrue(len(subset) > 0)

        for spec_name, spec in subset._specs.items():
            self.assertTrue(spec_name in package)

    def test_PA1_subset(self):
        metric = Name('validate_drp.PA1')
        subset = self.spec_set.subset(name='validate_drp.PA1')

        self.assertTrue(isinstance(subset, type(self.spec_set)))
        self.assertTrue(len(subset) > 0)

        for spec_name, spec in subset._specs.items():
            self.assertTrue(spec_name in metric)


class TestSpecificationSetMetadataSubset(unittest.TestCase):
    """Test creating metadata-based or name and metadata-based subsets
    from a SpecificationSet.
    """

    def setUp(self):
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
        s4 = ThresholdSpecification(
            Name('validate_drp.PA1.design_r'),
            10 * u.mmag, '<',
            metadata_query={'filter_name': 'r'})
        self.spec_set = SpecificationSet([s1, s2, s3, s4])

    def test_metadata_subset(self):
        """Subset by metadata only."""
        subset = self.spec_set.subset(meta={'filter_name': 'r'})

        self.assertIn('validate_drp.AM1.design_r', subset)
        self.assertNotIn('validate_drp.AM1.design_i', subset)
        self.assertNotIn('validate_drp.AM1.design_HSC_r', subset)
        self.assertNotIn('validate_drp.PA1.design_HSC_r', subset)

    def test_name_and_metadata_subset(self):
        """Subset by name and metadata."""
        subset = self.spec_set.subset(name='validate_drp.AM1',
                                      meta={'filter_name': 'r'})

        self.assertIn('validate_drp.AM1.design_r', subset)
        self.assertNotIn('validate_drp.AM1.design_i', subset)
        self.assertNotIn('validate_drp.AM1.design_HSC_r', subset)
        self.assertNotIn('validate_drp.PA1.design_HSC_r', subset)

    def test_name_subset(self):
        """Subset by name."""
        subset = self.spec_set.subset(name='validate_drp.AM1')

        self.assertIn('validate_drp.AM1.design_r', subset)
        self.assertIn('validate_drp.AM1.design_i', subset)
        self.assertIn('validate_drp.AM1.design_HSC_r', subset)
        self.assertNotIn('validate_drp.PA1.design_HSC_r', subset)


if __name__ == "__main__":
    unittest.main()

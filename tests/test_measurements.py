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
import yaml

import astropy.units as u
from astropy.tests.helper import quantity_allclose

from lsst.utils.tests import TestCase
from lsst.verify import Measurement, Metric, Name, Blob, BlobSet, Datum


class MeasurementTestCase(TestCase):
    """Test lsst.verify.measurment.Measurement class."""

    def setUp(self):
        self.pa1 = Metric(
            'validate_drp.PA1',
            "The maximum rms of the unresolved source magnitude distribution "
            "around the mean value (repeatability).",
            'mmag',
            tags=['photometric', 'LPM-17'],
            reference_doc='LPM-17',
            reference_url='http://ls.st/lpm-17',
            reference_page=21)

        self.blob1 = Blob('Blob1')
        self.blob1['datum1'] = Datum(5 * u.arcsec, 'Datum 1')
        self.blob1['datum2'] = Datum(28. * u.mag, 'Datum 2')

        self.blob2 = Blob('Blob2')
        self.blob2['datumN'] = Datum(11 * u.dimensionless_unscaled, 'Count')

    def test_PA1_measurement_with_metric(self):
        """Standard metric with a given Metric instance."""
        measurement = Measurement(self.pa1, 0.002 * u.mag, blobs=[self.blob1],
                                  notes={'filter_name': 'r'})
        measurement.link_blob(self.blob2)

        measurement2 = Measurement(self.pa1, 0.002 * u.mag)

        self.assertTrue(quantity_allclose(measurement.quantity, 0.002 * u.mag))
        self.assertIsInstance(measurement.metric_name, Name)
        self.assertEqual(measurement.metric_name, Name('validate_drp.PA1'))
        self.assertEqual(measurement.metric, self.pa1)
        self.assertNotEqual(measurement.identifier, measurement2.identifier)

        # Test blob access
        self.assertIn('Blob1', measurement.blobs)
        self.assertIn('Blob2', measurement.blobs)

        # Test Datum representation
        datum = measurement.datum
        self.assertTrue(quantity_allclose(datum.quantity, 0.002 * u.mag))
        self.assertEqual(datum.label, str(self.pa1.name))
        self.assertEqual(datum.description, str(self.pa1.description))

        # Test notes (MeasurementNotes)
        self.assertEqual(measurement.notes['filter_name'], 'r')
        # Add a note
        measurement.notes['camera'] = 'MegaCam'
        self.assertEqual(measurement.notes['camera'], 'MegaCam')
        self.assertEqual(len(measurement.notes), 2)
        self.assertIn('camera', measurement.notes)
        self.assertIn('filter_name', measurement.notes)
        # Prefixed keys
        self.assertIn('validate_drp.PA1.camera', measurement.notes)
        # test iteration
        iterkeys = set([key for key in measurement.notes])
        self.assertEqual(len(iterkeys), 2)
        self.assertEqual(set(iterkeys), set(measurement.notes.keys()))
        itemkeys = set()
        for key, value in measurement.notes.items():
            self.assertEqual(measurement.notes[key], value)
            itemkeys.add(key)
        self.assertEqual(itemkeys, iterkeys)
        # Test update
        measurement.notes.update({'photometric': True, 'facility': 'CFHT'})
        self.assertIn('photometric', measurement.notes)
        # Test delete
        del measurement.notes['photometric']
        self.assertNotIn('photometric', measurement.notes)

        # Test serialization
        json_doc = measurement.json
        # Units should be cast to those of the metric
        self.assertEqual(json_doc['unit'], 'mmag')
        self.assertFloatsAlmostEqual(json_doc['value'], 2.0)
        self.assertEqual(json_doc['identifier'], measurement.identifier)
        self.assertIsInstance(json_doc['blob_refs'], list)
        self.assertIn(self.blob1.identifier, json_doc['blob_refs'])
        self.assertIn(self.blob2.identifier, json_doc['blob_refs'])
        # No extras, so should not be serialized
        self.assertNotIn(measurement.extras.identifier, json_doc['blob_refs'])

        # Test deserialization
        new_measurement = Measurement.deserialize(
            blobs=BlobSet([self.blob1, self.blob2]),
            **json_doc)
        # shim in original notes; normally these are deserialized via the
        # Job object.
        new_measurement.notes.update(measurement.notes)
        self.assertEqual(measurement, new_measurement)
        self.assertEqual(measurement.identifier, new_measurement.identifier)
        self.assertIn('Blob1', measurement.blobs)
        self.assertIn('Blob2', measurement.blobs)

    def test_PA1_measurement_without_metric(self):
        """Test a measurement without a Metric instance."""
        measurement = Measurement('validate_drp.PA1', 0.002 * u.mag)

        self.assertIsInstance(measurement.metric_name, Name)
        self.assertEqual(measurement.metric_name, Name('validate_drp.PA1'))
        self.assertIsNone(measurement.metric)

        json_doc = measurement.json
        # Units are not converted
        self.assertEqual(json_doc['unit'], 'mag')
        self.assertFloatsAlmostEqual(json_doc['value'], 0.002)

        new_measurement = Measurement.deserialize(**json_doc)
        self.assertEqual(measurement, new_measurement)
        self.assertEqual(measurement.identifier, new_measurement.identifier)

    def test_PA1_deferred_metric(self):
        """Test a measurement when the Metric instance is added later."""
        measurement = Measurement('PA1', 0.002 * u.mag)

        self.assertIsNone(measurement.metric)
        self.assertEqual(measurement.metric_name, Name(metric='PA1'))

        # Try adding in a metric with the wrong units to existing quantity
        other_metric = Metric('testing.other', 'Incompatible units', 'arcsec')
        with self.assertRaises(TypeError):
            measurement.metric = other_metric

        # Add metric in; the name should also update
        measurement.metric = self.pa1
        self.assertEqual(measurement.metric, self.pa1)
        self.assertEqual(measurement.metric_name, self.pa1.name)

    def test_PA1_deferred_quantity(self):
        """Test a measurement where the quantity is added later."""
        measurement = Measurement(self.pa1)
        json_doc = measurement.json
        self.assertIsNone(json_doc['unit'])
        self.assertIsNone(json_doc['value'])

        with self.assertRaises(TypeError):
            # wrong units
            measurement.quantity = 5 * u.arcsec

        measurement.quantity = 5 * u.mmag
        quantity_allclose(measurement.quantity, 5 * u.mmag)

    def test_creation_with_extras(self):
        """Test creating a measurement with an extra."""
        measurement = Measurement(
            self.pa1, 5. * u.mmag,
            extras={'extra1': Datum(10. * u.arcmin, 'Extra 1')})

        self.assertIn(str(self.pa1.name), measurement.blobs)
        self.assertIn('extra1', measurement.extras)

        json_doc = measurement.json
        self.assertIn(measurement.extras.identifier, json_doc['blob_refs'])

        blobs = BlobSet([b for k, b in measurement.blobs.items()])
        new_measurement = Measurement.deserialize(blobs=blobs, **json_doc)
        self.assertIn('extra1', new_measurement.extras)
        self.assertEqual(measurement, new_measurement)
        self.assertEqual(measurement.identifier, new_measurement.identifier)

    def test_deferred_extras(self):
        """Test adding extras to an existing measurement."""
        measurement = Measurement(self.pa1, 5. * u.mmag)

        self.assertIn(str(self.pa1.name), measurement.blobs)

        measurement.extras['extra1'] = Datum(10. * u.arcmin, 'Extra 1')
        self.assertIn('extra1', measurement.extras)

    def test_quantity_coercion(self):
        # strings can't be changed into a Quantity
        with self.assertRaises(TypeError):
            Measurement('test_metric', quantity='hello')
        # objects can't be a Quantity
        with self.assertRaises(TypeError):
            Measurement('test_metric', quantity=int)
        m = Measurement('test_metric', quantity=5)
        self.assertEqual(m.quantity, 5)
        m = Measurement('test_metric', quantity=5.1)
        self.assertEqual(m.quantity, 5.1)

    def test_str(self):
        metric = 'test.cmodel_mag'
        value = 1235 * u.mag
        m = Measurement(metric, value)
        self.assertEqual(str(m), "test.cmodel_mag: 1235.0 mag")

    def test_repr(self):
        metric = 'test.cmodel_mag'
        self.assertEqual(
            repr(Measurement(metric)),
            "Measurement('test.cmodel_mag', None)")
        value = 1235 * u.mag
        self.assertEqual(
            repr(Measurement(metric, value)),
            "Measurement('test.cmodel_mag', <Quantity 1235. mag>)")

        self.assertEqual(
            repr(Measurement(metric, value, [self.blob1])),
            "Measurement('test.cmodel_mag', <Quantity 1235. mag>, "
            f"blobs=[{self.blob1!r}])"
        )

        notes = {metric + '.filter_name': 'r'}
        extras = {'extra1': Datum(10. * u.arcmin, 'Extra 1')}
        self.assertEqual(
            repr(Measurement(metric, value, notes=notes, blobs=[self.blob1],
                             extras=extras)),
            "Measurement('test.cmodel_mag', <Quantity 1235. mag>, "
            f"blobs=[{self.blob1!r}], extras={extras!r}, notes={notes!r})"
        )

    def _check_yaml_round_trip(self, old_measurement):
        persisted = yaml.dump(old_measurement)
        new_measurement = yaml.safe_load(persisted)

        self.assertEqual(old_measurement, new_measurement)
        # These fields don't participate in Measurement equality
        self.assertEqual(old_measurement.identifier,
                         new_measurement.identifier)
        self.assertEqual(old_measurement.blobs,
                         new_measurement.blobs)
        self.assertEqual(old_measurement.extras,
                         new_measurement.extras)

    def test_yamlpersist_basic(self):
        measurement = Measurement('validate_drp.PA1', 0.002 * u.mag)
        self._check_yaml_round_trip(measurement)

    def test_yamlpersist_complex(self):
        measurement = Measurement(
            self.pa1,
            5. * u.mmag,
            notes={'filter_name': 'r'},
            blobs=[self.blob1],
            extras={'extra1': Datum(10. * u.arcmin, 'Extra 1')}
        )
        self._check_yaml_round_trip(measurement)


if __name__ == "__main__":
    unittest.main()

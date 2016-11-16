#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import unittest

import astropy.units as u

from lsst.validate.base import (MeasurementBase, Metric, Datum, BlobBase,
                                DeserializedMeasurement, Job)


class DemoBlob(BlobBase):
    """Example Blob class."""

    name = 'demo'

    def __init__(self):
        BlobBase.__init__(self)

        self.register_datum(
            'mag',
            quantity=5 * u.mag,
            description='Magnitude')

        self.register_datum(
            'updateable_mag',
            quantity=5 * u.mag,
            description='Magnitude')


class DemoMeasurement(MeasurementBase):

    metric = None

    def __init__(self):
        MeasurementBase.__init__(self)
        self.metric = Metric('Test', 'Test metric', '<')
        self.quantity = 5. * u.mag

        # link a blob
        self.ablob = DemoBlob()

        # datum-based parameters
        self.register_parameter(
            'datum_param',
            datum=Datum(10 * u.arcsec),
            description='A datum')
        # set this parameter later
        self.register_parameter(
            'deferred_datum_param',
            description='A datum')

        # quantity-based parameter
        self.register_parameter(
            'q_param',
            quantity=10 * u.arcsec,
            description='A quantity')
        # set this parameter later
        self.register_parameter(
            'deferred_q_param',
            description='A quantity')

        # string-based parameters
        self.register_parameter('str_param', 'test_string',
                                description='A string')
        # set this parameter later
        self.register_parameter('deferred_str_param',
                                description='A string')

        # boolean parameters
        self.register_parameter('bool_param', False,
                                description='A boolean')
        # set this parameter later
        self.register_parameter('deferred_bool_param',
                                description='A boolean')

        # quantity-based extras
        self.register_extra('q_extra', quantity=1000. * u.microJansky,
                            description='Quantity extra')

        # none-type extra
        self.register_extra('none_extra', label='none type',
                            description='None type Extra')
        self.none_extra = None


class MeasurementBaseTestCase(unittest.TestCase):
    """Test Mesaurement class (via MeasurementBase) functionality."""

    def setUp(self):
        self.meas = DemoMeasurement()

    def tearDown(self):
        pass

    def test_label(self):
        self.assertEqual(self.meas.label, 'Test')

    def test_quantity(self):
        """Test that a measurement's quantity is an astropy Quantity
        and that the measurement uses the QuantityAttributeMixin.
        """
        self.assertEqual(self.meas.quantity.value, 5.)
        self.assertEqual(self.meas.unit_str, 'mag')
        self.assertEqual(self.meas.unit, u.mag)

    def test_quantity_datum(self):
        """Test representation of measurement's quantity as a datum."""
        d = self.meas.datum
        self.assertEqual(self.meas.quantity, d.quantity)
        self.assertEqual(self.meas.unit, d.unit)
        self.assertEqual(self.meas.unit_str, d.unit_str)

    def test_json(self):
        """Test basic structure of the json output."""
        doc = self.meas.json
        self.assertEqual(doc['metric']['name'], 'Test')
        self.assertEqual(doc['value'], 5)
        self.assertEqual(doc['unit'], 'mag')
        self.assertIn('parameters', doc)
        self.assertIn('extras', doc)
        self.assertIn('blobs', doc)
        self.assertEqual(doc['spec_name'], None)
        self.assertEqual(doc['filter_name'], None)

    def test_json_deserialization(self):
        job = Job(measurements=[self.meas])
        job_json = job.json

        meas_doc = job_json['measurements'][0]
        blobs_doc = job_json['blobs']

        # Rebuild from JSON
        m2 = DeserializedMeasurement.from_json(meas_doc, blobs_json=blobs_doc)
        self.assertEqual(self.meas.metric.name, m2.metric.name)
        self.assertEqual(self.meas.quantity, m2.quantity)
        for k, param in self.meas.parameters.items():
            self.assertEqual(param.quantity, m2.parameters[k].quantity)
        for k, extra in self.meas.extras.items():
            self.assertEqual(extra.quantity, m2.extras[k].quantity)
        for k, blob in self.meas._linked_blobs.items():
            for kk, datum in blob.datums.items():
                print(m2._linked_blobs.keys())
                self.assertEqual(datum.quantity, m2._linked_blobs[k].datums[kk].quantity)

    def test_datum_param(self):
        self.assertEqual(self.meas.datum_param, 10 * u.arcsec)
        self.assertEqual(self.meas.parameters['datum_param'].quantity,
                         10 * u.arcsec)
        self.assertEqual(self.meas.parameters['datum_param'].unit,
                         u.arcsec)
        self.assertEqual(self.meas.parameters['datum_param'].label,
                         'datum_param')
        self.assertEqual(self.meas.parameters['datum_param'].description,
                         'A datum')

        # test json output
        doc = self.meas.json['parameters']['datum_param']
        self.assertEqual(doc['value'], 10)
        self.assertEqual(doc['unit'], 'arcsec')
        self.assertEqual(doc['label'], 'datum_param')
        self.assertEqual(doc['description'], 'A datum')

    def test_deferred_datum_param(self):
        self.assertEqual(self.meas.deferred_datum_param, None)

        self.meas.deferred_datum_param = 10. * u.arcsec

        self.assertEqual(self.meas.deferred_datum_param, 10 * u.arcsec)
        self.assertEqual(self.meas.parameters['deferred_datum_param'].quantity,
                         10 * u.arcsec)
        self.assertEqual(self.meas.parameters['deferred_datum_param'].unit,
                         u.arcsec)
        self.assertEqual(self.meas.parameters['deferred_datum_param'].label,
                         'deferred_datum_param')
        self.assertEqual(
            self.meas.parameters['deferred_datum_param'].description,
            'A datum')

    def test_quantity_param(self):
        self.assertEqual(self.meas.q_param, 10 * u.arcsec)
        self.assertEqual(self.meas.parameters['q_param'].quantity,
                         10 * u.arcsec)
        self.assertEqual(self.meas.parameters['q_param'].unit,
                         u.arcsec)
        self.assertEqual(self.meas.parameters['q_param'].label,
                         'q_param')
        self.assertEqual(self.meas.parameters['q_param'].description,
                         'A quantity')

        # test json output
        doc = self.meas.json['parameters']['q_param']
        self.assertEqual(doc['value'], 10)
        self.assertEqual(doc['unit'], 'arcsec')
        self.assertEqual(doc['label'], 'q_param')
        self.assertEqual(doc['description'], 'A quantity')

    def test_deferred_quantity_param(self):
        self.assertEqual(self.meas.deferred_q_param, None)

        self.meas.deferred_q_param = 10. * u.arcsec

        self.assertEqual(self.meas.deferred_q_param, 10 * u.arcsec)
        self.assertEqual(self.meas.parameters['deferred_q_param'].quantity,
                         10 * u.arcsec)
        self.assertEqual(self.meas.parameters['deferred_q_param'].unit,
                         u.arcsec)
        self.assertEqual(self.meas.parameters['deferred_q_param'].label,
                         'deferred_q_param')
        self.assertEqual(self.meas.parameters['deferred_q_param'].description,
                         'A quantity')

    def test_str_param(self):
        self.assertEqual(self.meas.str_param, 'test_string')
        self.assertEqual(self.meas.parameters['str_param'].quantity,
                         'test_string')
        self.assertEqual(self.meas.parameters['str_param'].label, 'str_param')
        self.assertEqual(self.meas.parameters['str_param'].description,
                         'A string')

    def test_deferred_str_param(self):
        self.meas.deferred_str_param = 'deferred_test_string'
        self.assertEqual(self.meas.parameters['deferred_str_param'].quantity,
                         'deferred_test_string')
        self.assertEqual(self.meas.parameters['deferred_str_param'].label,
                         'deferred_str_param')
        self.assertEqual(
            self.meas.parameters['deferred_str_param'].description,
            'A string')

    def test_bool_param(self):
        self.assertEqual(self.meas.bool_param, False)
        self.assertEqual(self.meas.parameters['bool_param'].quantity, False)
        self.assertEqual(self.meas.parameters['bool_param'].label,
                         'bool_param')
        self.assertEqual(self.meas.parameters['bool_param'].description,
                         'A boolean')

    def test_deferred_bool_param(self):
        self.meas.deferred_bool_param = True
        self.assertEqual(self.meas.parameters['deferred_bool_param'].quantity,
                         True)
        self.assertEqual(self.meas.parameters['deferred_bool_param'].label,
                         'deferred_bool_param')
        self.assertEqual(
            self.meas.parameters['deferred_bool_param'].description,
            'A boolean')

    def test_quantity_extra(self):
        self.assertEqual(self.meas.q_extra, 1000. * u.microJansky)
        self.assertEqual(self.meas.extras['q_extra'].quantity,
                         1000. * u.microJansky)
        self.assertEqual(self.meas.extras['q_extra'].label, 'q_extra')
        self.assertEqual(self.meas.extras['q_extra'].description,
                         'Quantity extra')

        doc = self.meas.json['extras']['q_extra']
        self.assertEqual(doc['value'], 1000.)
        self.assertEqual(doc['unit'], 'uJy')
        self.assertEqual(doc['label'], 'q_extra')
        self.assertEqual(doc['description'], 'Quantity extra')

    def test_blob_link(self):
        doc = self.meas.json
        self.assertEqual(self.meas.ablob.identifier, doc['blobs']['ablob'])


class DemoNoneQuantityMeasurement(MeasurementBase):
    """Measurement whose quantity is None."""

    metric = None

    def __init__(self):
        MeasurementBase.__init__(self)
        self.metric = Metric('Test', 'Test metric', '<')
        self.quantity = None


class MeasurementBaseNoneQuantityTestCase(unittest.TestCase):
    """Test Mesaurement class (via MeasurementBase) functionality."""

    def setUp(self):
        self.meas = DemoNoneQuantityMeasurement()

    def test_none_quantity(self):
        self.assertTrue(self.meas.quantity is None)

    def test_none_json(self):
        data = self.meas.json
        self.assertTrue(data['value'] is None)


if __name__ == "__main__":
    unittest.main()

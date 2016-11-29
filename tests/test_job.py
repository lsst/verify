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


class JobTestCase(unittest.TestCase):
    """Test Job classes."""

    def setUp(self):
        meas = DemoMeasurement()
        self.job = Job(measurements=[meas])

    def test_json(self):
        job_json = self.job.json

        self.assertTrue(isinstance(job_json['measurements'], list))
        self.assertEqual(len(job_json['measurements']), 1)
        self.assertTrue(isinstance(job_json['blobs'], list))
        self.assertEqual(len(job_json['blobs']), 1)

        # Rebuild from JSON
        job2 = Job.from_json(job_json)
        for m1, m2 in zip(self.job.measurements, job2.measurements):
            self.assertEqual(m1.quantity, m2.quantity)

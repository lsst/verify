# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function

import astropy.units as u
import unittest

from lsst.verify import (Job, Metric, ThresholdSpecification, Measurement,
                         MeasurementSet, MetricSet, SpecificationSet, Datum)


class JobTestCase(unittest.TestCase):
    """Test Job classes."""

    def setUp(self):
        # Mock metrics
        self.metric_photrms = Metric('test.PhotRms', 'Photometric RMS', 'mmag')
        self.metric_set = MetricSet([self.metric_photrms])

        # Mock specifications
        self.spec_photrms_design = ThresholdSpecification(
            'test.PhotRms.design', 20. * u.mmag, '<'
        )
        self.spec_set = SpecificationSet([self.spec_photrms_design])

        # Mock measurements
        self.meas_photrms = Measurement(self.metric_photrms, 15 * u.mmag)
        self.meas_photrms.extras['n_stars'] = Datum(
            250,
            label='N stars',
            description='Number of stars included in RMS estimate')
        self.measurement_set = MeasurementSet([self.meas_photrms])

    def test_job(self):
        """Create a Job from object sets."""
        job = Job(metrics=self.metric_set, specs=self.spec_set,
                  measurements=self.measurement_set)

        # Test object access via properties
        self.assertIn('test.PhotRms.design', job.specs)
        self.assertIn('test.PhotRms', job.metrics)
        self.assertIn('test.PhotRms', job.measurements)

        json_doc = job.json

        self.assertIn('measurements', json_doc)
        self.assertEqual(len(json_doc['measurements']), len(job.measurements))

        self.assertIn('blobs', json_doc)

        self.assertIn('metrics', json_doc)
        self.assertEqual(len(json_doc['metrics']), len(job.metrics))

        self.assertIn('specs', json_doc)
        self.assertEqual(len(json_doc['specs']), len(job.specs))

        new_job = Job.deserialize(**json_doc)
        self.assertEqual(job, new_job)


if __name__ == "__main__":
    unittest.main()

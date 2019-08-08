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

import astropy.units as u
import unittest

from lsst.verify import (Job, Metric, ThresholdSpecification, Measurement,
                         MeasurementSet, MetricSet, SpecificationSet, Datum,
                         Blob)


class JobTestCase(unittest.TestCase):
    """Test Job classes."""

    def setUp(self):
        # Mock metrics
        self.metric_photrms = Metric('test.PhotRms', 'Photometric RMS', 'mmag')
        self.metric_photmed = Metric('test.PhotMedian',
                                     'Median magntidue', 'mag')
        self.metric_set = MetricSet([self.metric_photrms, self.metric_photmed])

        # Mock specifications
        self.spec_photrms_design = ThresholdSpecification(
            'test.PhotRms.design', 20. * u.mmag, '<'
        )
        self.spec_set = SpecificationSet([self.spec_photrms_design])

        # Mock measurements
        self.meas_photrms = Measurement(
            self.metric_photrms, 15 * u.mmag,
            notes={'note': 'value'})
        self.meas_photrms.extras['n_stars'] = Datum(
            250,
            label='N stars',
            description='Number of stars included in RMS estimate')
        self.measurement_set = MeasurementSet([self.meas_photrms])

        # Metrics for Job 2
        self.metric_test_2 = Metric('test2.SourceCount', 'Source Count', '')
        self.blob_test_2 = Blob(
            'test2_blob',
            sn=Datum(50 * u.dimensionless_unscaled, label='S/N'))
        self.metric_set_2 = MetricSet([self.metric_test_2])

        # Specifications for Job 2
        self.spec_test_2 = ThresholdSpecification(
            'test2.SourceCount.design', 100 * u.dimensionless_unscaled, '>=')
        self.spec_set_2 = SpecificationSet([self.spec_test_2])

        # Measurements for Job 2
        self.meas_test_2_SourceCount = Measurement(
            self.metric_test_2, 200 * u.dimensionless_unscaled)
        self.meas_test_2_SourceCount.link_blob(self.blob_test_2)
        self.measurement_set_2 = MeasurementSet([self.meas_test_2_SourceCount])

    def test_job(self):
        """Create a Job from object sets."""
        job = Job(metrics=self.metric_set, specs=self.spec_set,
                  measurements=self.measurement_set)

        # Test object access via properties
        self.assertIn('test.PhotRms.design', job.specs)
        self.assertIn('test.PhotRms', job.metrics)
        self.assertIn('test.PhotRms', job.measurements)

        # Test metadata access
        self.assertIn('test.PhotRms.note', job.meta)
        self.assertEqual(job.meta['test.PhotRms.note'], 'value')
        # measurement metadata is always prefixed
        self.assertNotIn('note', job.meta)

        job.meta['job-level-key'] = 'yes'
        self.assertEqual(job.meta['job-level-key'], 'yes')
        self.assertIn('job-level-key', job.meta)

        self.assertEqual(len(job.meta), 2)

        job.meta.update({'test.PhotRms.note2': 'foo',
                         'dataset': 'ci_hsc'})
        # note2 should be in measurement notes
        self.assertEqual(
            job.measurements['test.PhotRms'].notes['note2'],
            'foo')
        self.assertEqual(job.meta['dataset'], 'ci_hsc')
        # Delete measurement and job-level metadata
        del job.meta['test.PhotRms.note2']
        self.assertNotIn('test.PhotRms.note2', job.meta)
        self.assertNotIn('note2', job.measurements['test.PhotRms'].notes)
        del job.meta['dataset']
        self.assertNotIn('dataset', job.meta)

        self.assertEqual(
            set(job.meta.keys()),
            set(['job-level-key', 'test.PhotRms.note'])
        )
        self.assertEqual(
            set([key for key in job.meta]),
            set(['job-level-key', 'test.PhotRms.note'])
        )
        keys = set()
        for key, value in job.meta.items():
            keys.add(key)
        self.assertEqual(keys, set(['job-level-key', 'test.PhotRms.note']))

        # Add a new measurement
        m = Measurement('test.PhotMedian', 28.5 * u.mag,
                        notes={'aperture_corr': True})
        job.measurements.insert(m)
        self.assertIn('test.PhotMedian', job.measurements)
        self.assertEqual(job.meta['test.PhotMedian.aperture_corr'], True)

        # Test serialization
        json_doc = job.json

        self.assertIn('measurements', json_doc)
        self.assertEqual(len(json_doc['measurements']), len(job.measurements))

        self.assertIn('blobs', json_doc)

        self.assertIn('metrics', json_doc)
        self.assertEqual(len(json_doc['metrics']), len(job.metrics))

        self.assertIn('specs', json_doc)
        self.assertEqual(len(json_doc['specs']), len(job.specs))

        self.assertIn('meta', json_doc)
        self.assertEqual(len(json_doc['meta']), len(job.meta))

        new_job = Job.deserialize(**json_doc)
        self.assertEqual(job, new_job)

        # check job-to-measurement metadata deserialization
        self.assertEqual(
            new_job.measurements['test.PhotRms'].notes['note'],
            'value')
        self.assertEqual(
            new_job.meta['test.PhotRms.note'],
            'value')
        self.assertEqual(
            new_job.meta['job-level-key'],
            'yes')

    def test_job_iadd(self):
        job_1 = Job(metrics=self.metric_set, specs=self.spec_set,
                    measurements=self.measurement_set)
        job_2 = Job(metrics=self.metric_set_2, specs=self.spec_set_2,
                    measurements=self.measurement_set_2)

        job_1 += job_2

        self.assertIn(self.metric_photrms.name, job_1.metrics)
        self.assertIn(self.metric_test_2.name, job_1.metrics)
        self.assertIn('test.PhotRms.design', job_1.specs)
        self.assertIn('test2.SourceCount.design', job_1.specs)
        self.assertIn('test.PhotRms', job_1.measurements)
        self.assertIn('test2.SourceCount', job_1.measurements)
        self.assertIn('test.PhotRms', job_1.measurements['test.PhotRms'].blobs)
        self.assertIn(
            'test2_blob',
            job_1.measurements['test2.SourceCount'].blobs)

    def test_metric_package_reload(self):
        # Create a Job without Metric definitions
        meas = Measurement('validate_drp.PA1', 15 * u.mmag)
        measurement_set = MeasurementSet([meas])

        job = Job(measurements=measurement_set)
        job.reload_metrics_package('verify_metrics')

        # Should now have metrics and specs
        self.assertTrue(len(job.specs) > 0)
        self.assertTrue(len(job.metrics) > 0)
        self.assertIsInstance(
            job.measurements['validate_drp.PA1'].metric,

            Metric)


if __name__ == "__main__":
    unittest.main()

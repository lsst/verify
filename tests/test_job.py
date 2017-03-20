#!/usr/bin/env python
# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function
from builtins import zip

import unittest

from lsst.validate.base import Job


@unittest.skip("FIXME DM-8477 re-instance when Job is working again")
class JobTestCase(unittest.TestCase):
    """Test Job classes."""

    def setUp(self):
        # self.job = Job(measurements=[meas])
        pass

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

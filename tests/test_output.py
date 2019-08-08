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

import json
import unittest
import os

import astropy.units as u
from astropy.tests.helper import quantity_allclose

import lsst.verify


def load_json(filename):
    with open(filename) as logfile:
        json_doc = json.load(logfile)
    return json_doc


class OutputQuantitiesTestCase(unittest.TestCase):

    def tearDown(self):
        if hasattr(self, 'output_filename'):
            if os.path.exists(self.output_filename):
                os.remove(self.output_filename)

    def test_output_quantities(self):
        data = {'thing1': 10 * u.mmag,
                'thing2': 5.2 * u.dimensionless_unscaled}

        self.output_filename = lsst.verify.output_quantities(
            'testing', data)
        self.assertEqual(self.output_filename, 'testing.verify.json')

        json_doc = load_json(self.output_filename)
        self.assertEqual(len(json_doc['measurements']), 2)
        self.assertEqual(len(json_doc['metrics']), 0)
        self.assertEqual(len(json_doc['specs']), 0)
        self.assertEqual(len(json_doc['blobs']), 0)

        job = lsst.verify.Job.deserialize(**json_doc)

        self.assertEqual(len(job.measurements), 2)
        quantity_allclose(
            job.measurements['testing.thing1'].quantity,
            data['thing1'])
        quantity_allclose(
            job.measurements['testing.thing2'].quantity,
            data['thing2'])


if __name__ == "__main__":
    unittest.main()

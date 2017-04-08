# See COPYRIGHT file at the top of the source tree.
from __future__ import absolute_import, division, print_function

import json

from .measurement import MeasurementSet, Measurement


def output_measurements(package_name, measurement_dict):
    measurements = []
    for name, value in measurement_dict.items():
        measurements.append(Measurement('.'.join((package_name, name)), value))
    measurement_set = MeasurementSet(package_name, measurements)

    out_filename = '{}.measurements'.format(name)
    with open(out_filename, 'w') as outfile:
        json.dump(measurement_set, outfile)
    return out_filename

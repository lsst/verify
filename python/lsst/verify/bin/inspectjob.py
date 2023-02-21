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
"""Print the measurements and metadata in lsst.verify JSON files.

This script takes as arguments one or more lsst.verify JSON files, and prints
the top-level metadata and a summary of any measurements.

This script does not print information about metrics or specifications.
"""

__all__ = ["main", "inspect_job"]

import argparse
import json

from lsst.verify import Job


def _is_measurement_metadata(key, metrics):
    """Test whether a job-level metadata key is really measurement metadata.

    Parameters
    ----------
    key : `str`
        The metadata key to test.
    metrics : iterable of `lsst.verify.Name` or of `str`
        The metrics recorded in the job.

    Returns
    -------
    result : `bool`
        `True` if ``key`` represents measurement metadata, `False` if it
        represents purely job-level metadata.
    """
    for metric in metrics:
        if str(metric) in key:
            return True
    return False


def _simplify_key(key, prefix):
    """Remove a prefix from a key, if it's present.

    Parameters
    ----------
    key : `str`
        The key to simplify.
    prefix : `str`
        The prefix to remove from ``key``.

    Returns
    -------
    simplifiedKey : `str`
        ``key`` with any initial ``prefix`` removed
    """
    if key.startswith(prefix):
        return key.replace(prefix, "", 1)
    else:
        return key


def _get_first_col_width(job):
    """Return the width to use for the output's first column.

    This column displays metadata and metric keys.

    Parameters
    ----------
    job : `lsst.verify.Job`
        The Job to print.

    Returns
    -------
    width : `int`
        The minimum width to use to format the Job's values. May be 0 if the
        Job is empty.
    """
    max_meta = max(len(key) for key in job.meta) if job.meta else 0
    max_meas = max(len(str(metric)) for metric in job.measurements) \
        if job.measurements else 0

    return max(max_meta, max_meas)


def inspect_job(job):
    """Present the measurements in a Job object.

    The measurements and any metadata are printed to standard output.

    Parameters
    ----------
    job : `lsst.verify.Job`
        The Job to examine.
    """
    # Leave enough space for output so that all '=' characters are aligned
    max_metric_length = _get_first_col_width(job)

    print("Common metadata:")
    for key, value in job.meta.items():
        if _is_measurement_metadata(key, job.measurements.keys()):
            continue
        print("%*s = %s" % (max_metric_length, key, value))

    print("\nMeasurements:")
    for metric, measurement in job.measurements.items():
        if (measurement.quantity.value < 1e-2):
            pretty_quantity = '{0.value:0.2e} {0.unit}'.format(measurement.quantity)
        else:
            pretty_quantity = '{0.value:0.2f} {0.unit}'.format(measurement.quantity)
        if measurement.notes:
            prefix = str(measurement.metric_name) + "."
            # Raw representation of measurement.notes hard to read
            simple_notes = {_simplify_key(key, prefix): value
                            for key, value in measurement.notes.items()}
            print("%*s = %10s (%s)"
                  % (max_metric_length, metric, pretty_quantity, simple_notes))
        else:
            print("%*s = %10s" % (max_metric_length, metric, pretty_quantity))


def build_argparser():
    """Construct an argument parser for the ``inspect_job.py`` script.

    Returns
    -------
    argparser : `argparse.ArgumentParser`
        The argument parser that defines the ``inspect_job.py`` command-line
        interface.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='More information is available at https://pipelines.lsst.io.')
    parser.add_argument(
        'json_paths',
        nargs='+',
        metavar='json',
        help='lsst.verify JSON file, or files (``*verify.json``).')
    return parser


def main():
    """Present all Job files.
    """
    args = build_argparser().parse_args()
    for filename in args.json_paths:
        if len(args.json_paths) > 1:
            print("\n%s:" % filename)
        with open(filename) as f:
            job = Job.deserialize(**json.load(f))
        inspect_job(job)

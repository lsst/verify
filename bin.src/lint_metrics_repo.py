#!/usr/bin/env python
"""
Validate the contents of a RetricsRepo, by constructing all of its
constitutent MetricSets and their Metrics.
"""

import os
import argparse

import lsst.pex.exceptions
from lsst.utils import getPackageDir
from lsst.validate.base import MetricRepo


def main():
    try:
        default_metrics_dir = os.path.join(
            getPackageDir('validate_metrics'),
            'metrics')
    except lsst.pex.exceptions.NotFoundError:
        default_metrics_dir = None

    print(default_metrics_dir)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "repo",
        default=default_metrics_dir,
        type=str,
        nargs='?',
        help="Directory containing the MetricRepo to be checked.")
    args = parser.parse_args()

    metric_repo = MetricRepo.from_path(args.repo)

    print("Successfully constructed a MetricRepo from {}".format(args.repo))
    print()
    print(metric_repo)


if __name__ == "__main__":
    main()

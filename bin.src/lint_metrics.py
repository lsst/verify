#!/usr/bin/env python
"""
Validate the contents of an LSST Verification Framework metrics package.

A metrics package contains, minimally, two root directories:

1. metrics/ - contains one YAML file per LSST Science Pipelines package
   that define metrics measured by that package.

2. specs/ - contains sub-directories named after LSST Science Pipelines
   packages. Specifications are defined in YAML files within those
   sub-directories.
"""

import os
import argparse

import lsst.pex.exceptions
from lsst.utils import getPackageDir
from lsst.verify import MetricRepo, SpecificationSet


def main():
    try:
        default_metrics_package_dir = getPackageDir('verify_metrics')
    except lsst.pex.exceptions.NotFoundError:
        default_metrics_package_dir = None

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "package_dir",
        default=default_metrics_package_dir,
        type=str,
        nargs='?',
        help="Filepath of the metrics package to be checked.")
    args = parser.parse_args()

    print('Linting {}.'.format(args.package_dir))

    metric_repo = MetricRepo.from_metrics_dir(
        os.path.join(args.package_dir, 'metrics'))
    print('Passed: metrics/')
    print('\tParsed {0:d} metric sets.'.format(len(metric_repo)))

    spec_set = SpecificationSet.load_metrics_package(args.package_dir)
    print('Passed: specs/')
    print('\tParsed {0:d} specifications.'.format(len(spec_set)))

    print("\nAll tests passed.")


if __name__ == "__main__":
    main()

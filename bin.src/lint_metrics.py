#!/usr/bin/env python
#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
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
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
"""
Validate the contents of an LSST Verification Framework metrics package.

A metrics package contains, minimally, two root directories:

1. metrics/ - contains one YAML file per LSST Science Pipelines package
   that define metrics measured by that package.

2. specs/ - contains sub-directories named after LSST Science Pipelines
   packages. Specifications are defined in YAML files within those
   sub-directories.
"""

import argparse

import lsst.pex.exceptions
from lsst.utils import getPackageDir
from lsst.verify import MetricSet, SpecificationSet


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

    metric_repo = MetricSet.load_metrics_package(args.package_dir)
    print('Passed: metrics/')
    print('\tParsed {0:d} metric sets.'.format(len(metric_repo)))

    spec_set = SpecificationSet.load_metrics_package(args.package_dir)
    print('Passed: specs/')
    print('\tParsed {0:d} specifications.'.format(len(spec_set)))

    print("\nAll tests passed.")


if __name__ == "__main__":
    main()

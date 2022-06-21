# This file is part of verify.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Summarize measured metric values in one butler repo, or difference values
between two repos.
"""
__all__ = ["main", "build_argparser"]

import argparse

import lsst.daf.butler
from .. import extract_metricvalues


def build_argparser():
    """Return an ArgumentParser for this script.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='More information is available at https://pipelines.lsst.io.')
    parser.add_argument("repo", type=str,
                        help="Path to butler repo to load metrics from.")
    parser.add_argument("collection", type=str,
                        help="Collection in REPO to load from.")
    parser.add_argument("repo2", type=str, nargs="?", default=None,
                        help="Path to butler repo to load metrics from, to difference with REPO.")
    parser.add_argument("collection2", type=str, nargs="?", default=None,
                        help="Collection in REPO2 to load from, otherwise use COLLECTION.")
    parser.add_argument("--kind", choices=["value", "timing", "memory"], default="value",
                        help="What kind of metrics to load (default='value')."
                             "Not supported when printing metric differences.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print extra information when loading metric values or handling errors.")
    parser.add_argument("--data-id-keys", nargs="+", default=None,
                        help="Only print these dataId keys in the output;"
                             "for example, `--data-id-keys detector visit`.")
    return parser


def main():
    args = build_argparser().parse_args()

    butler = lsst.daf.butler.Butler(args.repo, collections=args.collection)

    if args.repo2 is None:
        extract_metricvalues.print_metrics(butler,
                                           args.kind,
                                           data_id_keys=args.data_id_keys,
                                           verbose=args.verbose)
    else:
        collection2 = args.collection2 if args.collection2 is not None else args.collection
        butler2 = lsst.daf.butler.Butler(args.repo2, collections=collection2)
        print(f"Showing difference of {args.repo2}#{collection2} - {args.repo}#{args.collection}")
        extract_metricvalues.print_diff_metrics(butler,
                                                butler2,
                                                data_id_keys=args.data_id_keys,
                                                verbose=args.verbose)

#!/usr/bin/env python

# LSST Data Management System
# Copyright 2008-2016 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
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

from __future__ import print_function

import argparse
import os.path
import sys

from lsst.validate.drp import validate, util


if __name__ == "__main__":
    description="""
    Calculate and plot validation Key Project Metrics from the LSST SRD.

    Produces results to:
    STDOUT
        Summary of key metrics
    *.png
        Plots of key metrics.  Generated in current working directory.
    *.json
        JSON serialization of each KPM.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('repo', type=str, 
                        help='path to a repository containing the output of processCcd')
    parser.add_argument('--configFile', '-c', type=str, default=None,
                        help='YAML configuration file validation parameters and dataIds.')
    parser.add_argument('--verbose', '-v', default=False, action='store_true',
                        help='Display additional information about the analysis.')
    
    args = parser.parse_args()

    if not os.path.isdir(args.repo):
        print("Could not find repo %r" % (args.repo,))
        sys.exit(1)

    kwargs = {}
    if args.configFile:
        dataIds, good_mag_limit, medianAstromscatterRef, medianPhotoscatterRef, matchRef = \
            util.loadDataIdsAndParameters(args.configFile)
        kwargs = {
            'good_mag_limit': good_mag_limit, 
            'medianAstromscatterRef': medianAstromscatterRef, 
            'medianPhotoscatterRef': medianPhotoscatterRef, 
            'matchRef': matchRef,
            }

    if not args.configFile or not dataIds:
        dataIds = util.discoverDataIds(args.repo)
        if args.verbose:
            print("VISITDATAIDS: ", dataIds)

    kwargs['verbose'] = args.verbose
    validate.run(args.repo, dataIds, **kwargs)

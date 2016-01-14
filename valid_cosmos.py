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

import os.path
import sys

import numpy as np

from check_astrometry import main, loadAndMatchData

def defaultData(repo):
    # List of visits to be considered
    visits = [176846, 176850]

    # Reference visit (the other visits will be compared to this one)
    ref = 176837

    # List of CCD to be considered (source catalogs will be concateneted)
    ccd = [10] #, 12, 14, 18]
    filter = 'z'
    
    # Reference values for the median astrometric scatter and the number of matches
    good_mag_limit = 21
    medianRef = 25
    matchRef = 5600

    visitDataIds = [[{'visit':v, 'filter':filter, 'ccdnum':c} for v in visits]
                    for c in ccd]
    refDataIds = [{'visit':ref, 'filter':filter, 'ccdnum':c} for c in ccd]
    
    return visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("""Usage: valid_cosmos repo
where repo is the path to a repository containing the output of processCcd
""")
        sys.exit(1)

    repo = sys.argv[1]
    if not os.path.isdir(repo):
        print("Could not find repo %r" % (repo,))
        sys.exit(1)

    visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef = defaultData(repo)
    main(repo, visitDataIds, refDataIds, good_mag_limit, medianRef, matchRef)

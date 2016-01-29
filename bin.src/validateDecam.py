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

from lsst.validate.drp import checkAstrometryPhotometry


def defaultData(repo):
    # List of visits to be considered
    visits = [176837, 176846]

    # List of CCD to be considered (source catalogs will be concateneted)
    ccd = [10, 11, 12, 13, 14, 15, 16, 17, 18]
    filter = 'z'

    # Reference values that the DECam analysis should pass
    #  for the median astrometric scatter and the number of matches
    good_mag_limit = 21  # [mag]
    medianRef = 25  # [arcsec]
    matchRef = 10000  # [number of stars]

    visitDataIds = [{'visit': v, 'filter': filter, 'ccdnum': c} for v in visits
                    for c in ccd]

    return visitDataIds, good_mag_limit, medianRef, matchRef

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

    args = defaultData(repo)
    checkAstrometryPhotometry.run(repo, *args)

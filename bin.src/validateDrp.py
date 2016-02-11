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

from lsst.validate.drp import validate, util


if __name__ == "__main__":
    helpMessage = """Usage: validateDrp.py repo configFile

    Arguments
    ---------
    `repo` : str
        path to a repository containing the output of processCcd
    `configFile` : str
        YAML configuration file declaring the parameters for this run.

    Output
    ------
    STDOUT
        Summary of key metrics
    *.png
        Plots of key metrics.  Generated in current working directory.

    Notes
    -----
    Currently can only work on one filter at a time.
      -- There is no logic to organize things by filter in the analysis,
      -- There is no syntax for matching visits with filters in the YAML file.
    """
    if len(sys.argv) < 2:
        print(helpMessage)
        sys.exit(1)

    repo = sys.argv[1]
    if not os.path.isdir(repo):
        print("Could not find repo %r" % (repo,))
        sys.exit(1)

    configFile = sys.argv[2]

    visitDataIds, good_mag_limit, medianAstromscatterRef, medianPhotoscatterRef, matchRef = \
        util.loadDataIdsAndParameters(configFile)
    validate.run(repo, visitDataIds,
                 good_mag_limit=good_mag_limit, 
                 medianAstromscatterRef=medianAstromscatterRef, 
                 medianPhotoscatterRef=medianPhotoscatterRef, 
                 matchRef=matchRef)

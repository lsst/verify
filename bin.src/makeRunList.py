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

from lsst.validate.drp import validate


if __name__ == "__main__":
    helpMessage = """Usage: makeRunList.py configFile

    Arguments
    ---------
    `configFile` : str
        YAML configuration file declaring the parameters for this run.

    Output
    ------
    STDOUT
        List of run IDs suitable for ingestion by `processCcd.py`

    Notes
    -----
    """
    if len(sys.argv) < 2:
        print(helpMessage)
        sys.exit(1)

    configFile = sys.argv[1]
    if not os.path.isfile(configFile):
        print("Could not find config file %r" % (configFile,))
        sys.exit(1)

    runList = validate.loadRunList(configFile)
    lines = "\n".join(runList)
    print(lines)

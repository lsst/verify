#!/usr/bin/env python
#
# This file is part of ap_verify.
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

"""Print the contents of a persisted Job object.

This script takes as arguments one or more Job .json files, and prints the
top-level metadata and a summary of any measurements. It does not print
metrics that don't have measurements (there are far too many) or
specifications (which are not helpful for testing measurement code).
"""

import sys

from lsst.verify.bin.inspectjob import main


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Syntax: %s <job file> [[job file]...]" % sys.argv[0])
        sys.exit(1)
    main(sys.argv[1:])

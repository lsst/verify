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

import yaml

from .util import getCcdKeyName

def loadDataIdsFromConfigFile(configFile):
    """Load data IDs, magnitude range, and expected metrics from a yaml file."""
    stream = open(configFile, mode='r')
    data = yaml.load(stream)

    ccdKeyName = getCcdKeyName(data)
    visitDataIds = [{'visit': v, 'filter': data['filter'], ccdKeyName: c} 
                    for v in data['visits']
                    for c in data[ccdKeyName]]

    return visitDataIds, data['good_mag_limit'], data['medianRef'], data['matchRef']

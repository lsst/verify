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

from __future__ import print_function, division

import numpy as np
import scipy.stats

# To validate these width estimates, we can plot a single random realization (re-evaluate the cell or call the function again to get a new one).
def calcPA1(gv, magKey):
    diffs = gv.aggregate(getRandomDiff, field=magKey)
    means = gv.aggregate(np.mean, field=magKey)
    rmsPA1, iqrPA1 = computeWidths(diffs)
    return rmsPA1, iqrPA1, diffs, means


def calcPA2(gv, magKey):
    """Calculate PA2 values for min, design, stretch values of PF1.

    The SRD requirements puts a limit on the fraction of outliers plot of PA1.
    This is PA2.  Below, we compute the values of PA2 for the minimum, design, and stretch specification values of PF1 in the SRD.
    """
 
    diffs = gv.aggregate(getRandomDiff, field=magKey)
    minPA2, designPA2, stretchPA2 = np.percentile(np.abs(diffs), [80, 90, 95])
    return minPA2, designPA2, stretchPA2

# The SRD recommends computing repeatability from a histogram of magnitude differences for the same star measured on two visits (using a median over the diffs to reject outliers). Since our dataset includes N>2 measurements for each star, we select a random pair of visits for each star.
# We also divide each difference by sqrt(2), because we want the RMS about the (unknown) mean magnitude, not the RMS difference, and convert from mags to mmag.
# Note that this randomization still works for cases where we have only 2 obervations of the star.
def getRandomDiff(array):
    # not the most efficient way to extract a pair, but it's the easiest to write
    copy = array.copy()
    np.random.shuffle(copy)
    return 1000*(copy[0] - copy[1])/(2**0.5)

def computeWidths(diffs):
    """Compute the RMS and the scaled inter-quartile range of an array.
  
    We estimate the width of the histogram in two ways: using a simple RMS, and using the interquartile range (scaled by the IQR/RMS ratio for a Gaussian). We do this for 50 different random realizations of the measurement pairs, to provide some estimate of the uncertainty on our RMS estimates due to the random shuffling (we could probably turn this into a more formal estimate somehow, but I'm not going to bother with that at the moment).
    While the SRD specifies that we should just compute the RMS directly, we haven't limited our sample to nonvariable stars as carefully as the SRD specifies, so using a more robust estimator like IQR will allow us to reject some outliers. It is also less sensitive some realistic sources of scatter the metric should include, however, such as bad zero points.
    """

    rmsSigma = np.mean(diffs**2)**0.5
    iqrSigma = np.subtract.reduce(np.percentile(diffs, [75, 25])) / (scipy.stats.norm.ppf(0.75)*2)
    return rmsSigma, iqrSigma



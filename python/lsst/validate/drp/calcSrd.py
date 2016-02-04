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

import math

import numpy as np
import scipy.stats

import lsst.pipe.base as pipeBase

def calcPA1(groupView, magKey):
    """Calculate the photometric repeatability of measurements across a set of observations.

    @param[in] groupView -- A lsst.afw.table.GroupView of matched observations.
    @param[in] magKey -- The lookup key of the field storing the magnitude of interest.
       E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
       where `allMatches` is a the result of lsst.afw.table.MultiMatch.finish()

    @param[out] -- pipeBase.Struct containing
       the RMS, inter-quartile range, differences between pairs of observations, mean mag of each object.

    The LSST Science Requirements Document (LPM-17), commonly referred to as the SRD
    characterizes the photometric repeatability by putting a requirement
    on the median RMS of measurements of non-variable bright stars.
    This quantity is PA1, with a design, minimum, and stretch goal of (5, 8, 3) millimag
      following LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.

    This present routine calculates this quantity in two different ways: RMS, interquartile
    and also returns additional quantities of interest: 
      the pair differences of observations of stars, the mean magnitude of each star
    """

    diffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
    means = groupView.aggregate(np.mean, field=magKey)
    rmsPA1, iqrPA1 = computeWidths(diffs)
    return pipeBase.Struct(rms = rmsPA1, iqr = iqrPA1, diffs = diffs, means = means)


def calcPA2(groupView, magKey):
    """Calculate the fraction of outliers from the photometric repeatability of measurements.

    @param[in] groupView -- A lsst.afw.table.GroupView of matched observations.
    @param[in] magKey -- The lookup key of the field storing the magnitude of interest.
       E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
       where `allMatches` is a the result of lsst.afw.table.MultiMatch.finish()

    @param[out] -- pipeBase.Struct containing PA2, the millimags of varaition at the 
       `design`, `minimum`, and `stretch` fraction of outliers
       The specified fractions are also avialable as `PF1`.

    The LSST Science Requirements Document (LPM-17) is commonly referred to as the SRD.
    The SRD puts a limit that no more than PF1 % of difference will very by more than PA2 millimag.
    The design, minimum, and stretch goals are PF1 = (10, 20, 5) % at PA2 = (15, 15, 10) millimag
      following LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.
    """
 
    diffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
    PF1 = {'minimum' : 20, 'design' : 10, 'stretch' : 5}
    PF1_percentiles = 100 - np.asarray([PF1['minimum'], PF1['design'], PF1['stretch']])
    minPA2, designPA2, stretchPA2 = np.percentile(np.abs(diffs), PF1_percentiles)
    return pipeBase.Struct(design = designPA2, minimum = minPA2, stretch = stretchPA2, PF1 = PF1)

def getRandomDiffRmsInMas(array):
    """Get the RMS difference between two randomly selected elements of an array of magnitudes.

    The LSST SRD recommends computing repeatability from a histogram of magnitude differences 
       for the same star measured on two visits (using a median over the diffs to reject outliers). 
    Because we have N>=2 measurements for each star, we select a random pair of visits for each star.
    We divide each difference by sqrt(2) to obtain RMS about the (unknown) mean magnitude, 
       instead of obtaining just the RMS difference.
    """
    # For scalars, math.sqrt is several times faster than numpy.sqrt.
    return (1000/math.sqrt(2)) * getRandomDiff(array)


def getRandomDiff(array):
    """Get the difference between two randomly selected elements of an array.

    Notes: 
      * This is not the most efficient way to extract a pair, but it's the easiest to write.
      * Shuffling works correctly for low N (even N=2), where a naive random generation of entries 
          would result in duplicates.  
      * In principle it might be more efficient to shuffle the indices, then extract the difference.
        But this probably only would make a difference for arrays whose elements were
          substantially larger than just scalars and had the subtraction operation defined.
    """
    copy = array.copy()
    np.random.shuffle(copy)
    return copy[0] - copy[1]


def computeWidths(array):
    """Compute the RMS and the scaled inter-quartile range of an array.
  
    We estimate the width of the histogram in two ways: using a simple RMS, 
       and using the interquartile range (scaled by the IQR/RMS ratio for a Gaussian). 
    While the SRD specifies that we should just compute the RMS directly, 
       we haven't limited our sample to nonvariable stars as carefully as the SRD specifies, 
       so using a more robust estimator like IQR allows us to reject some outliers. 
       It is also less sensitive some realistic sources of scatter the metric should include, 
         such as bad zero points.
    """
    rmsSigma = math.sqrt(np.mean(array**2))
    iqrSigma = np.subtract.reduce(np.percentile(array, [75, 25])) / (scipy.stats.norm.ppf(0.75)*2)
    return rmsSigma, iqrSigma



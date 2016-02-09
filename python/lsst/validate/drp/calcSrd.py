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

    Parameters
    ----------
    groupView : lsst.afw.table.GroupView 
         GroupView object of matched observations from MultiMatch.
    magKey : lookup key to a `schema`
         The lookup key of the field storing the magnitude of interest.
         E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
         where `allMatches` is a the result of lsst.afw.table.MultiMatch.finish()

    Returns
    -------
    pipeBase.Struct
       The RMS, inter-quartile range, 
       differences between pairs of observations, mean mag of each object.

    Notes
    -----
    The LSST Science Requirements Document (LPM-17), or SRD,
    characterizes the photometric repeatability by putting a requirement
    on the median RMS of measurements of non-variable bright stars.
    This quantity is PA1, with a design, minimum, and stretch goals of
      (5, 8, 3) millimag
    following LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.

    This present routine calculates this quantity in two different ways: 
       RMS
       interquartile range (IQR)
    and also returns additional quantities of interest:
      the pair differences of observations of stars, 
      the mean magnitude of each star

    While the SRD specifies that we should just compute the RMS directly, 
       the current filter doesn't screen out variable stars as carefully 
       as the SRD specifies, so using a more robust estimator like the IQR 
       allows us to reject some outliers. 
    However, the IRQ is also less sensitive some realistic sources of scatter 
       such as bad zero points, that the metric should include.

    See Also
    --------
    calcPA2 : Calculate photometric repeatability outlier fraction.

    Examples
    --------
    >>> import lsst.daf.persistence as dafPersist
    >>> from lsst.afw.table import SourceCatalog, SchemaMapper, Field
    >>> from lsst.afw.table import MultiMatch, SourceRecord, GroupView
    >>> repo = "CFHT/output"
    >>> butler = dafPersist.Butler(repo)
    >>> dataset = 'src'
    >>> schema = butler.get(dataset + "_schema", immediate=True).schema
    >>> mmatch = MultiMatch(newSchema,
    >>>                     dataIdFormat={'visit': int, 'ccd': int},
    >>>                     radius=matchRadius,
    >>>                     RecordClass=SourceRecord)
    >>> for vId in visitDataIds:
    ...     cat = butler.get('src', vId)
    ...     mmatch.add(catalog=cat, dataId=vId)
    ...
    >>> matchCat = mmatch.finish()
    >>> allMatches = GroupView.build(matchCat)
    >>> allMatches
    >>> psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
    >>> pa1_sample = calcPA1(allMatches, psfMagKey)
    >>> print("The RMS was %.3f, the IQR was %.3f" % (pa1_sample.rms, pa1_sample.iqr))
    """

    diffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
    means = groupView.aggregate(np.mean, field=magKey)
    rmsPA1, iqrPA1 = computeWidths(diffs)
    return pipeBase.Struct(rms = rmsPA1, iqr = iqrPA1, 
                           diffs = diffs, means = means)


def calcPA2(groupView, magKey):
    """Calculate the fraction of outliers from PA1.

    Calculate the fraction of outliers from the median RMS characterizaing 
    the photometric repeatability of measurements as calculated via `calcPA1`.

    Parameters
    ----------
    groupView : lsst.afw.table.GroupView 
         GroupView object of matched observations from MultiMatch.
    magKey : lookup key to a `schema`
         The lookup key of the field storing the magnitude of interest.
         E.g., `magKey = allMatches.schema.find("base_PsfFlux_mag").key`
         where `allMatches` is a the result of lsst.afw.table.MultiMatch.finish()

    Returns
    -------
    pipeBase.Struct
       The RMS, inter-quartile range, 
       differences between pairs of observations, mean mag of each object.

    See Also
    --------
    calcPA1 : Calculate photometric repeatability median RMS

    Examples
    --------
    >>> import lsst.daf.persistence as dafPersist
    >>> from lsst.afw.table import SourceCatalog, SchemaMapper, Field
    >>> from lsst.afw.table import MultiMatch, SourceRecord, GroupView
    >>> repo = "CFHT/output"
    >>> butler = dafPersist.Butler(repo)
    >>> dataset = 'src'
    >>> schema = butler.get(dataset + "_schema", immediate=True).schema
    >>> mmatch = MultiMatch(newSchema,
    >>>                     dataIdFormat={'visit': int, 'ccd': int},
    >>>                     radius=matchRadius,
    >>>                     RecordClass=SourceRecord)
    >>> for vId in visitDataIds:
    ...     cat = butler.get('src', vId)
    ...     mmatch.add(catalog=cat, dataId=vId)
    ...
    >>> matchCat = mmatch.finish()
    >>> allMatches = GroupView.build(matchCat)
    >>> allMatches
    >>> psfMagKey = allMatches.schema.find("base_PsfFlux_mag").key
    >>> pa2 = calcPA2(allMatches, psfMagKey)
    >>> print("minimum: PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" %
    ...       (pa2.PF1['minimum'], pa2.minimum))
    >>> print("design:  PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 15 mmag)" %
    ...       (pa2.PF1['design'], pa2.design))
    >>> print("stretch: PF1=%2d%% of diffs more than PA2 = %4.2f mmag (target is PA2 < 10 mmag)" %
    ...       (pa2.PF1['stretch'], pa2.stretch))


    Notes
    -----
    The LSST Science Requirements Document (LPM-17) is commonly referred 
    to as the SRD.  The SRD puts a limit that no more than PF1 % of difference 
    will vary by more than PA2 millimag.  The design, minimum, and stretch goals
    are PF1 = (10, 20, 5) % at PA2 = (15, 15, 10) millimag
      following LPM-17 as of 2011-07-06, available at http://ls.st/LPM-17.
    """
 
    diffs = groupView.aggregate(getRandomDiffRmsInMas, field=magKey)
    PF1 = {'minimum' : 20, 'design' : 10, 'stretch' : 5}
    PF1_percentiles = 100 - np.asarray([PF1['minimum'], PF1['design'], PF1['stretch']])
    minPA2, designPA2, stretchPA2 = np.percentile(np.abs(diffs), PF1_percentiles)
    return pipeBase.Struct(design = designPA2, minimum = minPA2, stretch = stretchPA2, PF1 = PF1)

def getRandomDiffRmsInMas(array):
    """Calculate the RMS difference in mmag between a random pairs of magnitudes.

    Input
    -----
    array : list or np.array
        Magnitudes from which to select the pair  [mag]

    Returns
    -------
    float
        RMS difference
        
    Notes
    -----
    The LSST SRD recommends computing repeatability from a histogram of 
    magnitude differences for the same star measured on two visits 
    (using a median over the diffs to reject outliers). 
    Because we have N>=2 measurements for each star, we select a random 
    pair of visits for each star.  We divide each difference by sqrt(2) 
    to obtain RMS about the (unknown) mean magnitude, 
       instead of obtaining just the RMS difference.

    See Also
    --------
    getRandomDiff : Get the difference

    Examples
    --------
    >>> mag = [24.2, 25.5]
    >>> rms = getRandomDiffRmsInMas(mag)
    >>> print(rms)
    212.132034
    """
    # For scalars, math.sqrt is several times faster than numpy.sqrt.
    return (1000/math.sqrt(2)) * getRandomDiff(array)


def getRandomDiff(array):
    """Get the difference between two randomly selected elements of an array.
    Input
    -----
    array : list or np.array
    
    Returns
    -------
    float or int
        Difference between two random elements of the array.

    Notes 
    -----
    * As implemented the returned value is the result of subtracting 
        two elements of the input array.  In all of the imagined uses 
        that's going to be a scalar (float, maybe int).  
        In principle, however the code as implemented returns the result
        of subtracting two elements of the array, which could be any
        arbitrary object that is the result of the subtraction operator
        applied to two elements of the array.
    * This is not the most efficient way to extract a pair, 
        but it's the easiest to write.
    * Shuffling works correctly for low N (even N=2), where a naive 
        random generation of entries would result in duplicates.  
    * In principle it might be more efficient to shuffle the indices, 
        then extract the difference.  But this probably only would make a 
        difference for arrays whose elements were objects that were 
        substantially larger than a float.  And that would only make
        sense for objects that had a subtraction operation defined.
    """
    copy = array.copy()
    np.random.shuffle(copy)
    return copy[0] - copy[1]


def computeWidths(array):
    """Compute the RMS and the scaled inter-quartile range of an array.
  
    Input
    -----
    array : list or np.array

    Returns
    -------
    float, float
        RMS and scaled inter-quartile range (IQR).  
        
    Notes
    -----
    We estimate the width of the histogram in two ways: 
       using a simple RMS, 
       using the interquartile range (IQR)
    The IQR is scaled by the IQR/RMS ratio for a Gaussian such that it
       if the array is Gaussian distributed, then the scaled IQR = RMS. 
    """
    rmsSigma = math.sqrt(np.mean(array**2))
    iqrSigma = np.subtract.reduce(np.percentile(array, [75, 25])) / (scipy.stats.norm.ppf(0.75)*2)
    return rmsSigma, iqrSigma



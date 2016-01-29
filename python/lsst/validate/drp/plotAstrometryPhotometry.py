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

import os.path
import sys

import matplotlib.pylab as plt
import numpy as np
import scipy.stats

from .calcSrd import calcPA2

# Plotting defaults
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['font.size'] = 20
plt.rcParams['axes.labelsize'] = 20
# plt.rcParams['figure.titlesize'] = 30

def plotMedians(ax, x1, x2, x1_color='blue', x2_color='red'):
    ax.axhline(x1, color='white', linewidth=4)
    ax.axhline(x2, color='white', linewidth=4)
    ax.axhline(x1, color=x1_color, linewidth=3)
    ax.axhline(x2, color=x2_color, linewidth=3)


def plotAstrometry(mag, mmagrms, dist, match, good_mag_limit=19.5,
                   plotbase=""):
    """Plot angular distance between matched sources from different exposures.

    @param[in] mag    Magnitude.  List or numpy.array.
    @param[in] mmagrms    Magnitude RMS.  List or numpy.array.
    @param[in] dist   Separation from reference.  List of numpy.array
    @param[in] match  Number of stars matched.  Integer.
    """

    bright, = np.where(np.asarray(mag) < good_mag_limit)

    dist_median = np.median(dist) 
    bright_dist_median = np.median(np.asarray(dist)[bright])

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(18, 12))

    ax[0].hist(dist, bins=100, color='blue',
               histtype='stepfilled', orientation='horizontal')
    ax[0].hist(np.asarray(dist)[bright], bins=100, color='red',
               histtype='stepfilled', orientation='horizontal',
               label='mag < %.1f' % good_mag_limit)

    ax[0].set_ylim([0., 500.])
    ax[0].set_ylabel("Distance [mas]")
    ax[0].set_title("Median : %.1f, %.1f mas" % 
                       (bright_dist_median, dist_median),
                       x=0.55, y=0.88)
    plotMedians(ax[0], dist_median, bright_dist_median)

    ax[1].scatter(mag, dist, s=10, color='blue', label='All')
    ax[1].scatter(np.asarray(mag)[bright], np.asarray(dist)[bright], s=10, 
                  color='red', 
                  label='mag < %.1f' % good_mag_limit)
    ax[1].set_xlabel("Magnitude")
    ax[1].set_ylabel("Distance [mas]")
    ax[1].set_xlim([17, 24])
    ax[1].set_ylim([0., 500.])
    ax[1].set_title("# of matches : %d, %d" % (len(bright), match))
    ax[1].legend(loc='upper left')
    plotMedians(ax[1], dist_median, bright_dist_median)

    plt.suptitle("Astrometry Check", fontsize=30)
    plotPath = plotbase+"check_astrometry.png"
    plt.savefig(plotPath, format="png")


def plotPhotometryRms(mag, mmagrms, dist, match, good_mag_limit=19.5,
                      plotbase=""):
    """Plot photometric RMS for matched sources.

    @param[in] mag    Magnitude.  List or numpy.array.
    @param[in] mmagrms    Magnitude RMS.  List or numpy.array.
    @param[in] dist   Separation from reference.  List of numpy.array
    @param[in] match  Number of stars matched.  Integer.
    """

    bright, = np.where(np.asarray(mag) < good_mag_limit)

    mmagrms_median = np.median(mmagrms) 
    bright_mmagrms_median = np.median(np.asarray(mmagrms)[bright])

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(18, 12))
    ax[0].hist(mmagrms, bins=100, range=(0, 500), color='blue', label='All',
                  histtype='stepfilled', orientation='horizontal')
    ax[0].hist(np.asarray(mmagrms)[bright], bins=100, range=(0, 500), color='red', 
                  label='mag < %.1f' % good_mag_limit,
                  histtype='stepfilled', orientation='horizontal')
    ax[0].set_ylim([0, 500])
    ax[0].set_ylabel("RMS [mmag]")
    ax[0].set_title("Median : %.1f, %.1f mmag" % 
                    (bright_mmagrms_median, mmagrms_median),
                    x=0.55, y=0.88)
    plotMedians(ax[0], mmagrms_median, bright_mmagrms_median)

    ax[1].scatter(mag, mmagrms, s=10, color='blue', label='All')
    ax[1].scatter(np.asarray(mag)[bright], np.asarray(mmagrms)[bright], 
                     s=10, color='red', 
                     label='mag < %.1f' % good_mag_limit)

    ax[1].set_xlabel("Magnitude")
    ax[1].set_ylabel("RMS [mmag]")
    ax[1].set_xlim([17, 24])
    ax[1].set_ylim([0, 500])
    ax[1].set_title("# of matches : %d, %d" % (len(bright), match))
    ax[1].legend(loc='upper left')
    plotMedians(ax[1], mmagrms_median, bright_mmagrms_median)

    plt.suptitle("Photometry Check", fontsize=30)
    plotPath = plotbase+"check_photometry.png"
    plt.savefig(plotPath, format="png")

def plotPA1(gv, magKey, plotbase=""):
    rmsPA1, iqrPA1, diffs, means = calcPA1(gv, magKey)

    fig = plt.figure(figsize=(18,12))
    ax1 = fig.add_subplot(1,2,1)
    ax1.scatter(means, diffs, s=8, linewidth=0, alpha=0.4)
    ax1.axhline(rmsPA1, color='r')
    ax1.axhline(-rmsPA1, color='r')
    ax1.axhline(iqrPA1, color='g')
    ax1.axhline(-iqrPA1, color='g')
    ax2 = fig.add_subplot(1,2,2, sharey=ax1)
    ax2.hist(diffs, bins=50, orientation='horizontal', normed=True, alpha=0.5)
    yv = np.linspace(-100, 100, 100)
    ax2.plot(scipy.stats.norm.pdf(yv, scale=rmsPA1), yv, 'r-', label="PA1(RMS)=%4.2f mmag" % rmsPA1)
    ax2.plot(scipy.stats.norm.pdf(yv, scale=iqrPA1), yv, 'g-', label="PA1(IQR)=%4.2f mmag" % iqrPA1)
    ax2.set_ylim(-100, 100)
    ax2.legend()
#    ax1.set_ylabel(u"12-pixel aperture magnitude diff (mmag)")
#    ax1.set_xlabel(u"12-pixel aperture magnitude")
    ax1.set_xlabel("psf aperture magnitude")
    ax1.set_ylabel("psf magnitude diff (mmag)")
    for label in ax2.get_yticklabels(): label.set_visible(False)

    plotPath = "%s%s" % (plotbase, "PA1.png")
    plt.savefig(plotPath, format="png")


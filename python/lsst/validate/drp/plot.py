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

import matplotlib.pylab as plt
import numpy as np
import scipy.stats
from scipy.optimize import curve_fit

# Plotting defaults
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['font.size'] = 20
plt.rcParams['axes.labelsize'] = 20
# plt.rcParams['figure.titlesize'] = 30

color = {'all': 'grey', 'bright': 'blue',
         'iqr': 'green', 'rms': 'red'}


def plotOutlinedLinesHorizontal(ax, *args, **kwargs):
    """Plot horizontal lines outlined in white.

    The motivation is to let horizontal lines stand out clearly
    even against a cluttered background.
    """
    plotOutlinedLines(ax.axhline, *args, **kwargs)


def plotOutlinedLinesVertical(ax, *args, **kwargs):
    """Plot vertical lines outlined in white.

    The motivation is to let horizontal lines stand out clearly
    even against a cluttered background.
    """
    plotOutlinedLines(ax.axvline, *args, **kwargs)


def plotOutlinedLines(ax_plot, x1, x2, x1_color=color['all'], x2_color=color['bright']):
    """Plot horizontal lines outlined in white.

    The motivation is to let horizontal lines stand out clearly
    even against a cluttered background.
    """
    ax_plot(x1, color='white', linewidth=4)
    ax_plot(x2, color='white', linewidth=4)
    ax_plot(x1, color=x1_color, linewidth=3)
    ax_plot(x2, color=x2_color, linewidth=3)


def plotAstrometry(dist, mag, snr, brightSnr=100,
                   outputPrefix=""):
    """Plot angular distance between matched sources from different exposures.

    Creates a file containing the plot with a filename beginning with `outputPrefix`.

    Parameters
    ----------
    dist : list or numpy.array
        Separation from reference [mas]
    mag : list or numpy.array
        Mean magnitude of PSF flux
    snr : list or numpy.array
        Median SNR of PSF flux
    brightSnr : float, optional
        Minimum SNR for a star to be considered "bright".
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot titles.
        E.g., outputPrefix='Cfht_output_r_' will result in a file named
           'Cfht_output_r_check_astrometry.png'
    """
    bright, = np.where(np.asarray(snr) > brightSnr)

    numMatched = len(dist)
    dist_median = np.median(dist)
    bright_dist_median = np.median(np.asarray(dist)[bright])

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(18, 12))

    ax[0].hist(dist, bins=100, color=color['all'],
               histtype='stepfilled', orientation='horizontal')
    ax[0].hist(np.asarray(dist)[bright], bins=100, color=color['bright'],
               histtype='stepfilled', orientation='horizontal',
               label='SNR > %.0f' % brightSnr)

    ax[0].set_ylim([0., 500.])
    ax[0].set_ylabel("Distance [mas]")
    ax[0].set_title("Median : %.1f, %.1f mas" %
                    (bright_dist_median, dist_median),
                    x=0.55, y=0.88)
    plotOutlinedLinesHorizontal(ax[0], dist_median, bright_dist_median)

    ax[1].scatter(snr, dist, s=10, color=color['all'], label='All')
    ax[1].scatter(np.asarray(snr)[bright], np.asarray(dist)[bright], s=10,
                  color=color['bright'],
                  label='SNR > %.0f' % brightSnr)
    ax[1].set_xlabel("SNR")
    ax[1].set_xscale("log")
    ax[1].set_ylim([0., 500.])
    ax[1].set_title("# of matches : %d, %d" % (len(bright), numMatched))
    ax[1].legend(loc='upper left')
    ax[1].axvline(brightSnr, color='red', linewidth=4, linestyle='dashed')
    plotOutlinedLinesHorizontal(ax[1], dist_median, bright_dist_median)

    plt.suptitle("Astrometry Check : %s" % outputPrefix.rstrip('_'), fontsize=30)
    plotPath = outputPrefix+"check_astrometry.png"
    plt.savefig(plotPath, format="png")
    plt.close(fig)


def expModel(x, a, b, norm):
    return a * np.exp(x/norm) + b


def magerrModel(x, a, b):
    return expModel(x, a, b, norm=5)


def plotExpFit(x, y, y_err, deg=2, ax=None, verbose=False):
    """Fit and plot an exponential quadratic to x, y, y_err.
    """

    if ax is None:
        ax = plt.figure()
        xlim = [10, 30]
    else:
        xlim = ax.get_xlim()

    popt, pcov = curve_fit(expModel, x, y, p0=[1, 0.02, 5], sigma=y_err)
    fit_params = popt
    x_model = np.linspace(*xlim, num=100)
    fit_model = expModel(x_model, *fit_params)
    label = '%.4g exp(mag/%.4g) + %.4g' % \
            (fit_params[0], fit_params[2], fit_params[1])
    if verbose:
        print(fit_params)
        print(label)

    ax.plot(x_model, fit_model, color='red',
            label=label)

    return fit_params


def plotAstromErrModelFit():
    """Fit and plot model of photometric error from LSST Overview paper
    http://arxiv.org/abs/0805.2366v4

    Astrometric Errors
    error = C * theta / SNR
    """
    pass


def photErrModel(mag, sigmaSys, gamma, m5):
    """Fit model of photometric error from LSST Overview paper
    http://arxiv.org/abs/0805.2366v4

    Photometric errors described by
    Eq. 4
    sigma_1^2 = sigma_sys^2 + sigma_rand^2

    Eq. 5
    sigma_(rand) = (0.04 - gamma) * x + gamma * x^2 [mag^2]
    where x = 10**(0.4*(m-m_5))

    Parameters
    ----------
    mag : list or numpy.array
        Magnitude
    sigmaSq : float
        Limiting systematics floor [mag]
    gamma : float
        proxy for sky brightness and readout noise
    m5 : float
        5-sigma depth [mag]

    Returns
    -------
    numpy.array
        Result of noise estimation function
    """
    x = 10**(0.4*(mag - m5))
    sigmaRandSq = (0.04 - gamma) * x + gamma * x**2
    sigmaSq = sigmaSys**2 + sigmaRandSq
    return np.sqrt(sigmaSq)


def plotPhotErrModelFit(mag, mmag_err, ax=None, verbose=True):
    """Fit and plot model of photometric error from LSST Overview paper

    Parameters
    ----------
    mag : list or numpy.array
        Magnitude
    mag_err : list or numpy.array
        Magnitude uncertainty or variation in *mmag*.
    ax : matplotlib.Axis, optional
        The Axis object to plot to.
    verbose : bool, optional
        Produce extra output to STDOUT

    Returns
    -------
    float, float, float
        sigmaSys, gamma, m5 fit parameters.
    """

    if ax is None:
        ax = plt.figure()
        xlim = [10, 30]
    else:
        xlim = ax.get_xlim()

    mag_err = mmag_err / 1000
    popt, pcov = curve_fit(photErrModel, mag, mag_err, p0=[0.01, 0.039, 24.35])
    fit_params = popt
    x_model = np.linspace(*xlim, num=100)
    fit_model_mag_err = photErrModel(x_model, *fit_params)
    fit_model_mmag_err = 1000*fit_model_mag_err
    sigmaSysMmag, gamma, m5Mag = fit_params[:]
    label = r'$\sigma_{\rm sys\ mmag}$=%5.2f, $\gamma=$%6.4f, $m_5=$%6.3f mag' % \
        (1000*sigmaSysMmag, gamma, m5Mag) 

    if verbose:
        print(fit_params)
        print(label)

    ax.plot(x_model, fit_model_mmag_err, color='red',
            label=label)

    return fit_params


def plotMagerrFit(*args, **kwargs):
    plotExpFit(*args, **kwargs)


def plotPhotometry(mag, snr, mmagerr, mmagrms, brightSnr=100,
                   filterName='Magnitude',
                   outputPrefix=""):
    """Plot photometric RMS for matched sources.

    Parameters
    ----------
    snr : list or numpy.array
        Median SNR of PSF flux
    mag : list or numpy.array
        Average Magnitude
    mmagerr : list or numpy.array
        Average Magnitude uncertainty [millimag]
    mmagrms ; list or numpy.array
        Magnitude RMS across visits [millimag]
    brightSnr : float, optional
        Minimum SNR for a star to be considered "bright".
    filterName : str, optional
        Name of the observed filter to use on axis labels.
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot titles.
        E.g., outputPrefix='Cfht_output_r_' will result in a file named
           'Cfht_output_r_check_photometry.png'
    """

    bright, = np.where(np.asarray(snr) > brightSnr)

    numMatched = len(mag)
    mmagrms_median = np.median(mmagrms)
    bright_mmagrms_median = np.median(np.asarray(mmagrms)[bright])

    fig, ax = plt.subplots(ncols=2, nrows=2, figsize=(18, 16))
    ax[0][0].hist(mmagrms, bins=100, range=(0, 500), color=color['all'], label='All',
                  histtype='stepfilled', orientation='horizontal')
    ax[0][0].hist(np.asarray(mmagrms)[bright], bins=100, range=(0, 500), color=color['bright'],
                  label='SNR > %.0f' % brightSnr,
                  histtype='stepfilled', orientation='horizontal')
    ax[0][0].set_ylim([0, 500])
    ax[0][0].set_ylabel("RMS [mmag]")
    ax[0][0].set_title("Median : %.1f, %.1f mmag" %
                       (bright_mmagrms_median, mmagrms_median),
                       x=0.55, y=0.88)
    plotOutlinedLinesHorizontal(ax[0][0], mmagrms_median, bright_mmagrms_median)

    ax[0][1].scatter(mag, mmagrms, s=10, color=color['all'], label='All')
    ax[0][1].scatter(np.asarray(mag)[bright], np.asarray(mmagrms)[bright],
                     s=10, color=color['bright'],
                     label='SNR > %.0f' % brightSnr)

    ax[0][1].set_xlabel("%s [mag]" % filterName)
    ax[0][1].set_ylabel("RMS [mmag]")
    ax[0][1].set_xlim([17, 24])
    ax[0][1].set_ylim([0, 500])
    ax[0][1].set_title("# of matches : %d, %d" % (len(bright), numMatched))
    ax[0][1].legend(loc='upper left')
    plotOutlinedLinesHorizontal(ax[0][1], mmagrms_median, bright_mmagrms_median)

    ax[1][0].scatter(mmagrms, mmagerr, s=10, color=color['all'], label=None)
    ax[1][0].scatter(np.asarray(mmagrms)[bright], np.asarray(mmagerr)[bright],
                     s=10, color=color['bright'],
                     label=None)
    ax[1][0].set_xscale('log')
    ax[1][0].set_yscale('log')
    ax[1][0].plot([0, 1000], [0, 1000],
                  linestyle='--', color='black', linewidth=2)
    ax[1][0].set_xlabel("RMS [mmag]")
    ax[1][0].set_ylabel("Median Reported Magnitude Err [mmag]")
    brightSnrInMmag = 2.5*np.log10(1 + (1/brightSnr)) * 1000

    ax[1][0].axhline(brightSnrInMmag, color='red', linewidth=4, linestyle='dashed',
                     label=r'SNR > %.0f = $\sigma_{\rm mmag} < $ %0.1f' % (brightSnr, brightSnrInMmag))
    ax[1][0].set_xlim([1, 500])
    ax[1][0].set_ylim([1, 500])
    ax[1][0].legend(loc='upper center')

    ax[1][1].scatter(mag, mmagerr, color=color['all'], label=None)
    ax[1][1].set_yscale('log')
    ax[1][1].scatter(np.asarray(mag)[bright], np.asarray(mmagerr)[bright],
                     s=10, color=color['bright'],
                     label=None,
                     )
    ax[1][1].set_xlabel("%s [mag]" % filterName)
    ax[1][1].set_ylabel("Median Reported Magnitude Err [mmag]")
    ax[1][1].set_xlim([17, 24])
    ax[1][1].set_ylim([1, 500])
    ax[1][1].axhline(brightSnrInMmag, color='red', linewidth=4, linestyle='dashed',
                     label=r'$\sigma_{\rm mmag} < $ %0.1f' % (brightSnrInMmag))

    ax2 = ax[1][1].twinx()
    ax2.scatter(mag, snr,
                color=color['all'], facecolor='none',
                marker='.', label=None)
    ax2.scatter(np.asarray(mag)[bright], np.asarray(snr)[bright],
                color=color['bright'], facecolor='none',
                marker='.', label=None)
    ax2.set_ylim(bottom=0)
    ax2.set_ylabel("SNR")
    ax2.axhline(brightSnr, color='red', linewidth=2, linestyle='dashed',
                label=r'SNR > %.0f' % (brightSnr))

    w, = np.where(mmagerr < 200)
    plotPhotErrModelFit(mag[w], mmagerr[w], ax=ax[1][1])
    ax[1][1].legend(loc='upper left')

    plt.suptitle("Photometry Check : %s" % outputPrefix.rstrip('_'), fontsize=30)
    plotPath = outputPrefix+"check_photometry.png"
    plt.savefig(plotPath, format="png")
    plt.close(fig)


def plotPA1(pa1, outputPrefix=""):
    """Plot the results of calculating the LSST SRC requirement PA1.

    Creates a file containing the plot with a filename beginning with `outputPrefix`.

    Parameters
    ----------
    pa1 : pipeBase.Struct
        Must contain:
        rms, iqr, magMean, magDiffs
        rmsUnits, iqrUnits, magDiffsUnits
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot titles.
        E.g., outputPrefix='Cfht_output_r_' will result in a file named
           'Cfht_output_r_AM1_D_5_arcmin_17.0-21.5.png'
        for an AMx.name=='AM1' and AMx.magRange==[17, 21.5]
    """
    diffRange = (-100, +100)

    fig = plt.figure(figsize=(18, 12))
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.scatter(pa1.magMean, pa1.magDiffs, s=10, color=color['bright'], linewidth=0)
    ax1.axhline(+pa1.rms, color=color['rms'], linewidth=3)
    ax1.axhline(-pa1.rms, color=color['rms'], linewidth=3)
    ax1.axhline(+pa1.iqr, color=color['iqr'], linewidth=3)
    ax1.axhline(-pa1.iqr, color=color['iqr'], linewidth=3)

    ax2 = fig.add_subplot(1, 2, 2, sharey=ax1)
    ax2.hist(pa1.magDiffs, bins=25, range=diffRange,
             orientation='horizontal', histtype='stepfilled',
             normed=True, color=color['bright'])
    ax2.set_xlabel("relative # / bin")

    yv = np.linspace(diffRange[0], diffRange[1], 100)
    ax2.plot(scipy.stats.norm.pdf(yv, scale=pa1.rms), yv,
             marker='', linestyle='-', linewidth=3, color=color['rms'],
             label="PA1(RMS) = %4.2f %s" % (pa1.rms, pa1.rmsUnits))
    ax2.plot(scipy.stats.norm.pdf(yv, scale=pa1.iqr), yv,
             marker='', linestyle='-', linewidth=3, color=color['iqr'],
             label="PA1(IQR) = %4.2f %s" % (pa1.iqr, pa1.iqrUnits))
    ax2.set_ylim(*diffRange)
    ax2.legend()
#    ax1.set_ylabel(u"12-pixel aperture magnitude diff (mmag)")
#    ax1.set_xlabel(u"12-pixel aperture magnitude")
    ax1.set_xlabel("psf magnitude")
    ax1.set_ylabel("psf magnitude diff (%s)" % pa1.magDiffsUnits)
    for label in ax2.get_yticklabels():
        label.set_visible(False)

    plt.suptitle("PA1: %s" % outputPrefix.rstrip('_'))
    plotPath = "%s%s" % (outputPrefix, "PA1.png")
    plt.savefig(plotPath, format="png")
    plt.close(fig)


def plotAM1(*args, **kwargs):
    return plotAMx(*args, x=1, **kwargs)


def plotAM2(*args, **kwargs):
    return plotAMx(*args, x=2, **kwargs)


def plotAM3(*args, **kwargs):
    return plotAMx(*args, x=3, **kwargs)


def plotAMx(AMx, outputPrefix=""):
    """Plot a histogram of the RMS in relative distance between pairs of stars.

    Creates a file containing the plot with a filename beginning with `outputPrefix`.

    Parameters
    ----------
    AMx : pipeBase.Struct
        Must contain:
        AMx, rmsDistMas, fractionOver, annulus, magRange, x, level,
        AMx_spec, AFx_spec, ADx_spec
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot titles.
        E.g., outputPrefix='Cfht_output_r_' will result in a file named
           'Cfht_output_r_AM1_D_5_arcmin_17.0-21.5.png'
        for an AMx.name=='AM1' and AMx.magRange==[17, 21.5]
    """

    percentOver = 100*AMx.fractionOver

    AMxAsDict = AMx.getDict()
    AMxAsDict['AMxADx'] = AMxAsDict['AMx_spec']+AMxAsDict['ADx_spec']
    AMxAsDict['percentOver'] = percentOver

    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.hist(AMx.rmsDistMas, bins=25, range=(0.0, 100.0),
             histtype='stepfilled',
             label='D: %.1f-%.1f %s\nMag Bin: %.1f-%.1f' %
                   (AMx.annulus[0], AMx.annulus[1], AMx.annulusUnits, AMx.magRange[0], AMx.magRange[1]))
    ax1.axvline(AMx.AMx, 0, 1, linewidth=2, color='black',
                label='median RMS of relative\nseparation: %.2f %s' % (AMx.AMx, AMx.amxUnits))
    ax1.axvline(AMx.AMx_spec, 0, 1, linewidth=2, color='red',
                label='%s: %.0f %s' % (AMx.name, AMx.AMx_spec, AMx.amxUnits))
    ax1.axvline(AMx.AMx_spec+AMx.ADx_spec, 0, 1, linewidth=2, color='green',
                label='AM{x:d}+AD{x:d}: {AMxADx:.0f} {amxUnits:s}\n' +
                      'AF{x:d}: {AFx_spec:.2f}{afxUnits:s} > AM{x:d}+AD{x:d} = ' +
                      '{percentOver:.2f}%'.format(**AMxAsDict))

    ax1.set_title('The %d stars separated by D = [%.2f, %.2f] %s' %
                  (len(AMx.rmsDistMas), AMx.annulus[0], AMx.annulus[1], AMx.annulusUnits))
    ax1.set_xlim(0.0, 100.0)
    ax1.set_xlabel('rms Relative Separation (%s)' % AMx.rmsUnits)
    ax1.set_ylabel('# pairs / bin')

    ax1.legend(loc='upper right', fontsize=16)

    figName = outputPrefix+'%s_D_%d_%s_%.1f-%.1f.png' % \
        (AMx.name, int(sum(AMx.annulus)/2), AMx.DUnits.upper(), AMx.magRange[0], AMx.magRange[1])

    plt.savefig(figName, dpi=300)
    plt.close(fig)

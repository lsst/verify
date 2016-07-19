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
from .matchreduce import fitExp, expModel, astromErrModel, photErrModel


__all__ = ['plotOutlinedLinesHorizontal', 'plotOutlinedLinesVertical',
           'plotOutlinedLines', 'plotOutlinedAxline',
           'plotAnalyticAstrometryModel', 'plotExpFit',
           'plotAstromErrModelFit', 'plotPhotErrModelFit',
           'plotAnalyticPhotometryModel', 'plotPA1', 'plotAMx']


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

    The motivation is to let horizontal lines stand out clearly even against a
    cluttered background.
    """
    plotOutlinedLines(ax.axvline, *args, **kwargs)


def plotOutlinedLines(ax_plot, x1, x2, x1_color=color['all'],
                      x2_color=color['bright']):
    """Plot horizontal lines outlined in white.

    The motivation is to let horizontal lines stand out clearly even against a
    cluttered background.
    """
    ax_plot(x1, color='white', linewidth=4)
    ax_plot(x2, color='white', linewidth=4)
    ax_plot(x1, color=x1_color, linewidth=3)
    ax_plot(x2, color=x2_color, linewidth=3)


def plotOutlinedAxline(axMethod, x, **kwargs):
    shadowArgs = dict(kwargs)
    foregroundArgs = dict(kwargs)

    if 'linewidth' not in foregroundArgs:
        foregroundArgs['linewidth'] = 3

    if 'linewidth' in shadowArgs:
        shadowArgs['linewidth'] += 1
    else:
        shadowArgs['linewidth'] = 4
    shadowArgs['color'] = 'w'
    shadowArgs['label'] = None

    axMethod(x, **shadowArgs)
    axMethod(x, **foregroundArgs)


def plotAnalyticAstrometryModel(dataset, astromModel, outputPrefix=''):
    """Plot angular distance between matched sources from different exposures.

    Creates a file containing the plot with a filename beginning with
    `outputPrefix`.

    Parameters
    ----------
    dataset : `MatchedMultiVisitDataset`
        Blob with the multi-visit photometry model.
    photomModel : `AnalyticPhotometryModel`
        An analyticPhotometry model object.
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot
        titles. E.g., ``outputPrefix='Cfht_output_r_'`` will result in a file
        named ``'Cfht_output_r_check_astrometry.png'``.
    """
    bright, = np.where(dataset.snr > astromModel.brightSnr)

    numMatched = len(dataset.dist)
    dist_median = np.median(dataset.dist)
    bright_dist_median = np.median(dataset.dist[bright])

    fig, ax = plt.subplots(ncols=2, nrows=1, figsize=(18, 12))

    ax[0].hist(dataset.dist, bins=100, color=color['all'],
               histtype='stepfilled', orientation='horizontal')
    ax[0].hist(dataset.dist[bright], bins=100, color=color['bright'],
               histtype='stepfilled', orientation='horizontal')

    ax[0].set_ylim([0., 500.])
    ax[0].set_ylabel("Distance [{units}]".format(
        units=dataset.datums['dist'].latex_units))
    plotOutlinedAxline(
        ax[0].axhline, dist_median,
        color=color['all'],
        label="Median RMS: {v:.1f} [{u}]".format(
            v=dist_median, u=dataset.datums['dist'].latex_units))
    plotOutlinedAxline(
        ax[0].axhline, bright_dist_median,
        color=color['bright'],
        label="SNR > {snr:.0f}\nMedian RMS: {v:.1f} [{u}]".format(
            snr=astromModel.brightSnr,
            v=bright_dist_median, u=dataset.datums['dist'].latex_units))
    ax[0].legend(loc='upper right')

    ax[1].scatter(dataset.snr, dataset.dist,
                  s=10, color=color['all'], label='All')
    ax[1].scatter(dataset.snr[bright], dataset.dist[bright], s=10,
                  color=color['bright'],
                  label='SNR > %.0f' % astromModel.brightSnr)
    ax[1].set_xlabel("SNR")
    ax[1].set_xscale("log")
    ax[1].set_ylim([0., 500.])
    matchCountTemplate = '\n'.join([
        'Matches:',
        '{nBright:d} high SNR,',
        '{nAll:d} total'])
    ax[1].text(0.6, 0.6, matchCountTemplate.format(nBright=len(bright),
                                                   nAll=numMatched),
               transform=ax[1].transAxes, ha='left', va='baseline')

    w, = np.where(dataset.dist < 200)
    plotAstromErrModelFit(dataset.snr[w], dataset.dist[w], astromModel,
                          ax=ax[1])

    ax[1].legend(loc='upper right')
    ax[1].axvline(astromModel.brightSnr,
                  color='red', linewidth=4, linestyle='dashed')
    plotOutlinedAxline(
        ax[0].axhline, dist_median,
        color=color['all'])
    plotOutlinedAxline(
        ax[0].axhline, bright_dist_median,
        color=color['bright'])

    plt.suptitle("Astrometry Check : %s" % outputPrefix.rstrip('_'),
                 fontsize=30)
    plotPath = outputPrefix+"check_astrometry.png"
    plt.savefig(plotPath, format="png")
    plt.close(fig)


def plotExpFit(x, y, y_err, fit_params=None, deg=2, ax=None, verbose=False):
    """Plot an exponential quadratic fit to x, y, y_err.

    Parameters
    ----------
    fit_params : list or numpy.array
        Fit parameters to display
        If None, then will be fit.
    """

    if ax is None:
        ax = plt.figure()
        xlim = [1, 1e4]
    else:
        xlim = ax.get_xlim()

    if fit_params is None:
        fit_params = fitExp(x, y, y_err, deg=2)

    x_model = np.linspace(*xlim, num=100)
    fit_model = expModel(x_model, *fit_params)
    label = '%.4g exp(mag/%.4g) + %.4g' % \
            (fit_params[0], fit_params[2], fit_params[1])
    if verbose:
        print(fit_params)
        print(label)

    ax.plot(x_model, fit_model, color='red',
            label=label)


def plotAstromErrModelFit(snr, dist, model,
                          color='red', ax=None, verbose=True):
    """Plot model of photometric error from LSST Overview paper
    http://arxiv.org/abs/0805.2366v4

    Astrometric Errors
    error = C * theta / SNR

    Parameters
    ----------
    snr : list or numpy.array
        S/N of photometric measurements
    dist : list or numpy.array
        Separation from reference [mas]
    model : `AnalyticAstrometryModel`
        An `AnalyticAstrometryModel` instance.
    """
    if ax is None:
        ax = plt.figure()
        xlim = [10, 30]
    else:
        xlim = ax.get_xlim()

    x_model = np.logspace(np.log10(xlim[0]), np.log10(xlim[1]), num=100)
    fit_model_mas_err = astromErrModel(x_model,
                                       theta=model.theta,
                                       sigmaSys=model.sigmaSys,
                                       C=model.C)
    # labelTemplate = r'$C, \theta, \sigma_{{\rm sys}}$ = ' + '\n' + \
    #     '{C:.2g}, {theta:.4g}, {sigmaSys:.4g} [mas]'
    # label = labelTemplate.format(theta=model['theta'].value,
    #                              sigmaSys=model['sigmaSys'].value,
    #                              C=model['C'].value)
    ax.plot(x_model, fit_model_mas_err,
            color=color, linewidth=2,
            label='Model')

    modelLabelTemplate = '\n'.join([
        r'$C = {C:.2g}$',
        r'$\theta = {theta:.4g}$',
        r'$\sigma_\mathrm{{sys}} = {sigmaSys:.2g}$ {sigmaSysUnits}'])
    modelLabel = modelLabelTemplate.format(
        C=model.C,
        theta=model.theta,
        sigmaSys=model.sigmaSys,
        sigmaSysUnits=model.datums['sigmaSys'].latex_units)
    ax.text(0.6, 0.4, modelLabel,
            transform=ax.transAxes, va='baseline', ha='left', color=color)
    # Set the x limits back to their original values.
    ax.set_xlim(xlim)


def plotPhotErrModelFit(mag, mmag_err, photomModel, color='red', ax=None,
                        verbose=True):
    """Plot model of photometric error from LSST Overview paper (Eq. 4 & 5)

    Parameters
    ----------
    mag : list or numpy.array
        Magnitude
    mmag_err : list or numpy.array
        Magnitude uncertainty or variation in *mmag*.
    photomModel : `AnalyticPhotometryModel`
        Fit parameters to display.
    ax : matplotlib.Axis, optional
        The Axis object to plot to.
    verbose : bool, optional
        Produce extra output to STDOUT
    """

    if ax is None:
        ax = plt.figure()
        xlim = [10, 30]
    else:
        xlim = ax.get_xlim()

    x_model = np.linspace(*xlim, num=100)
    fit_model_mag_err = photErrModel(x_model,
                                     sigmaSys=photomModel.sigmaSys,
                                     gamma=photomModel.gamma,
                                     m5=photomModel.m5)
    fit_model_mmag_err = 1000*fit_model_mag_err
    ax.plot(x_model, fit_model_mmag_err,
            color=color, linewidth=2,
            label='Model')

    labelFormatStr = '\n'.join([
        r'$\sigma_\mathrm{{sys}} = {sigmaSysMmag:6.4f}~\mathrm{{[mmag]}}$',
        r'$\gamma = {gamma:6.4f}$',
        r'$m_5 = {m5:6.4f}~\mathrm{{[mag]}}$'])
    label = labelFormatStr.format(sigmaSysMmag=1000*photomModel.sigmaSys,
                                  gamma=photomModel.gamma,
                                  m5=photomModel.m5)
    ax.text(0.1, 0.8, label, color=color,
            transform=ax.transAxes, ha='left', va='top')


def plotMagerrFit(*args, **kwargs):
    plotExpFit(*args, **kwargs)


def plotAnalyticPhotometryModel(dataset, photomModel,
                                filterName='', outputPrefix=''):
    """Plot photometric RMS for matched sources.

    Parameters
    ----------
    dataset : `MatchedMultiVisitDataset`
        Blob with the multi-visit photometry model.
    photomModel : `AnalyticPhotometryModel`
        An analyticPhotometry model object.
    filterName : str, optional
        Name of the observed filter to use on axis labels.
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot
        titles. E.g., ``outputPrefix='Cfht_output_r_'`` will result in a file
        named ``'Cfht_output_r_check_photometry.png'``.
    """
    bright, = np.where(dataset.snr > photomModel.brightSnr)

    numMatched = len(dataset.mag)
    mmagRms = dataset.magrms * 1000.
    mmagRmsHighSnr = mmagRms[bright]
    mmagErr = dataset.magerr * 1000.
    mmagErrHighSnr = mmagErr[bright]

    mmagrms_median = np.median(mmagRms)
    bright_mmagrms_median = np.median(mmagRmsHighSnr)

    fig, ax = plt.subplots(ncols=2, nrows=2, figsize=(18, 16))

    ax[0][0].hist(mmagRms,
                  bins=100, range=(0, 500), color=color['all'],
                  histtype='stepfilled', orientation='horizontal')
    ax[0][0].hist(mmagRmsHighSnr,
                  bins=100, range=(0, 500),
                  color=color['bright'],
                  histtype='stepfilled', orientation='horizontal')
    plotOutlinedAxline(
        ax[0][0].axhline, mmagrms_median,
        color=color['all'],
        label="Median RMS: {v:.1f} [mmag]".format(v=mmagrms_median))
    plotOutlinedAxline(
        ax[0][0].axhline, bright_mmagrms_median,
        color=color['bright'],
        label="SNR > {snr:.0f}\nMedian RMS: {v:.1f} [{u}]".format(
            snr=photomModel.brightSnr,
            v=bright_mmagrms_median, u='mmag'))
    ax[0][0].set_ylim([0, 500])
    ax[0][0].set_ylabel("{0} [mmag]".format(dataset.datums['magrms'].label))
    ax[0][0].legend(loc='upper right')

    ax[0][1].scatter(dataset.mag, mmagRms,
                     s=10, color=color['all'], label='All')
    ax[0][1].scatter(dataset.mag[bright], mmagRmsHighSnr,
                     s=10, color=color['bright'],
                     label='{label} > {value:.0f}'.format(
                         label=photomModel.datums['brightSnr'].label,
                         value=photomModel.brightSnr))

    ax[0][1].set_xlabel("%s [mag]" % filterName)
    ax[0][1].set_ylabel("RMS [mmag]")
    ax[0][1].set_xlim([17, 24])
    ax[0][1].set_ylim([0, 500])
    ax[0][1].legend(loc='upper left')
    plotOutlinedAxline(
        ax[0][1].axhline, mmagrms_median,
        color=color['all'])
    plotOutlinedAxline(
        ax[0][1].axhline, bright_mmagrms_median,
        color=color['bright'])
    matchCountTemplate = '\n'.join([
        'Matches:',
        '{nBright:d} high SNR,',
        '{nAll:d} total'])
    ax[0][1].text(0.1, 0.6, matchCountTemplate.format(nBright=len(bright),
                                                      nAll=numMatched),
                  transform=ax[0][1].transAxes, ha='left', va='top')

    ax[1][0].scatter(mmagRms, mmagErr,
                     s=10, color=color['all'], label=None)
    ax[1][0].scatter(mmagRmsHighSnr, mmagErrHighSnr,
                     s=10, color=color['bright'],
                     label=None)
    ax[1][0].set_xscale('log')
    ax[1][0].set_yscale('log')
    ax[1][0].plot([0, 1000], [0, 1000],
                  linestyle='--', color='black', linewidth=2)
    ax[1][0].set_xlabel("RMS [mmag]")
    ax[1][0].set_ylabel("Median Reported Magnitude Err [mmag]")

    brightSnrInMmag = 2.5*np.log10(1 + (1/photomModel.brightSnr)) * 1000
    ax[1][0].axhline(brightSnrInMmag, color='red', linewidth=4,
                     linestyle='dashed',
                     label=r'$SNR > %.0f \equiv \sigma_\mathrm{mmag} <  %0.1f$'
                     % (photomModel.brightSnr, brightSnrInMmag))
    ax[1][0].set_xlim([1, 500])
    ax[1][0].set_ylim([1, 500])
    ax[1][0].legend(loc='upper center')

    ax[1][1].scatter(dataset.mag, mmagErr,
                     color=color['all'], label=None)
    ax[1][1].set_yscale('log')
    ax[1][1].scatter(np.asarray(dataset.mag)[bright],
                     mmagErrHighSnr,
                     s=10, color=color['bright'],
                     label=None)
    ax[1][1].set_xlabel("%s [mag]" % filterName)
    ax[1][1].set_ylabel("Median Reported Magnitude Err [mmag]")
    ax[1][1].set_xlim([17, 24])
    ax[1][1].set_ylim([1, 500])
    ax[1][1].axhline(brightSnrInMmag, color='red', linewidth=4,
                     linestyle='dashed',
                     label=None)
    # label=r'$\sigma_\mathrm{mmag} < $ %0.1f' % (brightSnrInMmag))

    # FIXME as originally implemented this makes the plot hard to interpret
    # ax2 = ax[1][1].twinx()
    # ax2.scatter(dataset.mag, dataset.snr,
    #             color=color['all'], facecolor='none',
    #             marker='.', label=None)
    # ax2.scatter(np.asarray(dataset.mag)[bright],
    #             np.asarray(dataset.snr)[bright],
    #             color=color['bright'], facecolor='none',
    #             marker='.', label=None)
    # ax2.set_ylim(bottom=0)
    # ax2.set_ylabel("SNR")
    # ax2.axhline(photomModel.brightSnr,
    #             color='red', linewidth=2, linestyle='dashed',
    #             label=r'SNR > {0:.0f}'.format(float(photomModel.brightSnr)))

    w, = np.where(mmagErr < 200)
    plotPhotErrModelFit(dataset.mag[w], dataset.magerr[w] * 1000.,
                        photomModel, ax=ax[1][1])
    ax[1][1].legend(loc='upper left')

    plt.suptitle("Photometry Check : %s" % outputPrefix.rstrip('_'),
                 fontsize=30)
    plotPath = outputPrefix+"check_photometry.png"
    plt.savefig(plotPath, format="png")
    plt.close(fig)


def plotPA1(pa1, outputPrefix=""):
    """Plot the results of calculating the LSST SRC requirement PA1.

    Creates a file containing the plot with a filename beginning with
    `outputPrefix`.

    Parameters
    ----------
    pa1 : `PA1Measurement`
        A `PA1Measurement` object.
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot
        titles. E.g., outputPrefix='Cfht_output_r_' will result in a file
        named ``'Cfht_output_r_AM1_D_5_arcmin_17.0-21.5.png'``
        for an ``AMx.name=='AM1'`` and ``AMx.magRange==[17, 21.5]``.
    """
    diffRange = (-100, +100)

    fig = plt.figure(figsize=(18, 12))
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.scatter(pa1.magMean[0],
                pa1.magDiff[0],
                s=10, color=color['bright'], linewidth=0)
    # index 0 because we show only the first sample from multiple trials
    ax1.axhline(+pa1.rms[0], color=color['rms'], linewidth=3)
    ax1.axhline(-pa1.rms[0], color=color['rms'], linewidth=3)
    ax1.axhline(+pa1.iqr[0], color=color['iqr'], linewidth=3)
    ax1.axhline(-pa1.iqr[0], color=color['iqr'], linewidth=3)

    ax2 = fig.add_subplot(1, 2, 2, sharey=ax1)
    ax2.hist(pa1.magDiff[0], bins=25, range=diffRange,
             orientation='horizontal', histtype='stepfilled',
             normed=True, color=color['bright'])
    ax2.set_xlabel("relative # / bin")

    yv = np.linspace(diffRange[0], diffRange[1], 100)
    ax2.plot(scipy.stats.norm.pdf(yv, scale=pa1.rms[0]), yv,
             marker='', linestyle='-', linewidth=3, color=color['rms'],
             label=r"PA1(RMS) = %4.2f %s" % (pa1.rms[0],
                                             pa1.extras['rms'].latex_units))
    ax2.plot(scipy.stats.norm.pdf(yv, scale=pa1.iqr[0]), yv,
             marker='', linestyle='-', linewidth=3, color=color['iqr'],
             label=r"PA1(IQR) = %4.2f %s" % (pa1.iqr[0],
                                             pa1.extras['iqr'].latex_units))
    ax2.set_ylim(*diffRange)
    ax2.legend()
    # ax1.set_ylabel(u"12-pixel aperture magnitude diff (mmag)")
    # ax1.set_xlabel(u"12-pixel aperture magnitude")
    ax1.set_xlabel("psf magnitude")
    ax1.set_ylabel(r"psf magnitude diff (%s)" % pa1.extras['magDiff'].latex_units)
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


def plotAMx(amx, afx, bandpass, amxSpecName='design', outputPrefix=""):
    """Plot a histogram of the RMS in relative distance between pairs of
    stars.

    Creates a file containing the plot with a filename beginning with
    `outputPrefix`.

    Parameters
    ----------
    amx : `AMxMeasurement`
    afx : `AFxMeasurement`
    outputPrefix : str, optional
        Prefix to use for filename of plot file.  Will also be used in plot
        titles. E.g., ``outputPrefix='Cfht_output_r_'`` will result in a file
        named ``'Cfht_output_r_AM1_D_5_arcmin_17.0-21.5.png'``
        for an ``AMx.name=='AM1'`` and ``AMx.magRange==[17, 21.5]``.
    """

    # percentOver = 100*AMx.fractionOver

    # AMxAsDict = AMx.getDict()
    # AMxAsDict['AMxADx'] = AMxAsDict['AMx_spec']+AMxAsDict['ADx_spec']
    # AMxAsDict['percentOver'] = percentOver

    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(1, 1, 1)

    histLabelTemplate = 'D: [{inner:.1f}-{outer:.1f}] {annulusUnits}\n'\
                        'Mag: [{magBright:.1f}-{magFaint:.1f}]'
    ax1.hist(amx.rmsDistMas, bins=25, range=(0.0, 100.0),
             histtype='stepfilled',
             label=histLabelTemplate.format(
                 inner=amx.annulus[0],
                 outer=amx.annulus[1],
                 annulusUnits=amx.parameters['annulus'].latex_units,
                 magBright=amx.magRange[0],
                 magFaint=amx.magRange[1]))

    if amx.checkSpec(amxSpecName):
        amxStatus = 'passed'
    else:
        amxStatus = 'failed'
    amxLabel = 'Median RMS\n' + \
               '{amx} measured: {amxValue:.1f} {amxUnits} ({status})'.format(
                   amx=amx.label,
                   amxValue=amx.value,
                   amxUnits=amx.latex_units,
                   status=amxStatus)
    ax1.axvline(amx.value, 0, 1, linewidth=2, color='black',
                label=amxLabel)

    amxSpec = amx.metric.getSpec(amxSpecName, bandpass=bandpass)
    amxSpecLabel = '{name} {specname}: {value:.0f} {units}'.format(
        name=amx.label,
        specname=amxSpecName,
        value=amxSpec.value,
        units=amxSpec.latex_units)
    ax1.axvline(amxSpec.value, 0, 1, linewidth=2, color='red',
                label=amxSpecLabel)

    if afx.checkSpec(afx.specName):
        afxStatus = 'passed'
    else:
        afxStatus = 'failed'
    afxLabelTemplate = '{afx} {specname}: {afxSpec}%\n' + \
                       '{afx} measured: {afxValue:.1f}% ({status})'
    afxLabel = afxLabelTemplate.format(
        afx=afx.label,
        specname=afx.specName,
        afxSpec=afx.metric.getSpec(afx.specName, bandpass=bandpass).value,
        afxValue=afx.value,
        status=afxStatus)

    ax1.axvline(amx.value + afx.ADx,
                0, 1, linewidth=2, color='green',
                label=afxLabel)

    title = '{metric} Astrometric Repeatability over {D:d} {units}'.format(
        metric=amx.label,
        D=int(amx.D),
        units=amx.parameters['D'].latex_units)
    ax1.set_title(title)
    ax1.set_xlim(0.0, 100.0)
    ax1.set_xlabel('{label} ({units})'.format(
        label=amx.extras['rmsDistMas'].label,
        units=amx.extras['rmsDistMas'].latex_units))
    ax1.set_ylabel('# pairs / bin')

    ax1.legend(loc='upper right', fontsize=16)

    plotPath = '{prefix}{metric}_D_{D:d}_{Dunits}_{magBright}_{magFaint}.{ext}'.format(
        prefix=outputPrefix,
        metric=amx.label,
        D=int(amx.D),
        Dunits=amx.parameters['D'].latex_units,
        magBright=amx.magRange[0],
        magFaint=amx.magRange[1],
        ext='png')

    plt.savefig(plotPath, dpi=300)
    plt.close(fig)

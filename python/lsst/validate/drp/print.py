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

from .srdSpec import srdSpec


def printPA1(PA1):
    """Print the calculated PA1 from the LSST SRD."""
    print("PA1(RMS) = %4.2f+-%4.2f %s" % (PA1.rms, PA1.rmsStd, PA1.rmsUnits))
    print("PA1(IQR) = %4.2f+-%4.2f %s" % (PA1.iqr, PA1.iqrStd, PA1.iqrUnits))


def printPA2(pa2):
    """Print the calculated PA2 and PF1 from the LSST SRD."""
    print('--')
    for level in ('minimum', 'design', 'stretch'):
        print("%-7s: PF1=%2d%s of diffs more than PA2 = %4.2f %s (target is < %2.0f %s)" %
              (level, pa2.PF1_spec[level], pa2.pf1Units, pa2.PA2_measured[level], pa2.pa2Units,
               srdSpec.PA2[level], srdSpec.pa2Units))

    print('--')
    for level in ('minimum', 'design', 'stretch'):
        print("%-7s: PF1=%2d%s of diffs more than PA2 = %4.2f %s (target is < %2.0f %s)" %
              (level, pa2.PF1_measured[level], pa2.pf1Units, pa2.PA2_spec[level], pa2.pa2Units,
               srdSpec.PF1[level], srdSpec.pf1Units))


def printAMx(AMx):
    """Print the Astrometric performance.

    Parameters
    ----------
    AMx : pipeBase.Struct
        Must contain:
        AMx, fractionOver, annulus, magRange, x, level,
        AMx_spec, AFx_spec, ADx_spec
    """

    percentOver = 100*AMx.fractionOver

    print("Median RMS of distances between pairs of stars.")
    print("  %s goals" % AMx.level.upper())
    print("  For stars from %.2f < mag < %.2f and D = [%.2f, %.2f] %s" %
          (AMx.magRange[0], AMx.magRange[1], AMx.annulus[0], AMx.annulus[1], AMx.annulusUnits))
    print("%s=%.2f %s (target is < %.0f %s)." %
          (AMx.name, AMx.AMx, AMx.amxUnits, AMx.AMx_spec, AMx.amxUnits))
    print("  %.2f%% of sample deviates by >%.0f %s (target is < %.0f%%)" %
          (percentOver, AMx.ADx_spec+AMx.AMx_spec, AMx.adxUnits, AMx.AFx_spec))

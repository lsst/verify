# This file is part of verify.
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

__all__ = ["time_this_to_measurement"]

from contextlib import contextmanager
import time

import astropy.units as u

from .datum import Datum
from .measurement import Measurement


def _epoch_to_iso(seconds):
    """Convert a time in seconds since Unix epoch to an ISO 8601 timestamp.

    Parameters
    ----------
    seconds : `float`
        The number of seconds since the Unix epoch.

    Returns
    -------
    timestamp : `str`
        The input time represented as a timestamp.
    """
    iso_format = "%Y-%m-%dT%H:%M:%SZ"
    return time.strftime(iso_format, time.gmtime(seconds))


@contextmanager
def time_this_to_measurement(measurement: Measurement):
    """Time the enclosed block and record it as an lsst.verify measurement.

    Parameters
    ----------
    measurement : `lsst.verify.Measurement`
        Measurement object to fill with the timing information. Its metric must
        have time dimensions. Any properties other than ``metric`` and
        ``metric_name`` may be overwritten.
    """
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        measurement.quantity = (end - start) * u.second
        # Same metadata as provided by TimingMetricTask
        measurement.notes["estimator"] = "verify.timer.time_this_to_measurement"
        measurement.extras["start"] = Datum(_epoch_to_iso(start))
        measurement.extras["end"] = Datum(_epoch_to_iso(end))

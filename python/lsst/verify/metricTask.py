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


__all__ = ["MetricComputationError"]


class MetricComputationError(RuntimeError):
    """This class represents unresolvable errors in computing a metric.

    `compatibility.MetricTask` raises ``MetricComputationError`` instead of
    other data- or processing-related exceptions to let code that calls a mix
    of data processing and metric tasks distinguish between the two.
    Therefore, most ``MetricComputationError`` instances should be chained to
    another exception representing the underlying problem.
    """
    pass

# TODO: implement MetricTask once PipelineTask is ready for general use

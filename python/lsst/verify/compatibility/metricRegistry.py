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

__all__ = []

from lsst.pex.config import Registry


class MetricRegistry:
    """Registry of all `lsst.verify.compatibility.MetricTask` subclasses known
    to `lsst.verify`'s client.

    Notes
    -----
    This class has a singleton-like architecture in case a custom subclass of
    `lsst.pex.config.Registry` is needed in the future. Code that refers to
    ``MetricRegistry.registry`` should be agnostic to such changes.
    """

    registry = Registry()
    """A unique registry of ``MetricTasks`` (`lsst.pex.config.Registry`).
    """

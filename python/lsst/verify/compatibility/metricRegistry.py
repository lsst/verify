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

__all__ = ["register"]

from lsst.pex.config import Registry
from .metricTask import MetricTask


def register(name):
    """A class decorator that registers a `lsst.verify.compatibility.MetricTask`
    with a central repository.

    Parameters
    ----------
    name : `str`
        The name under which this decorator will register the
        `~lsst.verify.compatibility.MetricTask`.

    Raises
    ------
    RuntimeError
        Raised if another class has already been registered under ``name``.
    ValueError
        Raised if this decorator is applied to a class that is not a
        `lsst.verify.compatibility.MetricTask`.

    Notes
    -----
    This decorator must be used for any `~lsst.verify.compatibility.MetricTask`
    that is to be used with `lsst.verify.compatibility.MetricsControllerTask`.

    Examples
    --------
    The decorator is applied at the class definition:

    >>> from lsst.verify.compatibility import register, MetricTask
    >>> @register("dummy")
    ... class DummyMetricTask(MetricTask):
    ...     pass
    """
    def wrapper(taskClass):
        if issubclass(taskClass, MetricTask):
            # TODO: if MetricRegistry is phased out, simply return taskClass
            # instead of removing the decorator
            MetricRegistry.registry.register(name, taskClass)
            return taskClass
        else:
            raise ValueError("%r is not a %r" % (taskClass, MetricTask))
    return wrapper


class MetricRegistry:
    """Registry of all `lsst.verify.compatibility.MetricTask` subclasses known
    to `lsst.verify`'s client.

    Notes
    -----
    This class has a singleton-like architecture in case a custom subclass of
    `lsst.pex.config.Registry` is needed in the future. Code that refers to
    ``MetricRegistry.registry`` should be agnostic to such changes.
    """

    registry = Registry(MetricTask.ConfigClass)
    """A unique registry of ``MetricTasks`` (`lsst.pex.config.Registry`).
    """

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

__all__ = ["register", "registerMultiple"]

from lsst.pex.config import Config, ConfigDictField, Registry
# Avoid importing tasks, which causes circular dependency
from ..tasks.metricTask import MetricTask


def register(name):
    """A class decorator that registers a
    `lsst.verify.tasks.MetricTask` with a central repository.

    Parameters
    ----------
    name : `str`
        The name under which this decorator will register the
        `~lsst.verify.tasks.MetricTask`.

    Raises
    ------
    RuntimeError
        Raised if another class has already been registered under ``name``.
    ValueError
        Raised if this decorator is applied to a class that is not a
        `lsst.verify.tasks.MetricTask`.

    Notes
    -----
    This decorator must be used for any
    `~lsst.verify.tasks.MetricTask` that is to be used with
    `lsst.verify.gen2tasks.MetricsControllerTask`.

    Examples
    --------
    The decorator is applied at the class definition:

    >>> from lsst.verify.gen2tasks import register
    >>> from lsst.verify.tasks import MetricTask
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


def registerMultiple(name):
    """A class decorator that registers a
    `lsst.verify.tasks.MetricTask` with a central repository.

    Unlike `register`, this decorator assumes the same
    `~lsst.verify.tasks.MetricTask` class will be run by
    `lsst.verify.gen2tasks.MetricsControllerTask` multiple times with
    different configs.

    Parameters
    ----------
    name : `str`
        The name under which this decorator will register the
        `~lsst.verify.tasks.MetricTask`.

    Raises
    ------
    RuntimeError
        Raised if another class has already been registered under ``name``.
    ValueError
        Raised if this decorator is applied to a class that is not a
        `lsst.verify.tasks.MetricTask`.

    Notes
    -----
    This decorator must be used for any
    `~lsst.verify.tasks.MetricTask` that will have multiple
    instances used with `lsst.verify.gen2tasks.MetricsControllerTask`.

    The registry entry produced by this decorator corresponds to an anonymous
    `~lsst.pex.config.Config` class with one field, ``configs``. ``configs``
    is a `~lsst.pex.config.ConfigDictField` that may have any number of
    configs attached to it. The field will create multiple
    `~lsst.verify.tasks.MetricTask` objects, one for each config
    provided. See
    :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` for an
    example of how to use ``configs``.

    Examples
    --------
    The decorator is applied at the class definition:

    >>> from lsst.verify.gen2tasks import registerMultiple
    >>> from lsst.verify.tasks import MetricTask
    >>> @registerMultiple("reusable")
    ... class ReusableMetricTask(MetricTask):
    ...     pass
    """
    def wrapper(taskClass):
        if issubclass(taskClass, MetricTask):
            # TODO: if MetricRegistry is phased out, simply return taskClass
            # instead of removing the decorator
            MetricRegistry.registry.register(
                name,
                _MultiConfigFactory(taskClass),
                ConfigClass=_makeMultiConfig(taskClass.ConfigClass))
            return taskClass
        else:
            raise ValueError("%r is not a %r" % (taskClass, MetricTask))
    return wrapper


def _makeMultiConfig(configClass):
    """A factory function for creating a config for registerMultiple.

    Parameters
    ----------
    configClass : `lsst.verify.tasks.MetricTask.ConfigClass`-type
        The type of task config to be stored inside the new config. Subclasses
        of ``configClass`` will **NOT** be supported (this is a limitation of
        `~lsst.pex.config.ConfigDictField`).

    Returns
    -------
    multiConfig : `lsst.pex.config.Config`-type
        A `~lsst.pex.config.Config` class containing the following fields:

        configs : `lsst.pex.config.ConfigDictField`
            A field that maps `str` to ``configClass``. The keys are arbitrary
            and can be chosen for user convenience.
    """
    class MultiConfig(Config):
        configs = ConfigDictField(
            keytype=str, itemtype=configClass, optional=False,
            default={},
            doc="A collection of multiple configs to create multiple items "
                "of the same type.")

    return MultiConfig


class _MultiConfigFactory:
    """A factory class for creating multiple `MetricTask` objects at once.

    Parameters
    ----------
    configurableClass : `lsst.verify.tasks.MetricTask`-type
        The type of configurable created by `__call__`.
    """
    def __init__(self, configurableClass):
        self._configurableClass = configurableClass

    def __call__(self, config, **kwargs):
        """Create the configured task(s).

        Parameters
        ----------
        config : type from ``_makeMultiConfig(configurableClass.ConfigClass)``
            A config containing multiple configs for ``configurableClass`.
        **kwargs
            Additional arguments to the ``configurableClass`` constructor.

        Returns
        -------
        tasks : iterable of ``configurableClass``
            A sequence of ``configurableClass``, one for each config in
            ``config``. The order in which the objects will be returned
            is undefined.
        """
        return [self._configurableClass(config=subConfig, **kwargs)
                for subConfig in config.configs.values()]


class MetricRegistry:
    """Registry of all `lsst.verify.tasks.MetricTask` subclasses known
    to `lsst.verify`'s client.

    Notes
    -----
    This class has a singleton-like architecture in case a custom subclass of
    `lsst.pex.config.Registry` is needed in the future. Code that refers to
    ``MetricRegistry.registry`` should be agnostic to such changes.
    """

    # Don't use MetricTask.ConfigClass, to accommodate MultiConfig
    registry = Registry(Config)
    """A unique registry of ``MetricTasks`` or collections of ``MetricTasks``
    (`lsst.pex.config.Registry`).
    """

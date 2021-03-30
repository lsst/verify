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

__all__ = ["MetricTask"]


import abc

from deprecated.sphinx import deprecated

# Avoid importing tasks, which causes circular dependency
from ..tasks.metricTask import MetricTask as Gen3MetricTask


# Docstring needs to have no leading whitespace for @deprecated to work
@deprecated(
    reason="Replaced by `lsst.verify.tasks.MetricTask`. "
           "To be removed along with daf_persistence.",
    version="v20.0",
    category=FutureWarning)
class MetricTask(Gen3MetricTask, metaclass=abc.ABCMeta):
    """A base class for tasks that compute one metric from input datasets.

Parameters
----------
*args
**kwargs
    Constructor parameters are the same as for
    `lsst.pipe.base.PipelineTask`.

Notes
-----
In general, both the ``MetricTask``'s metric and its input data are
configurable. Metrics may be associated with a data ID at any level of
granularity, including repository-wide.

Like `lsst.pipe.base.PipelineTask`, this class should be customized by
overriding `run` and by providing a `lsst.pipe.base.connectionTypes.Input`
for each parameter of `run`. For requirements that are specific to
``MetricTask``, see `run`.

.. note::
    The API is designed to make it easy to convert all ``MetricTasks`` to
    `~lsst.pipe.base.PipelineTask` later, but this class is *not* a
    `~lsst.pipe.base.PipelineTask` and does not work with activators,
    quanta, or `lsst.daf.butler`.
"""
    pass

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


__all__ = ["MetricComputationError", "MetricTask", "MetricConfig",
           "MetricConnections"]


import abc

import lsst.pipe.base as pipeBase
from lsst.pipe.base import connectionTypes

from lsst.verify import Name


class MetricComputationError(RuntimeError):
    """This class represents unresolvable errors in computing a metric.

    `lsst.verify.tasks.MetricTask` raises ``MetricComputationError``
    instead of other data- or processing-related exceptions to let code that
    calls a mix of data processing and metric tasks distinguish between
    the two. Therefore, most ``MetricComputationError`` instances should be
    chained to another exception representing the underlying problem.
    """
    pass


class MetricConnections(pipeBase.PipelineTaskConnections,
                        defaultTemplates={"package": None, "metric": None},
                        dimensions={"instrument", "visit", "detector"},
                        ):
    """An abstract connections class defining a metric output.

    This class assumes detector-level metrics, which is the most common case.
    Subclasses can redeclare ``measurement`` and ``dimensions`` to override
    this assumption.

    Notes
    -----
    ``MetricConnections`` defines the following dataset templates:
        ``package``
            Name of the metric's namespace. By
            :ref:`verify_metrics <verify-metrics-package>` convention, this is
            the name of the package the metric is most closely
            associated with.
        ``metric``
            Name of the metric, excluding any namespace.
    """
    measurement = connectionTypes.Output(
        name="metricvalue_{package}_{metric}",
        doc="The metric value computed by this task.",
        storageClass="MetricValue",
        dimensions={"instrument", "visit", "detector"},
    )


class MetricConfig(pipeBase.PipelineTaskConfig,
                   pipelineConnections=MetricConnections):

    def validate(self):
        super().validate()

        if "." in self.connections.package:
            raise ValueError(f"package name {self.connections.package} must "
                             "not contain periods")
        if "." in self.connections.metric:
            raise ValueError(f"metric name {self.connections.metric} must "
                             "not contain periods; use connections.package "
                             "instead")

    @property
    def metricName(self):
        """The metric calculated by a `MetricTask` with this config
        (`lsst.verify.Name`, read-only).
        """
        return Name(package=self.connections.package,
                    metric=self.connections.metric)


class MetricTask(pipeBase.PipelineTask, metaclass=abc.ABCMeta):
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
    """

    ConfigClass = MetricConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abc.abstractmethod
    def run(self, **kwargs):
        """Run the MetricTask on in-memory data.

        Parameters
        ----------
        **kwargs
            Keyword arguments matching the inputs given in the class config;
            see `lsst.pipe.base.PipelineTask.run` for more details.

        Returns
        -------
        struct : `lsst.pipe.base.Struct`
            A `~lsst.pipe.base.Struct` containing at least the
            following component:

            - ``measurement``: the value of the metric
              (`lsst.verify.Measurement` or `None`). This method is not
              responsible for adding mandatory metadata (e.g., the data ID);
              this is handled by the caller.

        Raises
        ------
        lsst.verify.tasks.MetricComputationError
            Raised if an algorithmic or system error prevents calculation
            of the metric. Examples include corrupted input data or
            unavoidable exceptions raised by analysis code. The
            `~lsst.verify.tasks.MetricComputationError` should be chained to a
            more specific exception describing the root cause.

            Not having enough data for a metric to be applicable is not an
            error, and should not trigger this exception.

        Notes
        -----
        All input data must be treated as optional. This maximizes the
        ``MetricTask``'s usefulness for incomplete pipeline runs or runs with
        optional processing steps. If a metric cannot be calculated because
        the necessary inputs are missing, the ``MetricTask`` must return `None`
        in place of the measurement.
        """

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """Do Butler I/O to provide in-memory objects for run.

        This specialization of runQuantum performs error-handling specific to
        MetricTasks. Most or all of this functionality may be moved to
        activators in the future.
        """
        # Synchronize changes to this method with ApdbMetricTask
        try:
            inputs = butlerQC.get(inputRefs)
            outputs = self.run(**inputs)
            if outputs.measurement is not None:
                butlerQC.put(outputs, outputRefs)
            else:
                self.log.debug("Skipping measurement of %r on %s "
                               "as not applicable.", self, inputRefs)
        except MetricComputationError:
            self.log.error(
                "Measurement of %r failed on %s->%s",
                self, inputRefs, outputRefs, exc_info=True)

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

__all__ = ["MetricsControllerConfig", "MetricsControllerTask"]

import os.path

import lsst.pex.config as pexConfig
import lsst.daf.persistence as dafPersist
from lsst.pipe.base import Task, Struct
from lsst.verify import Job
from lsst.verify.tasks import MetricComputationError
from .metadataTask import SquashMetadataTask
from .metricRegistry import MetricRegistry


def _flatten(nested):
    """Flatten an iterable of possibly nested iterables.

    Parameters
    ----------
    nested : iterable
        An iterable that may contain a mix of scalars or other iterables.

    Returns
    -------
    flat : sequence
        A sequence where each iterable element of `nested` has been replaced
        with its elements, in order, and so on recursively.

    Examples
    --------
    >>> x = [42, [4, 3, 5]]
    >>> _flatten(x)
    [42, 4, 3, 5]
    """
    flat = []
    for x in nested:
        try:
            iter(x)
            flat.extend(_flatten(x))
        except TypeError:
            flat.append(x)
    return flat


class MetricsControllerConfig(pexConfig.Config):
    """Configuration options for `MetricsControllerTask`.
    """
    jobFileTemplate = pexConfig.Field(
        dtype=str,
        doc="A template for the path to which the measurements are "
        "written. {id} is replaced with a unique index (recommended), "
        "while {dataId} is replaced with the data ID.",
        default="metrics{id}.{dataId}.verify.json",
    )
    metadataAdder = pexConfig.ConfigurableField(
        target=SquashMetadataTask,
        doc="Task for adding metadata needed by measurement clients. "
            "Its ``run`` method must take a `~lsst.verify.Job` as its first "
            "parameter, and should accept unknown keyword arguments. It must "
            "return a `~lsst.pipe.base.Struct` with the field ``job`` "
            "pointing to the modified job.",
    )
    measurers = MetricRegistry.registry.makeField(
        multi=True,
        doc=r"`MetricTask`\ s to call and their configuration. Each "
            "`MetricTask` must be identified by the name passed to its "
            "`~lsst.verify.gen2tasks.register` or "
            "`~lsst.verify.gen2tasks.registerMultiple` decorator.",
    )


class MetricsControllerTask(Task):
    """A Task for executing a collection of
    `lsst.verify.tasks.MetricTask` objects.

    This class handles Butler input of datasets needed by metrics, as well as
    persistence of the resulting measurements.

    Notes
    -----
    ``MetricsControllerTask`` is a stand-in for functionality provided by the
    Gen 3 Tasks framework. It will become redundant once we fully adopt
    that framework.

    Because ``MetricsControllerTask`` cannot support the full functionality of
    the Gen 3 framework, it places several restrictions on its metrics:

        * each ``MetricTask`` must measure a unique metric
        * no ``MetricTask`` may depend on the output of another ``MetricTask``
        * the granularity of the metrics is determined by the inputs to
          ``runDataRefs``; configuration information specifying a different
          granularity is allowed but is ignored
    """

    _DefaultName = "metricsController"
    ConfigClass = MetricsControllerConfig

    measurers = []
    """The tasks to be executed by this object (iterable of
    `lsst.verify.tasks.MetricTask`).
    """

    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self.makeSubtask("metadataAdder")

        self.measurers = _flatten(self.config.measurers.apply())

    def _computeSingleMeasurement(self, job, metricTask, dataref):
        """Call a single metric task on a single dataref.

        This method adds a single measurement to ``job``, as specified by
        ``metricTask``.

        Parameters
        ----------
        job : `lsst.verify.Job`
            A Job object in which to store the new measurement. Must not
            already contain a measurement for ``metricTask.config.metricName``.
        metricTask : `lsst.verify.tasks.MetricTask`
            The code for computing the measurement.
        dataref : `lsst.daf.persistence.ButlerDataRef`
            The repository and data ID to analyze. The data ID may be
            incomplete, but must have the granularity of the desired metric.

        Notes
        -----
        If measurement calculation fails, this method logs an error and leaves
        ``job`` unchanged.
        """
        self.log.debug("Running %s on %r", type(metricTask), dataref)
        inputTypes = metricTask.getInputDatasetTypes(metricTask.config)
        inputScalars = metricTask.areInputDatasetsScalar(metricTask.config)
        inputData = {}
        inputDataIds = {}
        for (param, dataType), scalar \
                in zip(inputTypes.items(), inputScalars.values()):
            inputRefs = dafPersist.searchDataRefs(
                dataref.getButler(), dataType, dataId=dataref.dataId)
            if scalar:
                inputData[param] = inputRefs[0].get() if inputRefs else None
                inputDataIds[param] = inputRefs[0].dataId if inputRefs else {}
            else:
                inputData[param] = [ref.get() for ref in inputRefs]
                inputDataIds[param] = [ref.dataId for ref in inputRefs]

        outputDataIds = {"measurement": dataref.dataId}
        try:
            result = metricTask.adaptArgsAndRun(inputData, inputDataIds,
                                                outputDataIds)
            value = result.measurement
            if value is not None:
                job.measurements.insert(value)
            else:
                self.log.debug(
                    "Skipping measurement of %r on %s as not applicable.",
                    metricTask, inputDataIds)
        except MetricComputationError:
            self.log.error("Measurement of %r failed on %s->%s",
                           metricTask, inputDataIds, outputDataIds,
                           exc_info=True)

    def runDataRefs(self, datarefs, customMetadata=None, skipExisting=False):
        """Call all registered metric tasks on each dataref.

        This method loads all datasets required to compute a particular
        metric, and persists the metrics as one or more `lsst.verify.Job`
        objects. Only metrics that successfully produce a
        `~lsst.verify.Measurement` will be included in a job.

        Parameters
        ----------
        datarefs : `list` of `lsst.daf.persistence.ButlerDataRef`
            The data to measure. Datarefs may be complete or partial; each
            generates a measurement at the same granularity (e.g., a
            dataref with only ``"visit"`` specified generates visit-level
            measurements).
        customMetadata : `dict`, optional
            Any metadata that are needed for a specific pipeline, but that are
            not needed by the ``lsst.verify`` framework or by general-purpose
            measurement analysis code (these cases are handled by the
            `~MetricsControllerConfig.metadataAdder` subtask). If omitted,
            only generic metadata are added. Both keys and values must be valid
            inputs to `~lsst.verify.Metadata`.
        skipExisting : `bool`, optional
            If this flag is set, MetricsControllerTask will skip computing
            metrics for any data ID that already has an output job file on
            disk. While this option is useful for restarting failed runs, it
            does *not* check whether the file is valid.

        Returns
        -------
        struct : `lsst.pipe.base.Struct`
            A `~lsst.pipe.base.Struct` containing the following component:

            - ``jobs`` : a list of collections of measurements (`list` of
              `lsst.verify.Job`). Each job in the list contains the
              measurement(s) for the corresponding dataref, and each job has
              at most one measurement for each element in `self.measurers`. A
              particular measurement is omitted if it could not be created.
              If ``skipExisting`` is set, any jobs that already exist on disk
              are also omitted.

        Notes
        -----
        Some objects may be persisted, or incorrectly persisted, in the event
        of an exception.
        """
        jobs = []
        index = 0
        for dataref in datarefs:
            jobFile = self._getJobFilePath(index, dataref.dataId)
            if not (skipExisting and os.path.isfile(jobFile)):
                job = Job.load_metrics_package()
                try:
                    self.metadataAdder.run(job, dataref=dataref)
                    if customMetadata:
                        job.meta.update(customMetadata)

                    for task in self.measurers:
                        self._computeSingleMeasurement(job, task, dataref)
                finally:
                    self.log.info("Persisting metrics to %s...", jobFile)
                    # This call order maximizes the chance that job gets
                    # written, and to a unique file
                    index += 1
                    job.write(jobFile)
                    jobs.append(job)
            else:
                self.log.debug("File %s already exists; skipping.", jobFile)

        return Struct(jobs=jobs)

    def _getJobFilePath(self, index, dataId):
        """Generate an output file for a Job.

        Parameters
        ----------
        index : `int`
            A unique integer across all Jobs created by this task.
        dataId : `lsst.daf.persistence.DataId`
            The identifier of all metrics in the Job to be persisted.
        """
        # Construct a relatively OS-friendly string (i.e., no quotes or {})
        idString = "_".join("%s%s" % (key, dataId[key]) for key in dataId)
        return self.config.jobFileTemplate.format(id=index, dataId=idString)

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

import traceback

import astropy.units as u

import lsst.pex.config as pexConfig
import lsst.daf.persistence as dafPersist
from lsst.pipe.base import Task, Struct
from lsst.verify import Job, Measurement, Name, MetricComputationError
from .metadataTask import SquashMetadataTask
from .metricTask import MetricTask


class MetricsControllerConfig(pexConfig.Config):
    """Global, metric-independent options for `MetricsControllerTask`.
    """
    jobFileTemplate = pexConfig.Field(
        dtype=str,
        doc="A template for the path to which the measurements are "
        "written. {id} is replaced with a unique index (recommended), "
        "while {dataId} is replaced with the data ID.",
        default="metrics{id}.{dataId}.verify.json")
    metadataAdder = pexConfig.ConfigurableField(
        target=SquashMetadataTask,
        doc="Task for adding metadata needed by measurement clients. "
            "Its ``run`` method must take a `~lsst.verify.Job` as its first "
            "parameter, and should accept unknown keyword arguments. It must "
            "return a `~lsst.pipe.base.Struct` with the field ``job`` "
            "pointing to the modified job.",
    )


class MetricsControllerTask(Task):
    """A Task for executing a collection of
    `lsst.verify.compatibility.MetricTask` objects.

    This class handles Butler input of datasets needed by metrics, as well as
    persistence of the resulting measurements.

    Notes
    -----
    ``MetricsControllerTask`` is a stand-in for functionality provided by the
    Gen 3 Tasks framework. It will become redundant once we fully adopt
    that framework.

    Because ``MetricsControllerTask`` cannot support the full functionality of
    the Gen 3 framework, it places several restrictions on its metrics:

        * no ``MetricTask`` may depend on the output of another ``MetricTask``
        * the granularity of the metrics is determined by the inputs to
          ``runDataRefs``; configuration information specifying a different
          granularity is allowed but is ignored

    Multiple instances of ``MetricsControllerTask`` are allowed. The
    recommended way to handle metrics of different granularities is to group
    metrics of the same granularity under a ``MetricsControllerTask``
    configured for that granularity.
    """

    _DefaultName = "metricsController"
    ConfigClass = MetricsControllerConfig

    measurers = []
    """The tasks to be executed by this object (iterable of
    `lsst.verify.compatibility.MetricTask`).
    """

    # TODO: remove this method in DM-16535
    def _makeTimingTask(self, target, metric):
        """Create a `~lsst.verify.compatibility.MetricTask` that can time
        a specific method.

        Parameters
        ----------
        target : `str`
            the method to time, optionally prefixed by one or more tasks in
            the format of `lsst.pipe.base.Task.getFullMetadata()`. All
            matching methods are counted by the task.
        metric : `str`
            the fully qualified name of the metric to contain the
            timing information

        Returns
        -------
        task : `TimingMetricTask`
            a ``MetricTask`` that times ``target`` and stores the information
            in ``metric``. It assumes ``target`` is called as part of
            `lsst.ap.pipe.ApPipeTask`.
        """
        config = TimingMetricTask.ConfigClass()
        config.metadataDataset = "apPipe_metadata"
        config.target = target
        config.metric = metric
        return TimingMetricTask(config=config)

    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self.makeSubtask("metadataAdder")

        # TODO: generalize in DM-16535
        self.measurers = [
            self._makeTimingTask("apPipe.runDataRef", "ap_pipe.ApPipeTime"),
            self._makeTimingTask("apPipe:ccdProcessor.runDataRef",
                                 "pipe_tasks.ProcessCcdTime"),
            self._makeTimingTask("apPipe:ccdProcessor:isr.runDataRef",
                                 "ip_isr.IsrTime"),
            self._makeTimingTask("apPipe:ccdProcessor:charImage.runDataRef",
                                 "pipe_tasks.CharacterizeImageTime"),
            self._makeTimingTask("apPipe:ccdProcessor:calibrate.runDataRef",
                                 "pipe_tasks.CalibrateTime"),
            self._makeTimingTask("apPipe:differencer.runDataRef",
                                 "pipe_tasks.ImageDifferenceTime"),
            self._makeTimingTask("apPipe:differencer:register.run",
                                 "pipe_tasks.RegisterImageTime"),
            self._makeTimingTask("apPipe:differencer:measurement.run",
                                 "ip_diffim.DipoleFitTime"),
            self._makeTimingTask("apPipe:associator.run",
                                 "ap_association.AssociationTime"),
        ]

    def _computeSingleMeasurement(self, job, metricTask, dataref):
        """Call a single metric task on a single dataref.

        This method adds a single measurement to ``job``, as specified by
        ``metricTask``.

        Parameters
        ----------
        job : `lsst.verify.Job`
            A Job object in which to store the new measurement. Must not
            already contain a measurement for
            ``metricTask.getOutputMetricName()``.
        metricTask : `lsst.verify.compatibility.MetricTask`
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
        inputData = {}
        inputDataIds = {}
        for param, dataType in inputTypes.items():
            inputRefs = dafPersist.searchDataRefs(
                dataref.getButler(), dataType, dataId=dataref.dataId)
            inputData[param] = [ref.get() for ref in inputRefs]
            inputDataIds[param] = [ref.dataId for ref in inputRefs]

        outputDataIds = {"measurement": dataref.dataId}
        try:
            result = metricTask.adaptArgsAndRun(inputData, inputDataIds,
                                                outputDataIds)
            value = result.measurement
            if value is not None:
                job.measurements.insert(value)
        except MetricComputationError:
            # Apparently lsst.log doesn't have built-in exception support?
            self.log.error("Measurement of %r failed on %s->%s\n%s",
                           metricTask, inputDataIds, outputDataIds,
                           traceback.format_exc())

    def runDataRefs(self, datarefs):
        """Call all registered metric tasks on each dataref.

        This method loads all datasets required to compute a particular
        metric, and persists the metrics as one or more `lsst.verify.Job`
        objects.

        Parameters
        ----------
        datarefs : `list` of `lsst.daf.persistence.ButlerDataRef`
            The data to measure. Datarefs may be complete or partial; each
            generates a measurement at the same granularity (e.g., a
            dataref with only ``"visit"`` specified generates visit-level
            measurements).

        Returns
        -------
        struct : `lsst.pipe.base.Struct`
            A `~lsst.pipe.base.Struct` containing the following component:

            - ``jobs`` : a list of collections of measurements (`list` of
              `lsst.verify.Job`). Each job in the list contains the
              measurement(s) for the corresponding dataref, and each job has
              at most one measurement for each element in `self.measurers`. A
              particular measurement is omitted if it could not be created.

        Notes
        -----
        Some objects may be persisted, or incorrectly persisted, in the event
        of an exception.
        """
        jobs = []
        index = 0
        for dataref in datarefs:
            job = Job.load_metrics_package()
            try:
                self.metadataAdder.run(job, dataref=dataref)

                for task in self.measurers:
                    self._computeSingleMeasurement(job, task, dataref)
            finally:
                jobFile = self._getJobFilePath(index, dataref.dataId)
                self.log.info("Persisting metrics to %s...", jobFile)
                # This call order maximizes the chance that job gets
                # written, and to a unique file
                index += 1
                job.write(jobFile)
                jobs.append(job)

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
        idString = " ".join("%s=%s" % (key, dataId[key]) for key in dataId)
        return self.config.jobFileTemplate.format(id=index, dataId=idString)


# A verbatim copy of lsst.ap.verify.measurements.profiling.TimingMetricTask,
# to keep MetricsControllerTask from temporarily depending on ap_verify.
# TODO: remove all code below this point in DM-16535


class TimingMetricConfig(MetricTask.ConfigClass):
    """Information that distinguishes one timing metric from another.
    """
    # It would be more user-friendly to identify the top-level task and call
    # CmdLineTask._getMetadataName, but doing so bypasses the public API and
    # requires reconstruction of the full task just in case the dataset is
    # config-dependent.
    metadataDataset = pexConfig.Field(
        dtype=str,
        doc="The dataset type of the timed top-level task's metadata, "
            "such as 'processCcd_metadata'.")
    target = pexConfig.Field(
        dtype=str,
        doc="The method to time, optionally prefixed by one or more tasks "
            "in the format of `lsst.pipe.base.Task.getFullMetadata()`. "
            "All matching methods will be counted.")
    metric = pexConfig.Field(
        dtype=str,
        doc="The fully qualified name of the metric to contain the "
            "timing information.")


class TimingMetricTask(MetricTask):
    """A Task that measures a timing metric using metadata produced by the
    `lsst.pipe.base.timeMethod` decorator.

    Parameters
    ----------
    args
    kwargs
        Constructor parameters are the same as for
        `lsst.verify.compatibility.MetricTask`.
    """

    ConfigClass = TimingMetricConfig
    _DefaultName = "timingMetric"

    @classmethod
    def _getInputMetadataKeyRoot(cls, config):
        """A search string for the metadata.

        The string must contain the name of the target method, optionally
        prefixed by one or more tasks in the format of
        `lsst.pipe.base.Task.getFullMetadata()`. It should be as short as
        possible to avoid making assumptions about what subtasks are
        configured. However, if multiple tasks and methods match the string,
        they will be assumed to all be relevant to the metric.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this task.

        Returns
        -------
        keyRoot : `str`
            A string identifying the class(es) and method(s) for this task.
        """
        return config.target

    @staticmethod
    def _searchMetadataKeys(metadata, keyFragment):
        """Metadata search for partial keys.

        Parameters
        ----------
        metadata : `lsst.daf.base.PropertySet`
            A metadata object with task-qualified keys as returned by
            `lsst.pipe.base.Task.getFullMetadata()`.
        keyFragment : `str`
            A substring for a full metadata key.

        Returns
        -------
        keys : `set` of `str`
            All keys in ``metadata`` that have ``keyFragment`` as a substring.
        """
        keys = metadata.paramNames(topLevelOnly=False)
        return {key for key in keys if keyFragment in key}

    def run(self, metadata):
        """Compute a wall-clock measurement from metadata provided by
        `lsst.pipe.base.timeMethod`.

        The method shall return no metric if any element of ``metadata`` is
        ``None``, on the grounds that if a task run was aborted without writing
        metadata, then any timing measurement wouldn't be comparable to other
        results anyway. It will also return no metric if no timing information
        was provided by any of the metadata.

        Parameters
        ----------
        metadata : iterable of `lsst.daf.base.PropertySet`
            A collection of metadata objects, one for each unit of science
            processing to be incorporated into this metric. Its elements
            may be `None` to represent missing data.

        Returns
        -------
        result : `lsst.pipe.base.Struct`
            A Struct containing at least the following component:

            - ``measurement``: the total running time of the target method
                               across all elements of ``metadata``
                               (`lsst.verify.Measurement` or `None`)

        Raises
        ------
        MetricComputationError
            Raised if any of the timing metadata are invalid.
        """
        keyBase = self._getInputMetadataKeyRoot(self.config)
        endBase = keyBase + "EndCpuTime"

        # some timings are indistinguishable from 0,
        # so don't test totalTime > 0
        timingFound = False
        totalTime = 0.0
        for singleMetadata in metadata:
            if singleMetadata is not None:
                matchingKeys = TimingMetricTask._searchMetadataKeys(
                    singleMetadata, endBase)
                for endKey in matchingKeys:
                    startKey = endKey.replace("EndCpuTime", "StartCpuTime")
                    try:
                        # startKey not guaranteed to exist
                        start, end = (singleMetadata.getAsDouble(key)
                                      for key in (startKey, endKey))
                    except (LookupError, TypeError) as e:
                        raise MetricComputationError("Invalid metadata") \
                            from e
                    totalTime += end - start
                    timingFound = True
            else:
                self.log.warn(
                    "At least one run did not write metadata; aborting.")
                return Struct(measurement=None)

        if timingFound:
            meas = Measurement(self.getOutputMetricName(self.config),
                               totalTime * u.second)
            meas.notes['estimator'] = 'pipe.base.timeMethod'
        else:
            self.log.info(
                "Nothing to do: no timing information for %s found.",
                keyBase)
            meas = None
        return Struct(measurement=meas)

    @classmethod
    def getInputDatasetTypes(cls, config):
        """Return input dataset types for this task.

        Parameters
        ----------
        config : ``cls.ConfigClass``
            Configuration for this task.

        Returns
        -------
        metadata : `dict` from `str` to `str`
            Dictionary from ``"metadata"`` to the dataset type of
            the target task's metadata.
        """
        return {'metadata': config.metadataDataset}

    @classmethod
    def getOutputMetricName(cls, config):
        return Name(config.metric)

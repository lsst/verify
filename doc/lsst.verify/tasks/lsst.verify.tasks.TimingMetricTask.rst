.. lsst-task-topic:: lsst.verify.tasks.commonMetrics.TimingMetricTask

################
TimingMetricTask
################

``TimingMetricTask`` creates a wall-clock timing `~lsst.verify.Measurement` based on data collected by @\ `~lsst.pipe.base.timeMethod`.
It reads the raw timing data from the top-level `~lsst.pipe.base.CmdLineTask`'s metadata, which is identified by the task configuration.

.. _lsst.verify.tasks.TimingMetricTask-summary:

Processing summary
==================

``TimingMetricTask`` searches the metadata for @\ `~lsst.pipe.base.timeMethod`-generated keys corresponding to the method of interest.
If it finds matching keys, it stores the elapsed time as a `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.TimingMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.commonMetrics.TimingMetricTask

.. _lsst.verify.tasks.TimingMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

:lsst-config-field:`~lsst.verify.tasks.commonMetrics.TimingMetricConfig.metadata`
    The metadata of the top-level command-line task (e.g., ``ProcessCcdTask``, ``ApPipeTask``) being instrumented.
    Because the metadata produced by each top-level task is a different Butler dataset type, this dataset **must** be explicitly configured when running ``TimingMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

.. _lsst.verify.tasks.TimingMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.commonMetrics.TimingMetricTask

.. _lsst.verify.tasks.TimingMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.commonMetrics.TimingMetricTask

.. _lsst.verify.tasks.TimingMetricTask-examples:

Examples
========

.. code-block:: py

   from lsst.verify.tasks import TimingMetricTask

   config = TimingMetricTask.ConfigClass()
   config.metadata.name = "apPipe_metadata"
   config.target = "apPipe:ccdProcessor.runDataRef"
   config.metric = "pipe_tasks.ProcessCcdTime"
   task = TimingMetricTask(config)

   # config.metadata provided for benefit of MetricsControllerTask/Pipeline
   # but since we've defined it we might as well use it
   metadata = butler.get(config.metadata.name)
   processCcdTime = task.run(metadata).measurement

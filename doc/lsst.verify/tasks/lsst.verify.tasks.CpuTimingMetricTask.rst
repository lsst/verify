.. lsst-task-topic:: lsst.verify.tasks.commonMetrics.CpuTimingMetricTask

###################
CpuTimingMetricTask
###################

``CpuTimingMetricTask`` creates a CPU timing `~lsst.verify.Measurement` based on data collected by @\ `~lsst.utils.timer.timeMethod`.
It reads the raw timing data from the top-level `~lsst.pipe.base.PipelineTask`'s metadata, which is identified by the task configuration.

This task always returns a smaller value than :lsst-task:`lsst.verify.tasks.commonMetrics.TimingMetricTask`.
If it is *much* smaller, that may be a sign that the task is running inefficiently, since both metrics are normally run on task methods that don't perform I/O.

.. _lsst.verify.tasks.CpuTimingMetricTask-summary:

Processing summary
==================

``CpuTimingMetricTask`` searches the metadata for @\ `~lsst.utils.timer.timeMethod`-generated keys corresponding to the method of interest.
If it finds matching keys, it stores the elapsed time as a `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.CpuTimingMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.commonMetrics.CpuTimingMetricTask

.. _lsst.verify.tasks.CpuTimingMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

``metadata``
    The metadata of the top-level pipeline task (e.g., ``CharacterizeImageTask``, ``DiaPipeTask``) being instrumented.
    This connection is usually configured indirectly through the ``labelName`` template as ``"{labelName}_metadata"``.

Output datasets
---------------

``measurement``
    The value of the metric.
    The dataset type should not be configured directly, but should be set
    changing the ``package`` and ``metric`` template variables to the metric's
    namespace (package, by convention) and in-package name, respectively.
    Subclasses that only support one metric should set these variables
    automatically.

.. _lsst.verify.tasks.CpuTimingMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.commonMetrics.CpuTimingMetricTask

.. _lsst.verify.tasks.CpuTimingMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.commonMetrics.CpuTimingMetricTask

.. _lsst.verify.tasks.CpuTimingMetricTask-examples:

Examples
========

.. code-block:: py

   from lsst.verify.tasks import CpuTimingMetricTask

   config = CpuTimingMetricTask.ConfigClass()
   config.connections.labelName = "diaPipe"
   config.connections.package = "ap_association"
   cofig.connections.metric = "DiaForcedSourceCpuTime"
   config.target = "diaPipe:diaForcedSource.run"
   task = CpuTimingMetricTask(config=config)

   # config.connections provided for benefit of Pipeline
   # but since we've defined it we might as well use it
   metadata = butler.get(config.connections.metadata)
   processCcdTime = task.run(metadata).measurement

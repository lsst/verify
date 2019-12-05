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

``metadata``
    The metadata of the top-level command-line task (e.g., ``ProcessCcdTask``, ``ApPipeTask``) being instrumented.
    Because the metadata produced by each top-level task is a different Butler dataset type, this dataset **must** be explicitly configured when running ``TimingMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

Output datasets
---------------

``measurement``
    The value of the metric.
    The dataset type should not be configured directly, but should be set
    changing the ``package`` and ``metric`` template variables to the metric's
    namespace (package, by convention) and in-package name, respectively.
    Subclasses that only support one metric should set these variables
    automatically.

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
   config.connections.metadata = "apPipe_metadata"
   config.connections.package = "pipe_tasks"
   cofig.connections.metric = "ProcessCcdTime"
   config.target = "apPipe:ccdProcessor.runDataRef"
   task = TimingMetricTask(config=config)

   # config.connections provided for benefit of MetricsControllerTask/Pipeline
   # but since we've defined it we might as well use it
   metadata = butler.get(config.connections.metadata)
   processCcdTime = task.run(metadata).measurement

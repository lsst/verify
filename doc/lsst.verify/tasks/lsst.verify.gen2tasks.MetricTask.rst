.. lsst-task-topic:: lsst.verify.gen2tasks.MetricTask

.. currentmodule:: lsst.verify.gen2tasks

##################################
MetricTask (lsst.verify.gen2tasks)
##################################

``MetricTask`` is a base class for generating `lsst.verify.Measurement` given input data.
Each ``MetricTask`` class accepts specific type(s) of datasets and produces measurements for a specific metric or family of metrics.

While its API mirrors that of `~lsst.pipe.base.PipelineTask`, this version of ``MetricTask`` is designed to be used with the Gen 2 framework.

.. _lsst.verify.gen2tasks.MetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.gen2tasks.MetricTask

.. _lsst.verify.gen2tasks.MetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.gen2tasks.MetricTask

.. _lsst.verify.gen2tasks.MetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.gen2tasks.MetricTask

.. _lsst.verify.gen2tasks.MetricTask-indepth:

In Depth
========

.. _lsst.verify.gen2tasks.MetricTask-indepth-subclassing:

Subclassing
-----------

``MetricTask`` is primarily customized using the `~MetricTask.run` method.
Each subclass must also implement the `~MetricTask.getOutputMetricName` method.

The task config should use `lsst.pipe.base.PipelineTaskConnections` to identify input datasets as if it were a `~lsst.pipe.base.PipelineTask`.
Only the ``name`` and ``multiple`` fields are used in a Gen 2 context, but use of `~lsst.pipe.base.PipelineTaskConnections` is expected to simplify the transition to Gen 3.

.. _lsst.verify.gen2tasks.MetricTask-indepth-errors:

Error Handling
--------------

In general, a ``MetricTask`` may run in three cases:

#. the task can compute the metric without incident.
#. the task does not have the datasets required to compute the metric.
   This often happens if the user runs generic metric configurations on arbitrary pipelines, or if they make changes to the pipeline configuration that enable or disable processing steps.
   More rarely, it can happen when trying to compute diagnostic metrics on incomplete (i.e., failed) pipeline runs.
#. the task has the data it needs, but cannot compute the metric.
   This could be because the data are corrupted, because the selected algorithm fails, or because the metric is ill-defined given the data.

A ``MetricTask`` must distinguish between these cases so that `~lsst.verify.gen2tasks.MetricsControllerTask` and future calling frameworks can handle them appropriately.
A task for a metric that does not apply to a particular pipeline run (case 2) must return `None` in place of a `~lsst.verify.Measurement`.
A task that cannot give a valid result (case 3) must raise `~lsst.verify.tasks.MetricComputationError`.

In grey areas, developers should choose a ``MetricTask``'s behavior based on whether the root cause is closer to case 2 or case 3.
For example, :lsst-task:`~lsst.verify.tasks.commonMetrics.TimingMetricTask` accepts top-level task metadata as input, but returns `None` if it can't find metadata for the subtask it is supposed to time.
While the input dataset is available, the subtask metadata are most likely missing because the subtask was never run, making the situation equivalent to case 2.
On the other hand, metadata with nonsense values falls squarely under case 3.

.. _lsst.verify.gen2tasks.MetricTask-indepth-register:

Registration
------------

The most common way to run ``MetricTask`` is as plugins to :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask`.
Most ``MetricTask`` classes should use the `register` decorator to assign a plugin name.

Because of implementation limitations, each registered name may appear at most once in `MetricsControllerConfig`.
If you expect to need multiple instances of the same ``MetricTask`` class (typically when the same class can compute multiple metrics), it must have the `registerMultiple` decorator instead.

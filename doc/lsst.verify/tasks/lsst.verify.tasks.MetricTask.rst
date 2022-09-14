.. lsst-task-topic:: lsst.verify.tasks.MetricTask

.. currentmodule:: lsst.verify.tasks

##########
MetricTask
##########

``MetricTask`` is a base class for generating `lsst.verify.Measurement` given input data.
Each ``MetricTask`` class accepts specific type(s) of datasets and produces measurements for a specific metric or family of metrics.

``MetricTask`` is a `~lsst.pipe.base.PipelineTask` and can be executed as part of pipelines.

.. _lsst.verify.tasks.MetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.MetricTask

.. _lsst.verify.tasks.MetricTask-butler:

Butler datasets
===============

Output datasets
---------------

``measurement``
    The value of the metric.
    The dataset type should not be configured directly, but should be set
    changing the ``package`` and ``metric`` template variables to the metric's
    namespace (package, by convention) and in-package name, respectively.
    ``MetricTask`` subclasses that only support one metric should set these
    variables automatically.

.. _lsst.verify.tasks.MetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.MetricTask

.. _lsst.verify.tasks.MetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.MetricTask

.. _lsst.verify.tasks.MetricTask-indepth:

In Depth
========

.. _lsst.verify.tasks.MetricTask-indepth-subclassing:

Subclassing
-----------

``MetricTask`` is primarily customized using the `~MetricTask.run` method.

The task config should use `lsst.pipe.base.PipelineTaskConnections` to identify input datasets; ``MetricConfig`` handles the output dataset.

.. _lsst.verify.tasks.MetricTask-indepth-errors:

Error Handling
--------------

In general, a ``MetricTask`` may run in three cases:

#. the task can compute the metric without incident.
#. the task does not have the data required to compute the metric.
   This can happen with metadata- or table-based metrics if the user runs generic metric configurations on arbitrary pipelines, or if they make changes to the pipeline configuration that enable or disable processing steps.
   Middleware automatically handles the case where an entire dataset is missing.
#. the task has the data it needs, but cannot compute the metric.
   This could be because the data are corrupted, because the selected algorithm fails, or because the metric is ill-defined given the data.

A ``MetricTask`` must distinguish between these cases so that calling frameworks can handle them appropriately.
A task for a metric that does not apply to a particular pipeline run (case 2) must either raise `~lsst.pipe.base.NoWorkFound` or return `None`; it must not return a dummy value or raise a different exception.
A task that cannot give a valid result (case 3) must raise `~lsst.verify.tasks.MetricComputationError`.

In grey areas, developers should choose a ``MetricTask``'s behavior based on whether the root cause is closer to case 2 or case 3.
For example, :lsst-task:`~lsst.verify.tasks.commonMetrics.TimingMetricTask` accepts top-level task metadata as input, but returns `None` if it can't find metadata for the subtask it is supposed to time.
The subtask metadata are most likely missing because the subtask was never run, making the situation equivalent to case 2.
On the other hand, metadata with nonsense values falls squarely under case 3.

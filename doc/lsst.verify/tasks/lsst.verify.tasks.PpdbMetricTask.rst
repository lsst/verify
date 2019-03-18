.. lsst-task-topic:: lsst.verify.tasks.ppdbMetricTask.PpdbMetricTask

##############
PpdbMetricTask
##############

``PpdbMetricTask`` is a base class for generating `~lsst.verify.Measurement`\ s from a prompt products database.
The class handles loading an appropriately configured database, while subclasses are responsible for creating the `~lsst.verify.Measurement` using the database API.

``PpdbMetricTask`` is currently a subclass of `lsst.verify.gen2tasks.MetricTask`.
It is expected that ``PpdbMetricTask`` can be migrated to the Gen 3 framework without affecting its subclasses.

.. _lsst.verify.tasks.PpdbMetricTask-summary:

Processing summary
==================

``PpdbMetricTask`` runs this sequence of operations:

#. Load the dataset indicated by :lsst-config-field:`~lsst.verify.tasks.ppdbMetricTask.PpdbMetricConfig.dbInfo` (default: the top-level science task's config).
#. Generate a `~lsst.dax.ppdb.Ppdb` object by calling the :lsst-config-field:`~lsst.verify.tasks.ppdbMetricTask.PpdbMetricConfig.dbLoader` subtask (default: :lsst-task:`~lsst.verify.tasks.ppdbMetricTask.ConfigPpdbLoader`).
#. Process the database by passing it to the customizable `~lsst.verify.tasks.ppdbMetricTask.PpdbMetricTask.makeMeasurement` method, and return the `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.PpdbMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.PpdbMetricTask

.. _lsst.verify.tasks.PpdbMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

:lsst-config-field:`~lsst.verify.tasks.ppdbMetricTask.PpdbMetricConfig.dbInfo`
    The Butler dataset from which the database connection can be initialized.
    The type must match the input required by the :lsst-config-field:`~lsst.verify.tasks.ppdbMetricTask.PpdbMetricConfig.dbLoader` subtask (default: the top-level science task's config).
    If the input is a config, its name **must** be explicitly configured when running ``PpdbMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

.. _lsst.verify.tasks.PpdbMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.PpdbMetricTask

.. _lsst.verify.tasks.PpdbMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.PpdbMetricTask

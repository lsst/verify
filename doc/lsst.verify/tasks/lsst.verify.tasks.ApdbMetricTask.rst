.. lsst-task-topic:: lsst.verify.tasks.apdbMetricTask.ApdbMetricTask

##############
ApdbMetricTask
##############

``ApdbMetricTask`` is a base class for generating `~lsst.verify.Measurement`\ s from an Alert Production Database.
The class handles loading an appropriately configured database, while subclasses are responsible for creating the `~lsst.verify.Measurement` using the database API.

``ApdbMetricTask`` is currently a subclass of `lsst.verify.tasks.MetricTask`.
It is expected that ``ApdbMetricTask`` can be migrated to the Gen 3 framework without affecting its subclasses.

.. _lsst.verify.tasks.ApdbMetricTask-summary:

Processing summary
==================

``ApdbMetricTask`` runs this sequence of operations:

#. Load the dataset indicated by :lsst-config-field:`~lsst.verify.tasks.apdbMetricTask.ApdbMetricConfig.dbInfo` (default: one or more ``apdb_marker`` datasets).
#. Generate an `~lsst.dax.apdb.Apdb` object by calling the :lsst-config-field:`~lsst.verify.tasks.apdbMetricTask.ApdbMetricConfig.dbLoader` subtask (default: :lsst-task:`~lsst.verify.tasks.apdbMetricTask.DirectApdbLoader`).
#. Process the database by passing it to the customizable `~lsst.verify.tasks.apdbMetricTask.ApdbMetricTask.makeMeasurement` method, and return the `~lsst.verify.Measurement`.

.. _lsst.verify.tasks.ApdbMetricTask-api:

Python API summary
==================

.. lsst-task-api-summary:: lsst.verify.tasks.ApdbMetricTask

.. _lsst.verify.tasks.ApdbMetricTask-butler:

Butler datasets
===============

Input datasets
--------------

:lsst-config-field:`~lsst.verify.tasks.apdbMetricTask.ApdbMetricConfig.dbInfo`
    The Butler dataset from which the database connection can be initialized.
    The type must match the input required by the :lsst-config-field:`~lsst.verify.tasks.apdbMetricTask.ApdbMetricConfig.dbLoader` subtask (default: ``apdb_marker``).
    If the input is a task config, its name **must** be explicitly configured when running ``ApdbMetricTask`` or a :lsst-task:`~lsst.verify.gen2tasks.MetricsControllerTask` that contains it.

.. _lsst.verify.tasks.ApdbMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.ApdbMetricTask

.. _lsst.verify.tasks.ApdbMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.ApdbMetricTask

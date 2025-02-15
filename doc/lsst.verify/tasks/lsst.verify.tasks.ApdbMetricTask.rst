.. lsst-task-topic:: lsst.verify.tasks.apdbMetricTask.ApdbMetricTask

##############
ApdbMetricTask
##############

``ApdbMetricTask`` is a base class for generating `~lsst.verify.Measurement`\ s from an Alert Production Database.
The class handles loading an appropriately configured database, while subclasses are responsible for creating the `~lsst.verify.Measurement` using the database API.

.. _lsst.verify.tasks.ApdbMetricTask-summary:

Processing summary
==================

``ApdbMetricTask`` runs this sequence of operations:

#. Generate an `~lsst.dax.apdb.Apdb` object from the config in :lsst-config-field:`~lsst.verify.tasks.apdbMetricTask.ApdbMetricConfig.apdb_config_url`.
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

``dbInfo``
    A Butler dataset whose presence guarantees the APDB has been updated.
    The dataset itself is never used.

Output datasets
---------------

``measurement``
    The value of the metric.
    The dataset type should not be configured directly, but should be set
    changing the ``package`` and ``metric`` template variables to the metric's
    namespace (package, by convention) and in-package name, respectively.
    Subclasses that only support one metric should set these variables
    automatically.

.. _lsst.verify.tasks.ApdbMetricTask-subtasks:

Retargetable subtasks
=====================

.. lsst-task-config-subtasks:: lsst.verify.tasks.ApdbMetricTask

.. _lsst.verify.tasks.ApdbMetricTask-configs:

Configuration fields
====================

.. lsst-task-config-fields:: lsst.verify.tasks.ApdbMetricTask

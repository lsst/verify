.. _lsst.verify.inspect_job:

#########################################
Reviewing Job objects with inspect_job.py
#########################################

`lsst.verify.Job` provides a rich interface for examining verification jobs, including pass/fail notifications for specifications (see `SQR-019`_).
However, this interface is often too heavyweight for debugging purposes.
:command:`inspect_job.py` is a command-line tool that lets the developer quickly see what information is being stored in a `~lsst.verify.Job` without performing additional analysis.

.. _SQR-019: https://sqr-019.lsst.io

Usage
=====

:command:`inspect_job.py` takes a list of :file:`.json` files, and no other arguments.
Operating system wildcards can be used.
For example:

.. prompt:: bash

   inspect_job.py package*.verify.json global.verify.json

Output
======

:command:`inspect_job.py` prints a report for each file passed to it.

The report starts with the job-level metadata in the file, formatted as one key-value pair per line.
Unlike `lsst.verify.Job.meta`, this does not include metadata associated with individual measurements.
Presenting job and measurement metadata separately makes it easier for developers to see what metadata are added at which level.

The report then lists all the measurements in the file, formatted as one pair of metric and value per line.
If there are metadata associated with a measurement, they are listed after the value.

:command:`inspect_job.py` does *not* report specifications, which are usually irrelevant to the code that creates measurements or jobs.
It also does not report metrics that don't have a corresponding measurement, as the list could be cluttered with many metrics that don't apply to the task being instrumented.

An example report looks like:

.. code-block:: none

   Common metadata:
                                       ccdnum = 42
                                        visit = 411657
                                       object = Blind15A_26
                                         date = 2015-02-19
                                   instrument = DECAM
                                       filter = g

   Measurements:
                      ip_diffim.numSciSources =  1326.0 ct
         ip_diffim.fracDiaSourcesToSciSources =     0.0385
   ap_association.totalUnassociatedDiaObjects =   540.0 ct
                           ap_pipe.ApPipeTime =  63.1475 s ({'estimator': 'pipe.base.timeMethod'})
                    pipe_tasks.ProcessCcdTime =  24.3298 s ({'estimator': 'pipe.base.timeMethod'})
                               ip_isr.IsrTime =   0.9623 s ({'estimator': 'pipe.base.timeMethod'})
             pipe_tasks.CharacterizeImageTime =   7.5473 s ({'estimator': 'pipe.base.timeMethod'})
                     pipe_tasks.CalibrateTime =  11.0519 s ({'estimator': 'pipe.base.timeMethod'})
               pipe_tasks.ImageDifferenceTime =  37.5217 s ({'estimator': 'pipe.base.timeMethod'})
          meas_algorithms.SourceDetectionTime =   1.0205 s ({'estimator': 'pipe.base.timeMethod'})
                      ip_diffim.DipoleFitTime =   1.9112 s ({'estimator': 'pipe.base.timeMethod'})
               ap_association.AssociationTime =   0.6594 s ({'estimator': 'pipe.base.timeMethod'})
              ap_association.numNewDiaObjects =    51.0 ct
         ap_association.fracUpdatedDiaObjects =        0.0
     ap_association.numUnassociatedDiaObjects =     0.0 ct


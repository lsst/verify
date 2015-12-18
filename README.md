A set of utilities to run the processCcd task on some CFHT data
and validate the astrometry of the results.

Pre-requisites: install and declare the following
1. pipe_tasks from the LSST DM stack (note that pipe_tasks is included with lsst_apps, which is the usual thing to install)
2. obs_cfht from https://github.com/lsst/obs_cfht (this package is not included with lsst_apps); declare this with tag "current"

Locate and install the selected input data in `/lsst8/boutigny/valid_cfht/rawDownload` and the custom astrometry_net_data file in `/lsst8/boutigny/valid_cfht/astrometry_net_data`.

To setup for a run:
```
setup pipe_tasks
setup display_ds9 -k
setup obs_cfht -k
```
If you did not declare obs_cfht current then also specify the version name you used

The following installs the specialied astrometry_net_data directory that contains only the SDSS catalogs for the test data fields of CFHT data.
```
setup -r astrometry_net_data -j
```

Run the measurement algorithm processing and astrometry test with
```
sh run_test.sh
```

While `run_test.sh` does everything, here is some exampls of running the processing/measurement steps individually:

1. To process all CCDs with the new (now default) AstrometryTask use newAstrometryConfig.py:
```
processCcd.py input @run.list --configfile newAstrometryConfig.py --clobber-config -j 6 --output junk
```

2. To process all CCDs with the old ANetAstrometryTask:
```
processCcd.py input @run.list --configfile anetAstrometryConfig.py --clobber-config -j 6 --output <outputPath>
./valid_cfht.py <outputPath>
```

3. To process one CCD with the new AstrometryTask:
```
processCcd.py input  --id visit=850587 ccd=21 --configfile newAstrometryConfig.py --clobber-config --output junk
```

4. Or process one CCD with the ANetAstrometryTask:  
```
processCcd.py input --id visit=850587 ccd=21 --configfile anetAstrometryConfig.py --clobber-config --output junk
```

Files :
-------
* `run_test.sh`      : Run initialization, ingest, measurement, and astrometry validation.
* `valid_cfht.py`    : run some analysis on the output data produced by processCcd.py
* `newAstrometryConfig.py`  : configuration for running processCcd with the new AstrometryTask
* `anetAstrometryConfig.py` : configuration for running processCcd ANetAstrometryTask
* `run.list`         : list of vistits / ccd to be processed by processCcd

A set of utilities to run the processCcd task on some 
CFHT data and DECam data
and validate the astrometry of the results.

Pre-requisites: install and declare the following
1. `pipe_tasks` from the LSST DM stack (note that pipe_tasks is included with lsst_apps, which is the usual thing to install)
2. `obs_decam` from https://github.com/lsst/obs_decam 
3. `obs_cfht` from https://github.com/lsst/obs_cfht 
4. `validation_data_cfht` from https://github.com/lsst/validation_data_cfht
5. `validation_data_decam` from https://github.com/lsst/validation_data_decam

The `obs_decam` and `obs_cfht` products are also buildable by the standard LSST DM stack tools: `lsstsw` or `eups distrib`.  But they (intentionally) aren't in the dependency tree of `lsst_apps`.  If you have a stack already installed with `lsst_apps`, you can install `obs_decam` and `obs_cfht` in the same manner.  E.g.,

```
eups distrib obs_decam obs_cfht
```

XOR

```
rebuild obs_decam obs_cfht
```

------
To setup for a run with CFHT:
```
setup obs_cfht 
setup validation_data_cfht
```
If you did not declare obs_cfht and validation_data_cfht current then also specify the version name you used

validation_data_cfht contains both the test CFHT data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
sh runCfhtTest.sh
```

------
To setup for a run with DECam:
```
setup obs_decam
setup validation_data_decam
```
If you did not declare obs_decam and validation_data_decam current then also specify the version name you used

validation_data_decam contains both the test DECam data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
sh runDecamTest.sh
```


The last line of the output will give the median astrometric scatter (in milliarcseconds) for stars with mag < 21.

------
While `run_test.sh` does everything, here is some examples of running the processing/measurement steps individually:

First make sure the astrometry.net environment variable is pointed to the right place for this validation set:

```
export ASTROMETRY_NET_DATA_DIR=${VALIDATION_DATA_CFHT_DIR}/astrometry_net_data
```

1. To process all CCDs with the new (now default) AstrometryTask use newAstrometryConfig.py:
```
processCcd.py CFHT/input @runCfht.list --configfile newAstrometryConfig.py --clobber-config -j 6 --output junk
```

2. To process all CCDs with the old ANetAstrometryTask:
```
processCcd.py CFHT/input @runCfht.list --configfile anetAstrometryConfig.py --clobber-config -j 6 --output <outputPath>
./valid_cfht.py <outputPath>
```

3. To process one CCD with the new AstrometryTask:
```
processCcd.py CFHT/input  --id visit=850587 ccd=21 --configfile newAstrometryConfig.py --clobber-config --output junk
```

4. Or process one CCD with the ANetAstrometryTask:  
```
processCcd.py CFHT/input --id visit=850587 ccd=21 --configfile anetAstrometryConfig.py --clobber-config --output junk
```

Files :
-------
* `runCfhtTest.sh`  : CFHT Run initialization, ingest, measurement, and astrometry validation.
* `runDecamTest.sh` : DECam Run initialization, ingest, measurement, and astrometry validation.
* `validCfht.py`    : CFHT run some analysis on the output data produced by processCcd.py
* `validDecam.py`   : DECam run some analysis on the output data produced by processCcd.py
* `runCfht.list`    : CRHT list of vistits / ccd to be processed by processCcd
* `runDecam.list`   : DECam list of vistits / ccd to be processed by processCcd
* `newAstrometryConfig.py`  : configuration for running processCcd with the new AstrometryTask
* `anetAstrometryConfig.py` : configuration for running processCcd ANetAstrometryTask
* 'README.md` : THIS FILE.  Guide and examples.

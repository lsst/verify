A set of utilities to run the processCcd task on some 
CFHT data and DECam data
and validate the astrometric and photometric repeatability of the results.

Pre-requisites: install and declare the following

1. `pipe_base` from the LSST DM stack (note that `pipe_base` is included with `lsst_apps`, which is the usual thing to install)
2. `obs_decam` from https://github.com/lsst/obs_decam
3. `obs_cfht` from https://github.com/lsst/obs_cfht
4. `validation_data_cfht` from https://github.com/lsst/validation_data_cfht
5. `validation_data_decam` from https://github.com/lsst/validation_data_decam

The `obs_decam`, `obs_cfht`, `validation_data_cfht`, `validation_data_decam`, `validate_drp` products are also buildable by the standard LSST DM stack tools: `lsstsw` or `eups distrib`.  But they (intentionally) aren't in the dependency tree of `lsst_apps`.  If you have a stack already installed with `lsst_apps`, you can install these in the same manner.  E.g.,

```
eups distrib install obs_decam obs_cfht validation_data_decam validation_data_cfht validate_drp
```

XOR

```
rebuild -u obs_decam obs_cfht validation_data_decam validation_data_cfht validate_drp
```

------
To setup for a run with CFHT:
```
setup obs_cfht 
setup validation_data_cfht
setup validate_drp
```
As usual, if any of these packages are not declared current you will also need to specify a version or tag.

`validation_data_cfht` contains both the test CFHT data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
$VALIDATE_DRP_DIR/examples/runCfhtTest.sh
```
This will create a repository in your current working directory called CFHT.

The last line of the output will give the median astrometric scatter (in milliarcseconds) for stars with mag < 21.

------
To setup for a run with DECam:
```
setup obs_decam
setup validation_data_decam
setup validate_drp
```
As usual, if any of these packages are not declared current you will also need to specify a version or tag.

`validation_data_decam` contains both the test DECam data and selected SDSS reference catalogs in astrometry.net format.

Run the measurement algorithm processing and astrometry test with
```
$VALIDATE_DRP_DIR/examples/runDecamTest.sh
```
This will create a repository in your current working directory called DECam.

The last line of the output will give the median astrometric scatter (in milliarcseconds) for stars with mag < 21.

------
There are also "Quick" versions to run one CCD for quick debugging and verification that things are running properly: `examples/runCfhtQuickTest.sh` and `examples/runDecamQuickTest.sh`.


------
While `examples/runCfhtTest.sh` and `examples/runDecamTest.sh` respectively do all of the processing and validation analysis, below are some examples of running the processing/measurement steps individually.  While these examples are from  the CFHT validation example, analogous commands would work for DECam.

1. Make sure the astrometry.net environment variable is pointed to the right place for this validation set:
    ```
    export ASTROMETRY_NET_DATA_DIR=${VALIDATION_DATA_CFHT_DIR}/astrometry_net_data
    ```

2. Ingest the files into the repository
    ```
    mkdir -p CFHT/input
    ingestImages.py CFHT/input "${VALIDATION_DATA_CFHT_DIR}"/raw/*.fz --mode link
    ```

3. Create the `runCfht.list` file from the YAML configuration file
    ```
    makeRunList.py "${VALIDATE_DRP_DIR}"/examples/runCfht.yaml > "${VALIDATE_DRP_DIR}"/examples/runCfht.list
    ```

Once these basic steps are completed, then you can run any of the following:

* To process all CCDs with the standard AstrometryTask and 6 threads use newAstrometryConfig.py:
    ```
    processCcd.py CFHT/input @examples/runCfht.list --configfile config/newAstrometryConfig.py --clobber-config -j 6 --output CFHT/output
    ```

* To process all CCDs with the old ANetAstrometryTask and 6 threads:
    ```
    processCcd.py CFHT/input @examples/runCfht.list --configfile config/anetAstrometryConfig.py --clobber-config -j 6 --output CFHT/output
    validateDrp.py CFHT/output examples/runCfht.yaml
    ```

* To process one CCD with the new AstrometryTask:
    ```
    processCcd.py CFHT/input  --id visit=850587 ccd=21 --configfile config/newAstrometryConfig.py --clobber-config --output tempout
    ```

* Or process one CCD with the ANetAstrometryTask:
    ```
    processCcd.py CFHT/input --id visit=850587 ccd=21 --configfile config/anetAstrometryConfig.py --clobber-config --output tempout
    ```

* Run the validation test
    ```
    validateDrp.py CFHT/output examples/runCfht.yaml
    ```

Note that the example validation test selects several of the CCDs and will fail if you just pass it a repository with 1 visit or just 1 CCD.

Files of Interest:
------------------
* `examples/runCfhtTest.sh`  : CFHT Run initialization, ingest, measurement, and astrometry validation.
* `examples/runDecamTest.sh` : DECam Run initialization, ingest, measurement, and astrometry validation.
* `examples/runCfht.list`    : CRHT list of vistits / ccd to be processed by processCcd
* `examples/runDecam.list`   : DECam list of vistits / ccd to be processed by processCcd
* `examples/runCfht.yaml`   : CFHT YAML file with visits, ccd, paramaters for validateDrp.
* `examples/runDecam.yaml`   : DECam YAML file with visits, ccd, paramaters for validateDrp.
* `examples/runDecamCosmos.yaml`   : DECam COSMOS YAML file with visits, ccd, paramaters for validateDrp.
* `config/newAstrometryConfig.py`  : configuration for running processCcd with the new AstrometryTask
* `config/anetAstrometryConfig.py` : configuration for running processCcd ANetAstrometryTask
* `bin.src/validateDrp.py`   : Analyze output data produced by processCcd.py
* `python/lsst/validate/drp/srdSpec.py` : class to contain the SRD specifications
* `python/lsst/validate/drp/calcSrd.py` : calculate metrics defined by the LSST SRC.
* `python/lsst/validate/drp/plot.py` : plotting routines
* `python/lsst/validate/drp/check.py` : coordination and calculation routines.
* `python/lsst/validate/drp/print.py` : printing routines
* `python/lsst/validate/drp/base.py` : base routines for the module
* `python/lsst/validate/drp/util.py` : utility routines
* `README.md` : THIS FILE.  Guide and examples.

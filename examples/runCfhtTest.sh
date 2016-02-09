#!/bin/bash

print_error() {
    >&2 echo "$@"
}

PRODUCT_DIR=${VALIDATE_DRP_DIR}
# OS X El Capitan SIP swallows DYLD_LIBRARY_PATH so export the duplicate in LSST_LIBRARY_PATH
if [[ -z "$DYLD_LIBRARY_PATH" ]]; then
    export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
fi

WORKSPACE=CFHT
if [ -d ${WORKSPACE} ]; then
   rm -rf ${WORKSPACE}
fi

# cleanup and create directories
echo "Ingesting Raw data"
INPUT=${WORKSPACE}/input
mkdir -p $INPUT
OUTPUT=${WORKSPACE}/output
mkdir -p $OUTPUT

echo "lsst.obs.cfht.MegacamMapper" > ${INPUT}/_mapper

# ingest CFHT raw data
RAWDATA=${VALIDATION_DATA_CFHT_DIR}
ingestImages.py ${INPUT} "${RAWDATA}"/raw/*.fz --mode link

# Set up astrometry 
export ASTROMETRY_NET_DATA_DIR=${VALIDATION_DATA_CFHT_DIR}/astrometry_net_data

# Create calexps and src
echo "running processCcd"
MACH=$(uname -s)
if [ "$MACH" == Darwin ]; then
    NUMPROC=$(sysctl -a | grep machdep.cpu | grep core_count | cut -d ' ' -f 2)
else
    NUMPROC=$(grep -c processor /proc/cpuinfo)
fi
NUMPROC=$((NUMPROC<8?NUMPROC:8))

# Extract desired dataIds runs from runCfht.yaml
CONFIGFILE="${PRODUCT_DIR}"/examples/runCfht.yaml 
RUNLIST="${PRODUCT_DIR}"/examples/runCfht.list
makeRunList.py "${CONFIGFILE}" > "${RUNLIST}"

processCcd.py "${INPUT}" --output "${OUTPUT}" \
    @"${RUNLIST}" \
    --logdest "${WORKSPACE}"/processCcd.log \
    --configfile "${PRODUCT_DIR}"/config/anetAstrometryConfig.py \
    -j $NUMPROC

# Run astrometry check on src
echo "validating"
validateDrp.py "${OUTPUT}" "${CONFIGFILE}"

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi

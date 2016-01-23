#!/bin/bash

print_error() {
    >&2 echo "$@"
}

PRODUCT_DIR=${VALIDATE_DRP_DIR}

WORKSPACE=CFHT
mkdir -p ${WORKSPACE}
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

processCcd.py ${INPUT} --output ${OUTPUT} \
    @"${PRODUCT_DIR}"/examples/runCfht.list \
    --logdest ${WORKSPACE}/processCcd.log \
    --configfile "${PRODUCT_DIR}"/config/anetAstrometryConfig.py \
    -j $NUMPROC

# Run astrometry check on src
echo "validating"
validateCfht.py ${OUTPUT}

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi



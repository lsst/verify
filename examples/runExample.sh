#!/bin/bash

print_error() {
    >&2 echo "$@"
}

CAMERA=$1
MAPPER=$2
VALIDATION_DATA=$3
CONFIG_FILE=$4

if [[ $# -gt 4 ]]
then
    INGEST=$5
    PROCESSCCD=$6
else
    INGEST=ingestImages.py
    PROCESSCCD=processCcd.py
fi


PRODUCT_DIR=${VALIDATE_DRP_DIR}
# OS X El Capitan SIP swallows DYLD_LIBRARY_PATH so export the duplicate in LSST_LIBRARY_PATH
if [[ -z "$DYLD_LIBRARY_PATH" ]]; then
    export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
fi

WORKSPACE=${CAMERA}
if [ -d "${WORKSPACE}" ]; then
   rm -rf "${WORKSPACE}"
fi

# cleanup and create directories
echo "Ingesting Raw data"
INPUT=${WORKSPACE}/input
mkdir -p "$INPUT"
OUTPUT=${WORKSPACE}/output
mkdir -p "$OUTPUT"

echo "$MAPPER" > "${INPUT}"/_mapper

# ingest raw data
RAWDATA=${VALIDATION_DATA}
${INGEST} "${INPUT}" "${RAWDATA}"/*.fz --mode link

# Set up astrometry 
export ASTROMETRY_NET_DATA_DIR="${VALIDATION_DATA}"/../astrometry_net_data

# Create calexps and src
echo "running processCcd"
MACH=$(uname -s)
if [ "$MACH" == Darwin ]; then
    NUMPROC=$(sysctl -n hw.logicalcpu)
else
    NUMPROC=$(grep -c processor /proc/cpuinfo)
fi
NUMPROC=$((NUMPROC<8?NUMPROC:8))

# Extract desired dataIds runs from YAML config file
YAMLCONFIG="${PRODUCT_DIR}"/examples/${CAMERA}.yaml 
RUNLIST="${PRODUCT_DIR}"/examples/${CAMERA}.list
makeRunList.py "${YAMLCONFIG}" > "${RUNLIST}"

${PROCESSCCD} "${INPUT}" --output "${OUTPUT}" \
    @"${RUNLIST}" \
    --logdest "${WORKSPACE}"/processCcd.log \
    --configfile "${CONFIG_FILE}" \
    -j $NUMPROC

# Run astrometry check on src
echo "validating"
validateDrp.py "${OUTPUT}" "${YAMLCONFIG}"

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi

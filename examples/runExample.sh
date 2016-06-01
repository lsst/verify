#!/bin/bash

print_error() {
    >&2 echo "$@"
}

INGEST=ingestImages.py
PROCESSCCD=processCcd.py

usage() {
    print_error
    print_error "Usage: $0 [-cmvfip] [-h] [-- <options to validateDrp.py>]"
    print_error
    print_error "Specifc options:"
    print_error "   -c          camera"
    print_error "   -m          mapper"
    print_error "   -v          validation data"
    print_error "   -f          config file"
    print_error "   -i          ingest (${INGEST})"
    print_error "   -p          processccd (${PROCESSCCD})"
    print_error "   -h          show this message"
    exit 1
}

# thank OSX for not including getopt
while getopts "c:m:v:f:i:p:h" option; do
    case "$option" in
        c)  CAMERA="$OPTARG";;
        m)  MAPPER="$OPTARG";;
        v)  VALIDATION_DATA="$OPTARG";;
        f)  CONFIG_FILE="$OPTARG";;
        i)  INGEST="$OPTARG";;
        p)  PROCESSCCD="$OPTARG";;
        h)  usage;;
        *)  usage;;
    esac
done
shift $((OPTIND-1))

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
validateDrp.py "${OUTPUT}" --configFile "${YAMLCONFIG}" "$@"

if [ $? != 0 ]; then
   print_error "Validation failed"
   exit 99
fi

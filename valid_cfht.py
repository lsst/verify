#!/usr/bin/env python
import math
import os.path
import sys

import matplotlib.pylab as plt
import numpy as np

import lsst.daf.persistence as dafPersist
import lsst.pipe.base as pipeBase
import lsst.afw.table as afwTable
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage

def angDist(ra_1, dec_1, ra_2, dec_2) :
# Compute separation angle between 2 positions in the sky given by their (ra,dec)
    sindec_1 = math.sin(dec_1)
    cosdec_1 = math.cos(dec_1)
    sindec_2 = math.sin(dec_2)
    cosdec_2 = math.cos(dec_2)
    cosra_2_ra_1 = math.cos(ra_2-ra_1)
    sinra_2_ra_1 = math.sin(ra_2-ra_1)
    
    aux = (cosdec_1 * sindec_2) - (sindec_1 * cosdec_2 * cosra_2_ra_1)
    num = (cosdec_2 * cosdec_2 * sinra_2_ra_1 * sinra_2_ra_1) + aux*aux
    den = (sindec_1 * sindec_2) + (cosdec_1 * cosdec_2 * cosra_2_ra_1)
    
    return math.atan2(math.sqrt(num), den)

def loadData(repo, visits, ref, ccd, filter) :

    Flags = ["base_PixelFlags_flag_saturated", "base_PixelFlags_flag_cr", "base_PixelFlags_flag_interpolated",
             "base_PsfFlux_flag_edge"]

    #setup butler
    butler = dafPersist.Butler(repo)

    for indx, c in enumerate(ccd) :
        dataid = {'visit':ref, 'filter':filter, 'ccd':c}
        oldSrc = butler.get('src', dataid, immediate=True)
        print len(oldSrc), "sources in ccd :", c
        if indx == 0 :
            # retrieve the schema of the source catalog and extend it in order to add a field to record the ccd number
            oldSchema = oldSrc.getSchema()
            mapper = afwTable.SchemaMapper(oldSchema)
            mapper.addMinimalSchema(oldSchema)
            newSchema = mapper.getOutputSchema()
            newSchema.addField("ccd", type=int, doc="CCD number")
            
            #create the new extented source catalog 
            srcRef = afwTable.SourceCatalog(newSchema)
        
        # create temporary catalog
        tmpCat = afwTable.SourceCatalog(srcRef.table)
        tmpCat.extend(oldSrc, mapper=mapper)
        # fill in the ccd information in numpy mode in order to be efficient
        tmpCat['ccd'][:] = c
        # append the temporary catalog to the extended source catalog    
        srcRef.extend(tmpCat, deep=False)

    print len(srcRef), "Sources in reference visit :", ref

    mag = []
    dist = []
    for v in visits :
        if v == ref :
            continue
        for indx, c in enumerate(ccd) :
            dataid = {'visit':v, 'filter':filter, 'ccd':c}
            if indx == 0 :
                srcVis = butler.get('src', dataid, immediate=True)
            else :
                srcVis.extend(butler.get('src', dataid, immediate=True), False)
            print len(srcVis), "sources in ccd : ", c
        
        match = afwTable.matchRaDec(srcRef, srcVis, afwGeom.Angle(1./3600., afwGeom.degrees))
        matchNum = len(match)
        print "Visit :", v, matchNum, "matches found"

	schemaRef = srcRef.getSchema()
        schemaVis = srcVis.getSchema()
        extRefKey = schemaRef["base_ClassificationExtendedness_value"].asKey()
        extVisKey = schemaVis["base_ClassificationExtendedness_value"].asKey()
        flagKeysRef = []
        flagKeysVis = []
        for f in Flags :
            keyRef = schemaRef[f].asKey()
            flagKeysRef.append(keyRef)
            keyVis = schemaVis[f].asKey()
            flagKeysVis.append(keyVis)
        
        for m in match :
            mRef = m.first
            mVis = m.second
            
            for f in flagKeysRef :
                if mRef.get(f) :
                    continue
            for f in flagKeysVis :
            	if mVis.get(f) :
            	    continue
            
            # cleanup the reference sources in order to keep only decent star-like objects
            if mRef.get(extRefKey) >= 1.0 or mVis.get(extVisKey) >= 1.0 :
                continue
            
            ang = afwGeom.radToMas(m.distance)
            
            # retrieve the CCD corresponding to the reference source
            ccdRef = mRef.get('ccd')
            # retrieve the calibration object associated to the CCD
            did = {'visit':ref, 'filter':filter, 'ccd':ccdRef}
            md = butler.get("calexp_md", did, immediate=True)
            calib = afwImage.Calib(md)
            # compute magnitude
            refMag = calib.getMagnitude(mRef.get('base_PsfFlux_flux'))
            
                                        
            mag.append(refMag)
            dist.append(ang)

    return pipeBase.Struct(
        mag = mag,
        dist = dist,
        match = matchNum
    )

def check_astrometry(repo, mag, dist, match) :
    # Plot angular distance between matched sources from different exposures
    
    plt.rcParams['axes.linewidth'] = 2 
    plt.rcParams['mathtext.default'] = 'regular'
    
    fig, ax = plt.subplots(ncols=2, nrows=3, figsize=(18,22))
    ax[0][0].hist(dist, bins=80)
    ax[0][1].scatter(mag, dist, s=10, color='b')
    ax[0][0].set_xlim([0., 900.])
    ax[0][0].set_xlabel("Distance in mas", fontsize=20)
    ax[0][0].tick_params(labelsize=20)
    ax[0][0].set_title("Median : %.1f mas"%(np.median(dist)), fontsize=20, x=0.6, y=0.88)
    ax[0][1].set_xlabel("Magnitude", fontsize=20)
    ax[0][1].set_ylabel("Distance in mas", fontsize=20)
    ax[0][1].set_ylim([0., 900.])
    ax[0][1].tick_params(labelsize=20)
    ax[0][1].set_title("Number of matches : %d"%match, fontsize=20)

    ax[1][0].hist(dist,bins=150)
    ax[1][0].set_xlim([0.,400.])
    ax[1][1].scatter(mag, dist, s=10, color='b')
    ax[1][1].set_ylim([0.,400.])
    ax[1][0].set_xlabel("Distance in mas", fontsize=20)
    ax[1][1].set_xlabel("Magnitude", fontsize=20)
    ax[1][1].set_ylabel("Distance in mas", fontsize=20)
    ax[1][0].tick_params(labelsize=20)
    ax[1][1].tick_params(labelsize=20)

    print "Median value of the astrometric scatter - all magnitudes:", np.median(dist), "mas"

    idxs = np.where(np.asarray(mag) < 21)
    ax[2][0].hist(np.asarray(dist)[idxs], bins=100)
    ax[2][0].set_xlabel("Distance in mas - mag < 21", fontsize=20)
    ax[2][0].set_xlim([0,200])
    ax[2][0].set_title("Median (mag < 21) : %.1f mas"%(np.median(np.asarray(dist)[idxs])), fontsize=20, x=0.6, y=0.88)
    ax[2][1].scatter(np.asarray(mag)[idxs], np.asarray(dist)[idxs], s=10, color='b')
    ax[2][1].set_xlabel("Magnitude", fontsize=20)
    ax[2][1].set_ylabel("Distance in mas - mag < 21", fontsize=20)
    ax[2][1].set_ylim([0.,200.])
    ax[2][0].tick_params(labelsize=20)
    ax[2][1].tick_params(labelsize=20)
    
    plt.suptitle("Astrometry Check", fontsize=30)
    plotPath = os.path.join(repo, "valid_cfht.png")
    plt.savefig(plotPath, format="png")

    medianMag21 = np.median(np.asarray(dist)[idxs])
    print "Astrometric scatter (median) - mag < 21 :", medianMag21, "mas"

    return medianMag21
    
def main(repo):
    
    # List of visits to be considered
    visits = [849375, 850587]

    # Reference visit (the other viisits will be compared to this one
    ref = 849375

    # List of CCD to be considered (source calalogs will be concateneted)
    ccd = [12, 13, 14, 21, 22, 23]
    filter = 'r'
    
    # Reference values for the median astrometric scatter and the number of matches
    medianRef = 25
    matchRef = 5600
    
    struct = loadData(repo, visits, ref, ccd, filter)
    mag = struct.mag
    dist = struct.dist
    match = struct.match
    medianMag21 = check_astrometry(repo, mag, dist, match)

    if medianMag21 > medianRef :
	print "Median astrometric scatter %.1f mas is larger than reference : %.1f mas "%(medianMag21, medianRef)
	sys.exit(99)
    if match < matchRef :
    	print "Number of matched sources %d is too small (shoud be > %d)"%(match,matchRef)
    	sys.exit(99)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print """Usage: valid_cfht.py repo
where repo is the path to a repository containing the output of processCcd
"""
        sys.exit(1)
    repo = sys.argv[1]
    if not os.path.isdir(repo):
        print "Could not find repo %r" % (repo,)
        sys.exit(1)
    main(repo)

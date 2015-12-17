from lsst.meas.astrom import AstrometryTask
config.calibrate.astrometry.retarget(AstrometryTask)

config.calibrate.astrometry.wcsFitter.order = 3
config.calibrate.astrometry.matcher.maxMatchDistArcSec = 3.0

config.calibrate.repair.cosmicray.nCrPixelMax = 1000000
config.calibrate.photocal.fluxField = 'base_PsfFlux_flux'
config.calibrate.photocal.applyColorTerms = True
config.calibrate.photocal.photoCatName="e2v"
config.calibrate.photocal.magLimit = 20.0
config.calibrate.photocal.sigmaMax = 0.05  # default 0.25
config.calibrate.photocal.badFlags = ['base_PixelFlags_flag_edge', 'base_PixelFlags_flag_interpolated', 'base_PixelFlags_flag_saturated', 'base_PixelFlags_flag_crCenter']

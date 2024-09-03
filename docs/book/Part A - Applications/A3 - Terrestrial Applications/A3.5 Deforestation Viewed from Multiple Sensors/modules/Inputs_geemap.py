import ee 
import geemap

Map = geemap.Map()

# Fusion Near Real-time (Lite)
# Near real-time monitoring of forest disturbance by fusion of
# multi-sensor data.  @author Xiaojing Tang (xjtang@bu.edu).

# Input data functions.

# Load Landsat time series.

def func_cmm(region, period):

    def func_igk(img):
            return img.addBands(
                    srcImg = img.multiply(0.0000275).add(-0.2).multiply(10000),
                    names = img.bandNames(),
                    overwrite = True
                    )

    c2ToSR = func_igk





    


    def func_tzp(img):
            bands = ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']
            sr = c2ToSR(img.select(bands)) \
            .rename(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
            validQA = [21824, 21888]
            mask1 = img.select(['QA_PIXEL']) \
            .remap(validQA, ee.List.repeat(1, validQA.length), 0)
            mask2 = sr.reduce(ee.Reducer.min()).gt(0)
            mask3 = sr.reduce(ee.Reducer.max()).lt(10000)
            return sr.updateMask(mask1.And(mask2).And(mask3))

    maskL8 = func_tzp









    


    def func_ljm(img):
            bands = ['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7']
            sr = c2ToSR(img.select(bands)) \
            .rename(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
            validQA = [5440, 5504]
            mask1 = img.select('QA_PIXEL') \
            .remap(validQA, ee.List.repeat(1, validQA.length), 0)
            mask2 = sr.reduce(ee.Reducer.min()).gt(0)
            mask3 = sr.reduce(ee.Reducer.max()).lt(10000)
            return sr.updateMask(mask1.And(mask2).And(mask3))

    maskL7 = func_ljm









    

    collection7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
    .filterBounds(region) \
    .filterDate(period.get('start'), period.get('end')) \
    .map(maskL7)
    collection8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .filterBounds(region) \
    .filterDate(period.get('start'), period.get('end')) \
    .map(maskL8)
    return ee.ImageCollection(collection7.merge(collection8))

loadLandsatData = func_cmm









































































))
return ee.ImageCollection(masked)
}

# Load Sentinel-1 time series.

def func_llc(region, period):
    slopeLib = require('projects/gee-edu/book:Part A - Applications/A3 - Terrestrial Applications/A3.5 Deforestation Viewed from Multiple Sensors/modules/slope_correction_lib.js')


    def func_nij(img):
            st = img.get('system:time_start')
            geom = img.geometry()
            angle = img.select('angle')
            edge = img.select('VV').lt(-30.0)
            fmean = img.select('V.').add(30)
            fmean = fmean.focal_mean(3, 'circle')
            ratio = fmean.select('VH').divide(fmean.select('VV')).rename('ratio').multiply(30)
            return img.select().addBands(fmean).addBands(ratio).addBands(angle).set('timeStamp', st)

    spatialMean = func_nij








    

    S1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filterBounds(region).filterDate(period.get('start'), period.get('end')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .select(['V.','angle']).map(spatialMean) \
    .select(['VH','VV','ratio','angle'])
    passCount = ee.Dictionary(S1.aggregate_histogram('orbitProperties_pass'))
    passValues = passCount.values().sort().reverse()
    higherCount = passValues.get(0)
    maxOrbitalPass = passCount.keys().get(passCount.values().indexOf(higherCount))
    S1Filtered = S1.filter(ee.Filter.eq('orbitProperties_pass', maxOrbitalPass))
    S1Corrected = slopeLib.slope_correction(S1Filtered)

    def func_xoo(img):
            st = img.get('timeStamp')
            return img.addBands(img.select('VH').divide(img.select('VV')) \
            .rename('ratio').multiply(10)).set('system:time_start', st)









































Map
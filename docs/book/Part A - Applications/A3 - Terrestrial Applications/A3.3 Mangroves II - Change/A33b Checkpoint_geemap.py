import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      A3.3 Mangroves II - Change Mapping
#  Checkpoint:   A33b
#  Authors:      Celio de Sousa, David Lagomasino, and Lola Fatoyinbo
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# STEP 1 - ADD THE MAPS
areaOfstudy = ee.FeatureCollection(
'projects/gee-book/assets/A3-3/Border5km')
mangrove2000 = ee.Image(
'projects/gee-book/assets/A3-3/MangroveGuinea2000_v2')
mangrove2020 = ee.Image(
'projects/gee-book/assets/A3-3/MangroveGuinea2020_v2')

Map.setCenter(-13.6007, 9.6295, 10)
# Sets the map center to Conakry, Guinea
Map.addLayer(areaOfstudy, {}, 'Area of Study')
Map.addLayer(mangrove2000, {
    'palette': '#16a596'
}, 'Mangrove Extent 2000')
Map.addLayer(mangrove2020, {
    'palette': '#9ad3bc'
}, 'Mangrove Extent 2020')

# STEP 2 -  MAP TO MAP CHANGE

mang2020 = mangrove2020.unmask(0)
mang2000 = mangrove2000.unmask(0)
change = mang2020.subtract(mang2000) \
.clip(areaOfstudy)

paletteCHANGE = [
'red', 
'white', 
'green', 
]

Map.addLayer(change, {
    'min': -1,
    'max': 1,
    'palette': paletteCHANGE
}, 'Changes 2000-2020')

# Calculate the area of each pixel
gain = change.eq(1)
loss = change.eq(-1)

gainArea = gain.multiply(ee.Image.pixelArea().divide(1000000))
lossArea = loss.multiply(ee.Image.pixelArea().divide(1000000))

# Sum all the areas
statsgain = gainArea.reduceRegion(
reducer = ee.Reducer.sum(),
scale = 30,
maxPixels = 1e14
)

statsloss = lossArea.reduceRegion(
reducer = ee.Reducer.sum(),
scale = 30,
maxPixels = 1e14
)

print(statsgain.get('classification'.getInfo())
'km² of new mangroves in 2020 in Guinea')
print(statsloss.get('classification'.getInfo())
'of mangrove was lost in 2020 in Guinea')

Map.addLayer(gain.selfMask(), {
    'palette': 'green'
}, 'Gains')
Map.addLayer(loss.selfMask(), {
    'palette': 'red'
}, 'Loss')

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------

# SECTION 2

# STEP 1 - SET THE BASELINE EXTENT AND BUFFER

buffer = 1000; 
extentBuffer = mangrove2000.focal_max(buffer, 'circle', 'meters')
Map.addLayer(mangrove2000, {
    'palette': '#000000'
}, 'Baseline', False)
Map.addLayer(extentBuffer, {
    'palette': '#0e49b5',
    'opacity': 0.3
}, 'Mangrove Buffer', False)

# STEP 2 - HARMONIZING LANDSAT 5/7/8 IMAGE COLLECTIONS

# 2.1 Temporal parameters
startYear = 1984
endyear = 2020
startDay = '01-01'
endDay = '12-31'

# 2.2 Harmonization function.
# Slopes and interceps were retrieved from Roy et. al (2016)

def func_lyo(oli):
    slopes = ee.Image.constant([0.9785, 0.9542, 0.9825,
    1.0073, 1.0171, 0.9949
    ])
    itcp = ee.Image.constant([-0.0095, -0.0016, -0.0022, -
    0.0021, -0.0030, 0.0029
    ])
    y = oli.select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7'], [
    'B1', 'B2', 'B3', 'B4', 'B5', 'B7'
    ]) \
    .resample('bicubic') \
    .subtract(itcp.multiply(10000)).divide(slopes) \
    .set('system:time_start', oli.get('system:time_start'))
    return y.toShort()

harmonizationRoy = func_lyo















# 2.3 Retrieve a particular sensor function
sensor) {
    srCollection = ee.ImageCollection('LANDSAT/' + sensor + \
    '/C01/T1_SR') \
    .filterDate(year + '-' + startDay, endYear + '-' + endDay)

    def func_qia(img):
            dat
if (sensor == 'LC08'):
                        dat = harmonizationRoy(img.unmask())
                     else {
                        dat = img.select(['B1', 'B2', 'B3', 'B4',
                        'B5', 'B7'
                        ]) \
                        .unmask() \
                        .resample('bicubic') \
                        .set('system:time_start', img.get(
                        'system:time_start'))
                    }
            # Cloud, cloud shadow and snow mask.
            qa = img.select('pixel_qa')
            mask = qa.bitwiseAnd(8).eq(0).And(
            qa.bitwiseAnd(16).eq(0)).And(
            qa.bitwiseAnd(32).eq(0))
            return dat.mask(mask) \
    .map(func_qia)



















    return srCollection
}

# 2.4 Combining the collections functio
endDay) {
    lt5 = getSRcollection(year, startDay, endYear, endDay,
    'LT05')
    le7 = getSRcollection(year, startDay, endYear, endDay,
    'LE07')
    lc8 = getSRcollection(year, startDay, endYear, endDay,
    'LC08')
    mergedCollection = ee.ImageCollection(le7.merge(lc8) \
    .merge(lt5))
    return mergedCollection
}

# 2.5 Calculating vegetation indices.

def func_atv(image):
    ndvi = image.normalizedDifference(['B4', 'B3']).rename(
    'NDVI')
    evi = image.expression(
    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
            'NIR': image.select('B4'),
            'RED': image.select('B3'),
            'BLUE': image.select('B1')
        }).rename('EVI')
    savi = image.expression(
    '((NIR - RED) / (NIR + RED + 0.5) * (0.5 + 1))', {
            'NIR': image.select('B4'),
            'RED': image.select('B3'),
            'BLUE': image.select('B1')
        }).rename('SAVI')
    ndmi = image.normalizedDifference(['B7', 'B2']).rename(
    'NDMI')
    ndwi = image.normalizedDifference(['B5', 'B4']).rename(
    'NDWI')
    mndwi = image.normalizedDifference(['B2', 'B5']).rename(
    'MNDWI')
    return image.addBands(ndvi) \
    .addBands(evi) \
    .addBands(savi) \
    .addBands(ndmi) \
    .addBands(ndwi) \
    .addBands(mndwi)

addIndices = func_atv




























# 2.6 Apply the indices function to the collection
collectionSR_wIndex = getCombinedSRcollection(startYear, startDay,
endyear, endDay).map(addIndices)
collectionL5L7L8 = collectionSR_wIndex.filterBounds(areaOfstudy)

# STEP 3 - VEGETATION INDEX ANOMALY

index = 'NDVI'
ref_start = '1984-01-01'; 
ref_end = '1999-12-31'; 

reference = collectionL5L7L8 \
.filterDate(ref_start, ref_end) \
.select(index) \
.sort('system:time_start', True)
print('Number of images in Reference Collection', reference.size().getInfo())

# 3.2 Compute the Mean value for the vegetation index
# (and other stats) for the reference period.
mean = reference.mean().mask(extentBuffer)
median = reference.median().mask(extentBuffer)
max = reference.max().mask(extentBuffer)
min = reference.min().mask(extentBuffer)

period_start = '2000-01-01'; 
period_end = '2020-12-31'

# 3.4 Anomaly calculation

def func_oop func_oop(image):
    return image.subtract(mean) \
    .set('system:time_start', image.get('system:time_start'))

anomalyfunc_oop




series = collectionL5L7L8.filterDate(period_start, period_end) \
.map(anomalyfunction)

# Sum the values of the series.
seriesSum = series.select(index).sum().mask(extentBuffer)
numImages = series.select(index).count().mask(extentBuffer)
anomaly = seriesSum.divide(numImages)

visAnon = {
    'min': -0.20,
    'max': 0.20,
    'palette': ['#481567FF', '#482677FF', '#453781FF', '#404788FF',
    '#39568CFF', '#33638DFF', '#2D708EFF', '#287D8EFF',
    '#238A8DFF',
    '#1F968BFF', '#20A387FF', '#29AF7FFF', '#3CBB75FF',
    '#55C667FF',
    '#73D055FF', '#95D840FF', '#B8DE29FF', '#DCE319FF',
    '#FDE725FF'
    ]
}
Map.addLayer(anomaly, visAnon, index + ' anomaly')

thresholdLoss = -0.05
lossfromndvi = anomaly.lte(thresholdLoss) \
.selfMask() \
.updateMask(
mangrove2000
); 

Map.addLayer(lossfromndvi, {
    'palette': ['orange']
}, 'Loss from Anomaly 00-20')

thresholdGain = 0.20
gainfromndvi = anomaly.gte(thresholdGain) \
.selfMask() \
.updateMask(
extentBuffer
); 

Map.addLayer(gainfromndvi, {
    'palette': ['blue']
}, 'Gain from Anomaly 00-20')

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------
Map
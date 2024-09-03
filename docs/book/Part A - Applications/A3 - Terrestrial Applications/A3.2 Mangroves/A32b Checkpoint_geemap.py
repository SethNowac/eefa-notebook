import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      A3.2 Mangroves
#  Checkpoint:   A32b
#  Author:       Aurélie Shapiro
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Create an ee.Geometry.
aoi = ee.Geometry.Polygon([
[
[88.3, 22.61],
[90, 22.61],
[90, 21.47],
[88.3, 21.47]
]
])

# Locate a coordinate in the aoi with land and water.
point = ee.Geometry.Point([89.2595, 21.7317])

# Position the map.
Map.centerObject(point, 13)
Map.addLayer(aoi, {}, 'AOI')

# Sentinel-1 wet season data.
wetS1 = ee.Image(
'projects/gee-book/assets/A3-2/wet_season_tscan_2020')
# Sentinel-1 dry season data.
dryS1 = ee.Image(
'projects/gee-book/assets/A3-2/dry_season_tscan_2020')
# Sentinel-2 mosaic.
S2 = ee.Image('projects/gee-book/assets/A3-2/Sundarbans_S2_2020')

#Visualize the input data.
s1VisParams = {
    'bands': ['VV_min', 'VH_min', 'VVVH_ratio_min'],
    'min': -36,
    'max': 3
}
s2VisParams = {
    'bands': ['swir1', 'nir', 'red'],
    'min': 82,
    'max': 3236
}

Map.addLayer(dryS1, s1VisParams, 'S1 dry', False)
Map.addLayer(wetS1, s1VisParams, 'S1 wet', False)
Map.addLayer(S2, s2VisParams, 'S2 2020')

NDVI = S2.normalizedDifference(['nir', 'red']).rename(['NDVI'])

ratio_swir1_nir = S2.expression(
'swir1/(nir+0.1)', {
    'swir1': S2.select('swir1'),
    'nir': S2.select('nir')
}) \
.rename('ratio_swir1_nir_wet')

data_stack = S2.addBands(NDVI).addBands(ratio_swir1_nir).addBands(
dryS1).addBands(wetS1)

print(data_stack.getInfo())

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------

#**
# This script computes surface water mask using
# Canny Edge detector and Otsu thresholding.
# See the following paper for details:
# http:#www.mdpi.com/2072-4292/8/5/386
#
# Author: Gennadii Donchyts
# Contributors: Nicholas Clinton
#
#

#**
# Return the DN that maximizes interclass variance in B5 (in the region).
#

def func_imr(histogram):
    histogram = ee.Dictionary(histogram)

    counts = ee.Array(histogram.get('histogram'))
    means = ee.Array(histogram.get('bucketMeans'))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    sum = means.multiply(counts).reduce(ee.Reducer.sum(), [0]) \
    .get([0])
    mean = sum.divide(total)

    indices = ee.List.sequence(1, size)

    # Compute between sum of squares, where each mean partitions the data.

    def func_omz(i):
            aCounts = counts.slice(0, 0, i)
            aCount = aCounts.reduce(ee.Reducer.sum(), [0]) \
            .get([0])
            aMeans = means.slice(0, 0, i)
            aMean = aMeans.multiply(aCounts) \
            .reduce(ee.Reducer.sum(), [0]).get([0]) \
            .divide(aCount)
            bCount = total.subtract(aCount)
            bMean = sum.subtract(aCount.multiply(aMean)) \
            .divide(bCount)
            return aCount.multiply(aMean.subtract(mean).pow(
            2)).add(
            bCount.multiply(bMean.subtract(mean).pow(
            2)))

    bss = indices.map(func_omz)
















    # Return the mean value corresponding to the maximum BSS.
    return means.sort(bss).get([-1])

otsu = func_imr


















































# Buffer around NDWI edges.
edgeBuffer = edge \
.focal_max(ee.Number(scale).multiply(1), 'square', 'meters')
imageEdge = image.mask(edgeBuffer)

# Compute threshold using Otsu thresholding.
buckets = 100
hist = ee.Dictionary(ee.Dictionary(imageEdge \
.reduceRegion(
reducer = ee.Reducer.histogram(buckets),
geometry = bounds,
scale = scale,
maxPixels = 1e9
)) \
.values() \
.get(0))

threshold = ee.Number(ee.Algorithms.If(
condition = hist.contains('bucketMeans'),
TrueCase = otsu(hist),
FalseCase = 0.3
))

if (debug):
    Map.addLayer(edge.mask(edge), {
        'palette': ['ff0000']
    }, 'edges', False)
    print('Threshold: ', threshold.getInfo())
    print(ui.Chart.image.histogram(image, bounds, scale,
    buckets).getInfo())
    print(ui.Chart.image.histogram(imageEdge, bounds, scale,
    buckets).getInfo())


return minValue not == 'undefined' ? threshold.max(minValue) :
threshold


bounds = ee.Geometry(Map.getBounds(True))

image = data_stack
print('image', image.getInfo())

ndwi_for_water = image.normalizedDifference(['green', 'nir'])
debug = True
scale = 10
cannyThreshold = 0.9
cannySigma = 1
minValue = -0.1
th = computeThresholdUsingOtsu(ndwi_for_water, scale, bounds,
cannyThreshold, cannySigma, minValue, debug)

print('th', th.getInfo())

def getEdge(mask):
    return mask.subtract(mask.focal_min(1))


water_mask = ndwi_for_water.mask(ndwi_for_water.gt(th))


def func_igl(th):
    Map.addLayer(water_mask, {
            'palette': '0000ff'
        }, 'water mask (th=' + th + ')')

th.evaluate(func_igl)





# Create land mask area.
land = water_mask.unmask()
land_mask = land.eq(0)
Map.addLayer(land_mask, {}, 'Land mask', False)

# Remove areas with elevation greater than mangrove elevation threshold.
elev_thresh = 40
dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
elev_mask = dem.lte(elev_thresh)
land_mask = land_mask.updateMask(elev_mask)

# Load global mangrove dataset as reference for training.
mangrove_ref = ee.ImageCollection('LANDSAT/MANGROVE_FORESTS') \
.filterBounds(aoi) \
.first() \
.clip(aoi)
Map.addLayer(mangrove_ref, {
    'palette': 'Green'
}, 'Reference Mangroves', False)

# Buffer around known mangrove area with a specified distance.
buffer_dist = 1000
mang_buffer = mangrove_ref \
.focal_max(buffer_dist, 'square', 'meters') \
.rename('mangrove_buffer')
Map.addLayer(mang_buffer, {}, 'Mangrove Buffer', False)

# Mask land from mangrove buffer.
area_to_classify = mang_buffer.updateMask(land_mask).selfMask()
Map.addLayer(area_to_classify,
{},
'Mangrove buffer with water and elevation mask',
False)
image_to_classify = data_stack.updateMask(area_to_classify)
Map.addLayer(image_to_classify,
{
    'bands': ['swir1', 'nir', 'red'],
    'min': 82,
    'max': 3236
},
'Masked Data Stack',
False)

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------
Map
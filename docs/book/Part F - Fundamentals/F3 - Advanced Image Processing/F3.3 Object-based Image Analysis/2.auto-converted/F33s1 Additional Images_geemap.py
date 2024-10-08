import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F3.3 Object-Based Image Analysis
#  Checkpoint:   F33s1 - Supplemental
#  Authors:      Morgan A. Crowley, Jeffrey Cardille, Noel Gorelick
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

##############################
# The purpose of this script is to compare segmented and
# per-pixel unsupervised classifications for the same image.
# In particular, this script uses SNIC segmentation to grow
# superpixels, basing the segmentation on multiple bands.
##############################

##############################
# 0. More information about SNIC segmentation
##############################

# SNIC stands for 'Simple Non-Iterative Clustering.'
# Segmentation algorithms like SNIC create pixel clusters
# using imagery information such as texture, color or pixel
# values, shape, and size.  SNIC is a bottom-up, seed-based
# segmentation approach that groups neighboring pixels together
# into clusters based on input data and parameters such as
# compactness, connectivity, and neighborhood size.

##############################
# 1. Functions to be used in this script.
##############################

# 1.1 Unsupervised k-Means classification

# This function does unsupervised clustering classification .
#  input = any image. All bands will be used for clustering.
#  numberOfUnsupervisedClusters = tuneable parameter for how
#    many clusters to create.
numberOfUnsupervisedClusters,
defaultStudyArea,
nativeScaleOfImage) {

    # Make a new sample set on the input. Here the sample set is
    # randomly selected spatially.
    training = input.sample(
        region = defaultStudyArea,
        scale = nativeScaleOfImage,
        numPixels = 1000
        )

    cluster = ee.Clusterer.wekaKMeans(
    numberOfUnsupervisedClusters) \
    .train(training)

    # Now apply that clusterer to the raw image that was also passed in.
    toexport = input.cluster(cluster)

    # The first item is the unsupervised classification. Name the band.
    return toexport.select(0).rename('unsupervisedClass')
}

# 1.2 Simple normalization by maxes function.

def func_opg(img, bandMaxes):
    return img.divide(bandMaxes)

afn_normalize_by_maxes = func_opg



# 1.3 Seed Creation and SNIC segmentation Function
Connectivity, NeighborhoodSize, SeedShape) {
    print('** 1.3a Begin Seed Creation **'.getInfo())
    theSeeds = ee.Algorithms.Image.Segmentation.seedGrid(
    SuperPixelSize, SeedShape)

    print('** 1.3b Begin SNIC segmentation **'.getInfo())
    snic2 = ee.Algorithms.Image.Segmentation.SNIC(
        image = imageOriginal,
        size = SuperPixelSize,
        compactness = Compactness,
        connectivity = Connectivity,
        neighborhoodSize = NeighborhoodSize,
        seeds = theSeeds
        )

    theStack = snic2.addBands(theSeeds)

    print(
    '** 1.3c Finished Seed Creation and SNIC segmentation **' \
    .getInfo())
    return (theStack)
}

# 1.4 Simple add mean to Band Name function

def func_sii(i):
    return i + '_mean'

afn_addMeanToBandName = (func_sii)



##############################
# 2. Parameters to function calls
##############################

# 2.1. Unsupervised KMeans Classification Parameters
numberOfUnsupervisedClusters = 4

# 2.2. Visualization and Saving parameters
# For different images, you might want to change the min and max
# values to stretch. Useful for images 2 and 3, the normalized images.
centerObjectYN = True

# 2.3 Object-growing parameters to change
# Adjustable Superpixel Seed and SNIC segmentation Parameters:
# The superpixel seed location spacing, in pixels.
SNIC_SuperPixelSize = 16
# Larger values cause clusters to be more compact (square/hexagonal).
# Setting this to 0 disables spatial distance weighting.
SNIC_Compactness = 0
# Connectivity. Either 4 or 8.
SNIC_Connectivity = 4
# Either 'square' or 'hex'.
SNIC_SeedShape = 'square'

# 2.4 Parameters that can stay the same.
# Tile neighborhood size (to avoid tile boundary artifacts).
# Defaults to 2 * size.
SNIC_NeighborhoodSize = 2 * SNIC_SuperPixelSize

#############################
# 3. Statements
#############################

# 3.1  Selecting an Image to Classify

# NOTE: If you're unsure which bands to use for your image, check out:
# Sentinel-2:  https:#forum.step.esa.int/t/list-of-band-combinations-for-sentinel-2/1156
# Landsat 8:  https:#www.esri.com/arcgis-blog/products/product/imagery/band-combinations-for-landsat-8/
# Landsat 5 and 7: http:#web.pdx.edu/~emch/ip1/bandcombinations.html

whichImage = 6

if (whichImage == 1):
    # Image 1
    # Puget Sound, WA: Forest Harvest
    # (April 21, 2016)
    # Harvested Parcels
    # Clear Parcel Boundaries
    # Sentinel 2, 10m
    whichCollection = 'COPERNICUS/S2'
    ImageToUseID = '20160421T191704_20160421T212107_T10TDT'
    originalImage = ee.Image(whichCollection + '/' + \
    ImageToUseID)
    print(ImageToUseID, originalImage.getInfo())
    nativeScaleOfImage = 10
    threeBandsToDraw = ['B4', 'B3', 'B2']
    bandsToUse = ['B4', 'B3', 'B2']
    bandMaxes = [1e4, 1e4, 1e4]
    drawMin = 0
    drawMax = 0.3
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-123.35, 47.7],
    [-123.35, 47.5],
    [-123, 47.5],
    [-123, 47.7]
    ]
    ])
    zoomBox1 = \
    ee.Geometry.Polygon(
    [
    [
    [-123.13105468749993, 47.612974066532004],
    [-123.13105468749993, 47.56214700543596],
    [-123.00179367065422, 47.56214700543596],
    [-123.00179367065422, 47.612974066532004]
    ]
    ], None, False)
    zoomArea = zoomBox1
    Map.addLayer(originalImage.select(threeBandsToDraw), {
        'min': 0,
        'max': 2000
    }, '3.1 ' + ImageToUseID,
    True,
    1)


if (whichImage == 2):
    ##Image 4.2
    #Puget Sound, WA: Forest Harvest
    #(August 12, 1973)
    #Harvested Parcels
    #Clear Parcel Boundaries
    #Landsat 1, 80m
    originalImage = ee.Image('LANDSAT/LM1/LM10510271973224AAA05')
    ImageToUseID = 'LM10510271973224AAA05'
    print(ImageToUseID, originalImage.getInfo())
    nativeScaleOfImage = 80
    bandsToUse = ['B4', 'B5', 'B6', 'B7']
    bandMaxes = [150, 150, 150, 150]
    threeBandsToDraw = ['B6', 'B5', 'B4']
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-123.39225769042969, 47.74178608664663],
    [-123.3929443359375, 47.515964043627555],
    [-122.90542602539062, 47.51318147039422],
    [-122.904052734375, 47.741786086646655]
    ]
    ])
    zoomArea = defaultStudyArea
    Map.addLayer(originalImage, {
        'min': 0,
        'max': 150
    }, '3.2 ' + ImageToUseID)
    drawMax = 1


if (whichImage == 3):
    ##Image 4.3
    #'Cape Cod, MA:
    #Shoreline Changes
    #(June 12, 1984)
    #Earthshots'
    #L5, 30m
    originalImage = ee.Image(
    'LANDSAT/LT05/C01/T1/LT05_011031_19840612')
    ImageToUseID = 'LT05_011031_19840612'
    print(ImageToUseID, originalImage.getInfo())
    nativeScaleOfImage = 30
    bandsToUse = ['B4', 'B3', 'B2']
    bandMaxes = [255, 255, 255]
    threeBandsToDraw = ['B4', 'B3', 'B2']
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-70.521240234375, 41.5538109921796],
    [-69.840087890625, 41.545589036668105],
    [-69.85107421875, 42.18375873465217],
    [-70.5047607421875, 42.18375873465217]
    ]
    ])
    zoomArea = defaultStudyArea
    Map.addLayer(originalImage.select(threeBandsToDraw), {
        'min': 0,
        'max': 150
    }, '3.3 ' + \
    ImageToUseID)
    drawMax = 1


if (whichImage == 4):
    ##Image 4.4
    #'Cape Cod, MA:
    #Shoreline Changes
    #(Sep 15, 2015)
    #Earthshots'
    #L8, 30m
    originalImage = ee.Image(
    'LANDSAT/LC08/C01/T1_SR/LC08_011031_20150906')
    ImageToUseID = 'LC08_011031_20150906'
    print(ImageToUseID, originalImage.getInfo())
    nativeScaleOfImage = 30
    bandsToUse = ['B5', 'B4', 'B3']
    bandMaxes = [1e4, 1e4, 1e4]
    threeBandsToDraw = ['B5', 'B4', 'B3']
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-70.521240234375, 41.5538109921796],
    [-69.840087890625, 41.545589036668105],
    [-69.85107421875, 42.18375873465217],
    [-70.5047607421875, 42.18375873465217]
    ]
    ])
    zoomArea = defaultStudyArea
    Map.addLayer(originalImage.select(threeBandsToDraw).clip(
    defaultStudyArea),{
        'min': 0,
        'max': 1000
    } , '3.4 ' + ImageToUseID)
    drawMax = 1


if (whichImage == 5):
    ##Image 4.5
    #'Hanceville, BC:
    #Fire Disturbance
    #(Sept. 28, 2017)'
    #Sentinel-2, 20m
    originalImage = ee.Image(
    'COPERNICUS/S2/20170928T191139_20170928T191139_T10UEC')
    ImageToUseID = '20170928T191139_20170928T191139_T10UEC'
    print(ImageToUseID, originalImage.getInfo())
    nativeScaleOfImage = 20
    bandsToUse = ['B8', 'B11', 'B12']
    bandMaxes = [1e4, 1e4, 1e4]
    threeBandsToDraw = ['B8', 'B11', 'B12']
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-122.9754638671875, 51.77803705914518],
    [-121.46484375, 51.529251355189906],
    [-121.4483642578125, 51.70660846336452],
    [-121.431884765625, 52.32526831457076],
    [-122.9864501953125, 52.34540753654635]
    ]
    ])
    zoomArea = defaultStudyArea
    Map.addLayer(originalImage.select(threeBandsToDraw), {'min':0, 'max':2000}, '3.5 ' + \
    ImageToUseID)
    drawMax = 1


if (whichImage == 6):
    ##Image 4.6
    #'Hanceville, BC:
    #Fire Disturbance
    #(Oct 3, 2017)'
    #Modis, 250m
    originalImage = ee.Image('MODIS/006/MOD09GQ/2017_10_03')
    ImageToUseID = 'MOD09GQ2017_10_03'
    print(ImageToUseID, originalImage.getInfo())
    nativeScaleOfImage = 250
    bandsToUse = ['sur_refl_b01', 'sur_refl_b02']
    bandMaxes = [1e4, 1e4]
    threeBandsToDraw = ['sur_refl_b02','sur_refl_b01']
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-122.9754638671875, 51.77803705914518],
    [-121.46484375, 51.529251355189906],
    [-121.4483642578125, 51.70660846336452],
    [-121.431884765625, 52.32526831457076],
    [-122.9864501953125, 52.34540753654635]
    ]
    ])
    zoomArea = defaultStudyArea
    Map.addLayer(originalImage.select(threeBandsToDraw), {'min':-100, 'max':5000}, '3.6 ' + \
    ImageToUseID)
    drawMax = 1


##############################
# 4. Image Preprocessing
##############################

#4.1 You can use the geometry of image to clip by using the following line:
#defaultStudyArea = originalImage.geometry()

clippedImageSelectedBands = originalImage.clip(defaultStudyArea) \
.select(bandsToUse)

ImageToUse = afn_normalize_by_maxes(clippedImageSelectedBands,
bandMaxes)

##############################
# 5. SNIC Clustering
##############################

# This function returns a multi-banded image that has had
# SNIC applied to it. It automatically determines the new names
# of the bands that will be returned from the segmentation.

print('5.1 Execute SNIC'.getInfo())
SNIC_MultiBandedResults = afn_SNIC(
ImageToUse,
SNIC_SuperPixelSize,
SNIC_Compactness,
SNIC_Connectivity,
SNIC_NeighborhoodSize,
SNIC_SeedShape
)

SNIC_MultiBandedResults = SNIC_MultiBandedResults \
.reproject('EPSG:3857', None, nativeScaleOfImage)
print('5.2 SNIC Multi-Banded Results', SNIC_MultiBandedResults.getInfo())

Map.addLayer(SNIC_MultiBandedResults.select('clusters') \
.randomVisualizer(), {}, '5.3 SNIC Segment Clusters', True, 1)

theSeeds = SNIC_MultiBandedResults.select('seeds')
Map.addLayer(theSeeds, {
    'palette': 'red'
}, '5.4 Seed points of clusters', True, 1)

bandMeansToDraw = threeBandsToDraw.map(afn_addMeanToBandName)
print('5.5 band means to draw', bandMeansToDraw.getInfo())
clusterMeans = SNIC_MultiBandedResults.select(bandMeansToDraw)
print('5.6 Cluster Means by Band', clusterMeans.getInfo())
Map.addLayer(clusterMeans, {
    'min': drawMin,
    'max': drawMax
}, '5.7 Image repainted by segments', True, 0)

##############################
# 6. Execute Classifications
##############################

# 6.1 Per Pixel Unsupervised Classification for Comparison

PerPixelUnsupervised = afn_Kmeans(ImageToUse,
numberOfUnsupervisedClusters, defaultStudyArea,
nativeScaleOfImage)
Map.addLayer(PerPixelUnsupervised.select('unsupervisedClass') \
.randomVisualizer(), {}, '6.1 Per-Pixel Unsupervised', True, 0
)
print('6.1b Per-Pixel Unsupervised Results:', PerPixelUnsupervised.getInfo())

# 6.2 SNIC Unsupervised Classification for Comparison

bandMeansNames = bandsToUse.map(afn_addMeanToBandName)
print('6.2 band mean names returned by segmentation', bandMeansNames.getInfo())
meanSegments = SNIC_MultiBandedResults.select(bandMeansNames)
SegmentUnsupervised = afn_Kmeans(meanSegments,
numberOfUnsupervisedClusters, defaultStudyArea,
nativeScaleOfImage)
Map.addLayer(SegmentUnsupervised.randomVisualizer(), {},
'6.3 SNIC Clusters Unsupervised', True, 0)
print('6.3b Per-Segment Unsupervised Results:', SegmentUnsupervised.getInfo())

##############################
# 7. Zoom if requested
##############################

if (centerObjectYN == True):
    Map.centerObject(zoomArea, 14)


#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------
Map
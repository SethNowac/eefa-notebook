import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F3.3 Object-Based Image Analysis
#  Checkpoint:   F33c
#  Authors:      Morgan A. Crowley, Jeffrey Cardille, Noel Gorelick
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# 1.1 Unsupervised k-Means classification

# This function does unsupervised clustering classification
# input = any image. All bands will be used for clustering.
# numberOfUnsupervisedClusters = tunable parameter for how
#        many clusters to create.
defaultStudyArea, nativeScaleOfImage) {

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
    clusterUnsup = toexport.select(0).rename(
    'unsupervisedClass')
    return (clusterUnsup)
}

# 1.2 Simple normalization by maxes function.

def func_dkw(img, bandMaxes):
    return img.divide(bandMaxes)

afn_normalize_by_maxes = func_dkw



# 1.3 Seed Creation and SNIC segmentation Function
Connectivity, NeighborhoodSize, SeedShape) {
    theSeeds = ee.Algorithms.Image.Segmentation.seedGrid(
    SuperPixelSize, SeedShape)
    snic2 = ee.Algorithms.Image.Segmentation.SNIC(
        image = imageOriginal,
        size = SuperPixelSize,
        compactness = Compactness,
        connectivity = Connectivity,
        neighborhoodSize = NeighborhoodSize,
        seeds = theSeeds
        )
    theStack = snic2.addBands(theSeeds)
    return (theStack)
}

# 1.4 Simple add mean to Band Name function

def func_dlv(i):
    return i + '_mean'

afn_addMeanToBandName = (func_dlv)



##############################
# 2. Parameters to function calls
##############################

# 2.1. Unsupervised KMeans Classification Parameters
numberOfUnsupervisedClusters = 4

##############################
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

# 2.4 Parameters that can stay unchanged
# Tile neighborhood size (to avoid tile boundary artifacts). Defaults to 2 * size.
SNIC_NeighborhoodSize = 2 * SNIC_SuperPixelSize

#############################
# 3. Statements
#############################

# 3.1  Selecting Image to Classify
whichImage = 1; 
if (whichImage == 1):
    # Image 1.
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
    # threeBandsToDraw = ['B4', 'B3', 'B2']
    threeBandsToDraw = ['B8', 'B11', 'B12']
    # bandsToUse = ['B4', 'B3', 'B2']
    bandsToUse = ['B8', 'B11', 'B12']
    bandMaxes = [1e4, 1e4, 1e4]
    drawMin = 0
    drawMax = 0.3
    defaultStudyArea = ee.Geometry.Polygon(
    [
    [
    [-123.13105468749993, 47.612974066532004],
    [-123.13105468749993, 47.56214700543596],
    [-123.00179367065422, 47.56214700543596],
    [-123.00179367065422, 47.612974066532004]
    ]
    ])
    zoomArea = ee.Geometry.Polygon(
    [
    [
    [-123.13105468749993, 47.612974066532004],
    [-123.13105468749993, 47.56214700543596],
    [-123.00179367065422, 47.56214700543596],
    [-123.00179367065422, 47.612974066532004]
    ]
    ], None, False)

Map.addLayer(originalImage.select(threeBandsToDraw), {
    'min': 0,
    'max': 2000
}, '3.1 ' + ImageToUseID, True, 1)


##############################
# 4. Image Preprocessing
##############################
clippedImageSelectedBands = originalImage.clip(defaultStudyArea) \
.select(bandsToUse)
ImageToUse = afn_normalize_by_maxes(clippedImageSelectedBands,
bandMaxes)

Map.addLayer(ImageToUse.select(threeBandsToDraw), {
    'min': 0.028,
    'max': 0.12
},
'4.3 Pre-normalization image', True, 0)

##############################
# 5. SNIC Clustering
##############################

# This function returns a multi-banded image that has had SNIC
# applied to it. It automatically determine the new names
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

##############################
# 7. Zoom if requested
##############################
if (centerObjectYN == True):
    Map.centerObject(zoomArea, 14)


#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------
Map
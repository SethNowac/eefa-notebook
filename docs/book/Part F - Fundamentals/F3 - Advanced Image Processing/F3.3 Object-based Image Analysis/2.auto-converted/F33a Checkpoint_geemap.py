import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F3.3 Object-Based Image Analysis
#  Checkpoint:   F33a
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

def func_wpa(img, bandMaxes):
    return img.divide(bandMaxes)

afn_normalize_by_maxes = func_wpa



# 1.4 Simple add mean to Band Name function

def func_syz(i):
    return i + '_mean'

afn_addMeanToBandName = (func_syz)



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
    threeBandsToDraw = ['B4', 'B3', 'B2']
    bandsToUse = ['B4', 'B3', 'B2']
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
'4.3 Post-normalization image', True, 0)

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
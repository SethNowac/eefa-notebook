import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F4.7 Interpreting Time Series with CCDC
#  Checkpoint:   F47b
#  Authors:      Paulo Arévalo, Pontus Olofsson
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

utils = require(
'users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/api')

studyRegion = ee.Geometry.Rectangle([
[-63.9533, -10.1315],
[-64.9118, -10.6813]
])

# Define start, end dates and Landsat bands to use.
startDate = '2000-01-01'
endDate = '2020-01-01'
bands = ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']

# Retrieve all clear, Landsat 4, 5, 7 and 8 observations (Collection 2, Tier 1).
filteredLandsat = utils.Inputs.getLandsat(
collection = 2
) \
.filterBounds(studyRegion) \
.filterDate(startDate, endDate) \
.select(bands)

print(filteredLandsat.first().getInfo())

# Set CCD params to use.
ccdParams = {
    'breakpointBands': ['GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2'],
    'tmaskBands': ['GREEN', 'SWIR1'],
    'minObservations': 6,
    'chiSquareProbability': 0.99,
    'minNumOfYearsScaler': 1.33,
    'dateFormat': 1,
    'lambda': 0.002,
    'maxIterations': 10000,
    'collection': filteredLandsat
}

# Run CCD.
ccdResults = ee.Algorithms.TemporalSegmentation.Ccdc(ccdParams)
print(ccdResults.getInfo())

exportResults = False
if (exportResults):
    # Create a metadata dictionary with the parameters and arguments used.
    metadata = ccdParams
    metadata['breakpointBands'] = metadata['breakpointBands'].toString()
    metadata['tmaskBands'] = metadata['tmaskBands'].toString()
    metadata['startDate'] = startDate
    metadata['endDate'] = endDate
    metadata['bands'] = bands.toString()

    # Export results, assigning the metadata as image properties.
    #
    geemap.ee_export_image_to_asset(
    image = ccdResults.set(metadata),
    region = studyRegion,
    pyramidingPolicy = {
        ".default": 'sample'
    },
    scale = 30
    )


#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------
Map
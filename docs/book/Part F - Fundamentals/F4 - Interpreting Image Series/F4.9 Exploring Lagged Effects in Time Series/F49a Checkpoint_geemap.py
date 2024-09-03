import ee 
import math
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F4.9 Exploring Lagged Effects in Time Series
#  Checkpoint:   F49a
#  Authors:      Andréa Puzzi Nicolau, Karen Dyson, David Saah, Nicholas Clinton
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Define function to mask clouds, scale, and add variables
# (NDVI, time and a constant) to Landsat 8 imagery.
def maskScaleAndAddVariable(image):
    # Bit 0 - Fill
    # Bit 1 - Dilated Cloud
    # Bit 2 - Cirrus
    # Bit 3 - Cloud
    # Bit 4 - Cloud Shadow
    qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111',
    2)).eq(0)
    saturationMask = image.select('QA_RADSAT').eq(0)

    # Apply the scaling factors to the appropriate bands.
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-
    0.2)
    thermalBands = image.select('ST_B.*').multiply(0.00341802) \
    .add(149.0)

    # Replace the original bands with the scaled ones and apply the masks.
    img = image.addBands(opticalBands, None, True) \
    .addBands(thermalBands, None, True) \
    .updateMask(qaMask) \
    .updateMask(saturationMask)
    imgScaled = image.addBands(img, None, True)

    # Now we start to add variables of interest.
    # Compute time in fractional years since the epoch.
    date = ee.Date(image.get('system:time_start'))
    years = date.difference(ee.Date('1970-01-01'), 'year')
    timeRadians = ee.Image(years.multiply(2 * math.pi))
    # Return the image with the added bands.
    return imgScaled \
    .addBands(imgScaled.normalizedDifference(['SR_B5', 'SR_B4']) \
    .rename('NDVI')) \
    .addBands(timeRadians.rename('t')) \
    .float() \
    .addBands(ee.Image.constant(1))


# Import region of interest. Area over California.
roi = ee.Geometry.Polygon([
[-119.44617458417066,35.92639730653253],
[-119.07675930096754,35.92639730653253],
[-119.07675930096754,36.201704711823844],
[-119.44617458417066,36.201704711823844],
[-119.44617458417066,35.92639730653253]
])

# Import the USGS Landsat 8 Level 2, Collection 2, Tier 1 collection,
# filter, mask clouds, scale, and add variables.
landsat8sr = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
.filterBounds(roi) \
.filterDate('2013-01-01', '2018-01-01') \
.map(maskScaleAndAddVariable)

# Set map center.
Map.centerObject(roi, 10)

# List of the independent variable names.
independents = ee.List(['constant', 't'])

# Name of the dependent variable.
dependent = ee.String('NDVI')

# Compute a linear trend.  This will have two bands: 'residuals' and
# a 2x1 band called coefficients (columns are for dependent variables).
trend = landsat8sr.select(independents.add(dependent)) \
.reduce(ee.Reducer.linearRegression(independents.length(), 1))

# Flatten the coefficients into a 2-band image
coefficients = trend.select('coefficients') \
.arrayProject([0]) \
.arrayFlatten([independents])

# Compute a detrended series.

def func_ryc(image):
    return image.select(dependent) \
    .subtract(image.select(independents).multiply(
    coefficients) \
    .reduce('sum')) \
    .rename(dependent) \
    .copyProperties(image, ['system:time_start'])

detrended = landsat8sr.map(func_ryc)








# Function that creates a lagged collection.

def func_uwd(leftCollection, rightCollection, lagDays):
    filter = ee.Filter.And(
    ee.Filter.maxDifference(
        difference = 1000 * 60 * 60 * 24 * lagDays,
        leftField = 'system =time_start',
        rightField = 'system =time_start'
        ),
    ee.Filter.greaterThan(
        leftField = 'system =time_start',
        rightField = 'system =time_start'
        ))

    return ee.Join.saveAll(
        matchesKey = 'images',
        measureKey = 'delta_t',
        ordering = 'system =time_start',
        ascending = False, 
        ).apply(
        primary = leftCollection,
        secondary = rightCollection,
        condition = filter
        )

lag = func_uwd























# Create a lagged collection of the detrended imagery.
lagged17 = lag(detrended, detrended, 17)

# Function to stack bands.

def func_nee(image):
    # Function to be passed to iterate.

    def func_flr(current, previous):
            return ee.Image(previous).addBands(current)

    merger = func_flr

    
    return ee.ImageCollection.fromImages(image.get('images')) \
    .iterate(merger, image)

merge = func_nee











# Function to compute covariance.

def func_vfw(mergedCollection, band, lagBand):

    def func_bzl(
image):
            return image.toArray()

    return mergedCollection.select([band, lagBand]).map(func_bzl

    ).reduce(ee.Reducer.covariance(), 8)

covariance = func_vfw







lagBand = dependent.cat('_1')

# Compute covariance.
covariance17 = ee.Image(covariance(merged17, dependent, lagBand)) \
.clip(roi)

# The output of the covariance reducer is an array image,
# in which each pixel stores a 2x2 variance-covariance array.
# The off diagonal elements are covariance, which you can map
# directly using:
Map.addLayer(covariance17.arrayGet([0, 1]),
{
    'min': 0,
    'max': 0.02
},
'covariance (lag = 17 days)')

# Define the correlation function.

def func_jay(vcArrayImage):
    covariance = ee.Image(vcArrayImage).arrayGet([0, 1])
    sd0 = ee.Image(vcArrayImage).arrayGet([0, 0]).sqrt()
    sd1 = ee.Image(vcArrayImage).arrayGet([1, 1]).sqrt()
    return covariance.divide(sd0).divide(sd1).rename(
    'correlation')

correlation = func_jay







# Apply the correlation function.
correlation17 = correlation(covariance17).clip(roi)
Map.addLayer(correlation17,
{
    'min': -1,
    'max': 1
},
'correlation (lag = 17 days)')

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------#  -----------------------------------------------------------------------#  -----------------------------------------------------------------------#  -----------------------------------------------------------------------
Map
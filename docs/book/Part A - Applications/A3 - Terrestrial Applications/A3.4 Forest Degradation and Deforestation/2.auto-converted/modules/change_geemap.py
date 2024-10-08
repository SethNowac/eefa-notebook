import ee 
import math
import geemap

#* #################################/
#
# Utility functions for exploring and processing change information
#
## #################################/

from . import dates_geemap as dateUtils
from . import stats_geemap as statsUtils

# Add time band and constant
def createTimeBand(img):
    year = ee.Image(img.date().difference('1970-01-01', 'year')).rename('t')
    constant = ee.Image(1).rename('constant')
    return img.addBands(constant).addBands(year.float())


# Function to get a sequence of names using a base name and a list
# of strings to append (e.g a sequence)
def constructBandNames(base, list):

    def func_adt(i):
        return ee.String(base).cat(ee.Number(i).int().format())

    return ee.List(list).map(func_adt)




# Function to add a constant and time band
def addDependents(image):
    # Compute time in fractional years since the epoch.
    years = image.date().difference('1970-01-01', 'year')
    timeRadians = ee.Image(years.multiply(2 * math.pi)).rename('t')
    constant = ee.Image(1)
    return image.addBands(constant).addBands(timeRadians.float())



# Calculated scaled cusum OLS residuals
def calc_scaled_cusum(resids, critVal):
    # Initialize empty cusum
    dt = ee.Date(resids.first().get('system:time_start')).advance(-1, 'day').millis()
    cs_0 = ee.List([ee.Image(0.0001).set('system:time_start', dt) \
    .rename('cusum')])

    # Simple CUSUM function. Unmask images to prevent sum to fail due to masked values.
    # Unmaked values will have a value of zero and won't affect the calculation

    def func_gqe(image, list):
        previous = ee.Image(ee.List(list).get(-1))
        current_cusum = previous.select('cusum').unmask() \
        .add(image.unmask()) \
        .set('system:time_start', image.get('system:time_start'))
        return ee.List(list).add(current_cusum.rename('cusum'))

    cusum_calc = func_gqe







    # Calculate CUSUM
    cusum = ee.ImageCollection(ee.List(resids.iterate(cusum_calc, cs_0)))

    # Scaled cumulative residuals, based on statsmodels (Ploberger, Werner, and Walter Kramer 1992)
    nobs = resids.count() 

    def func_awh(x):
        return x.pow(2)

    nobssigma2 = resids.map(func_awh

    ).sum()
    ddof = ee.Number(8) 
    # This notation replicates the python opearator order
    nobssigma2 = nobssigma2.divide(nobs.subtract(ddof)).multiply(nobs)


    # Actual calculation of scaled CUSUM. Append breakpoint band

    def func_lbh(img):
        scaledres = img.divide(nobssigma2.sqrt()).set('system:time_start', img.get('system:time_start'))
        breakpoint = scaledres.abs().gte(critVal).rename('break_detected')
        return scaledres.addBands(breakpoint)

    scaled_resid = cusum.map(func_lbh)




    return scaled_resid


# Add date band in fractional year format to compare against tstart/tend
def addFracyearBand(img):
    return img.addBands(ee.Image(dateUtils.msToFrac(img.date().millis())).rename('fracYear'))


# Function to run a harmonic regression for a given band in a collection
# and return observed and predicted values, residuals, and coefficients
def harmonic_regression(ts_collection, band):

    # The number of cycles per year to model and variable name to use
    harmonics = 3
    dependent = band

    # Make a list of harmonic frequencies to model.
    # These also serve as band name suffixes.
    harmonicFrequencies = ee.List.sequence(1, harmonics)

    # Construct lists of names for the harmonic terms.
    cosNames = constructBandNames('cos_', harmonicFrequencies)
    sinNames = constructBandNames('sin_', harmonicFrequencies)

    # Independent variables.
    independents = ee.List(['constant', 't']) \
    .cat(cosNames).cat(sinNames)

    # Function to compute the specified number of harmonics
    # and add them as bands.  Assumes the time band is present.

    def func_unk(freqs):

        def func_fyu(image):
                # Make an image of frequencies.
                frequencies = ee.Image.constant(freqs)
                # This band should represent time in radians.
                time = ee.Image(image).select('t')
                # Get the cosine terms.
                cosines = time.multiply(frequencies).cos().rename(cosNames)
                # Get the sin terms.
                sines = time.multiply(frequencies).sin().rename(sinNames)
                return image.addBands(cosines).addBands(sines)

        return func_fyu

    addHarmonics = func_unk

    # Add variables.
    harmonicLandsat = (ts_collection #all_scenes
        .map(addDependents)
        .map(addHarmonics(harmonicFrequencies)))
    
    # The output of the regression reduction is a 4x1 array image.
    harmonicTrend = (harmonicLandsat
        .select(independents.add(dependent))
        .reduce(ee.Reducer.linearRegression(independents.length(), 1)))

    # Turn the array image into a multi-band image of coefficients.
    harmonicTrendCoefficients = harmonicTrend.select('coefficients') \
    .arrayProject([0]) \
    .arrayFlatten([independents])

    # Compute fitted values.

    def func_rgh(image):
        return image.addBands(
        image.select(independents) \
        .multiply(harmonicTrendCoefficients) \
        .reduce('sum') \
        .rename('fitted'))

    fittedHarmonic = harmonicLandsat.map(func_rgh)







    # Compute residuals manually

    def func_bzu(img):
        resid = (img.select(dependent)).subtract(img.select('fitted')).rename('residuals')
        return img.addBands(resid)

    calc_residuals = func_bzu



    regression_results = fittedHarmonic.map(calc_residuals)

    return ee.List([harmonicTrendCoefficients, regression_results])


def getOmission(landsatCol, ccdcImg, segId, band, critVal):

    # a) Get tstart and tend for current segment
    tStart = ccdcImg.select(segId + '_tStart')
    tEnd = ccdcImg.select(segId + '_tEnd')

    # Add band with fractional year
    fracYearCol = landsatCol.map(addFracyearBand)

    #  b) Compare date for each image against the tstart-tend per pixel, and mask accordingly
    # Test date band against dates in tstart/tend and add mask accordingly
    def maskDates(img):
        fracYear = img.select('fracYear')
        mask = ee.Image(fracYear.gte(tStart)).And(ee.Image(fracYear.lte(tEnd))).rename('dateMask')
        return img.updateMask(mask)

    maskedCol = fracYearCol.map(maskDates)
    # Do harmonic regression instead of simple linear
    regressionResults = ee.ImageCollection(harmonic_regression(maskedCol, band).get(1))

    #  f) Calculate scaled residuals and occurence of break if threshold reached
    residuals = regressionResults.select('residuals')
    # Calculated scaled CUSUM and time of break for each image
    scaled_cusum = calc_scaled_cusum(residuals, critVal)

    def func_ukt(x):
        return x.abs()

    cusum = scaled_cusum.select('cusum').map(func_ukt)


    break_detected = scaled_cusum.select('break_detected')
    # Get presence of any breaks detected for the current segment, and the max abs value
    cusum_break = break_detected.reduce(ee.Reducer.anyNonZero()).rename('omission')
    cusum_treshold = cusum.reduce(ee.Reducer.max()).rename('maxCusum')

    return ee.Image.cat([cusum_break, cusum_treshold])



def getCommission(landsatCol, ccdcImg, seg1, seg2, band):

    # a) Get tstart and tend for each segment
    tStart1 = ccdcImg.select(seg1 + '_tStart')
    tEnd1 = ccdcImg.select(seg1 + '_tEnd')
    tStart2 = ccdcImg.select(seg2 + '_tStart')
    tEnd2 = ccdcImg.select(seg2 + '_tEnd')

    # Add band with fractional year
    fracYearCol = landsatCol.map(addFracyearBand)

    #  b) Compare date for each image against the tstart-tend per pixel, and mask accordingly
    # Test date band against dates in tstart/tend and add mask accordingly
    # def maskDates(img):
    #     fracYear = img.select('fracYear')
    #     mask = ee.Image(fracYear.gte(tStart)).And(ee.Image(fracYear.lte(tEnd))).rename('dateMask')
    #     return img.updateMask(mask)


    def maskDates (col, tStart, tEnd):
        def inner(img):
            fracYear = img.select('fracYear')
            mask = ee.Image(fracYear.gte(tStart)).And(ee.Image(fracYear.lte(tEnd))).rename('dateMask')
            return img.updateMask(mask)

        return col.map(inner)


    maskedCol1 = maskDates(fracYearCol, tStart1, tEnd1)
    maskedCol2 = maskDates(fracYearCol, tStart2, tEnd2)
    maskedColGlobal = maskDates(fracYearCol, tStart1, tEnd2)

    # Run harmonic regression instead of linear
    regressionResults1 = ee.ImageCollection(harmonic_regression(maskedCol1, band).get(1))
    regressionResults2 = ee.ImageCollection(harmonic_regression(maskedCol2, band).get(1))
    regressionResultsGlobal = ee.ImageCollection(harmonic_regression(maskedColGlobal, band).get(1))

    resid1 = regressionResults1.select('residuals')
    resid2 = regressionResults2.select('residuals')
    residGlobal = regressionResultsGlobal.select('residuals')

    # 6) Get sum of squared residuals for each model
    def sumSquares(col):

        def func_uyr(x):
            return x.pow(2)

        return col.map(func_uyr

        ).sum()


    ss1 = sumSquares(resid1)
    ss2 = sumSquares(resid2)
    ssGl = sumSquares(residGlobal)

    # Get nobs per segment, directly from CCDC record
    n1 = ccdcImg.select(seg1 + '_numObs')
    n2 = ccdcImg.select(seg2 + '_numObs')
    nGl = n1.add(n2)

    # 7) Calculate Chow test statistic
    # k = ee.Number(3) #Num of parameters, 3 for now bc we are doing simple OLS
    k = ee.Number(4) 
    num = ssGl.subtract(ss1.add(ss2)).divide(k.add(1))
    den = ss1.add(ss2).divide(nGl.subtract(k.add(1).multiply(2)))
    chow = num.divide(den)

    # Calculate probability
    Fprob = statsUtils.F_cdf(chow, k, nGl.subtract(k.multiply(2)))
    return chow.addBands(Fprob).rename(['chow_F', 'prob'])

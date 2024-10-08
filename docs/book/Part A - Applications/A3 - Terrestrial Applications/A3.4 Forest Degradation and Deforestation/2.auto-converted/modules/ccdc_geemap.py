import ee 
import math
import geemap


def buildSegmentTag(nSegments):

    def func_bfh(i):
        return ee.String('S').cat(ee.Number(i).int().format())

    return ee.List.sequence(1, nSegments).map(func_bfh)




def buildBandTag(tag, bandList):
    bands = ee.List(bandList)

    def func_zvh(s):
        return ee.String(s).cat('_' + tag)

    return bands.map(func_zvh)




def buildMagnitude(fit, nSegments, bandList):
    segmentTag = buildSegmentTag(nSegments)
    zeros = ee.Image(ee.Array(ee.List.repeat(0, nSegments)))
    # Pad zeroes for pixels that have less than nSegments and then slice the first nSegment values

    def func_iwa(band):
        magImg = fit.select(band + '_magnitude').arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)

        def func_zpu(x):
                return ee.String(x).cat('_').cat(band).cat('_MAG')

        tags = segmentTag.map(func_zpu)


        return magImg.arrayFlatten([tags])

    retrieveMags = func_iwa

    return ee.Image(bandList.map(retrieveMags))








def buildRMSE(fit, nSegments, bandList):
    segmentTag = buildSegmentTag(nSegments)
    zeros = ee.Image(ee.Array(ee.List.repeat(0, nSegments)))
    # Pad zeroes for pixels that have less than 6 segments and then slice the first 6 values

    def func_owi(band):
        magImg = fit.select(band + '_rmse').arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)

        def func_zdd(x):
                return ee.String(x).cat('_').cat(band).cat('_RMSE')

        tags = segmentTag.map(func_zdd)


        return magImg.arrayFlatten([tags])

    retrieveMags = func_owi

    return ee.Image(bandList.map(retrieveMags))







def buildCoefs(fit, nSegments, bandList):
    nBands = bandList.length
    segmentTag = buildSegmentTag(nSegments)
    bandTag = buildBandTag('coef', bandList)
    harmonicTag = ['INTP','SLP','COS','SIN','COS2','SIN2','COS3','SIN3']

    zeros = ee.Image(ee.Array([ee.List.repeat(0, harmonicTag.length)])).arrayRepeat(0, nSegments)

    def func_xsb(band):
        coefImg = fit.select(band + '_coefs').arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)

        def func_yjq(x):
                return ee.String(x).cat('_').cat(band).cat('_coef')

        tags = segmentTag.map(func_yjq)


        return coefImg.arrayFlatten([tags, harmonicTag])

    retrieveCoefs = func_xsb

    return ee.Image(bandList.map(retrieveCoefs))




def buildStartEndBreakProb(fit, nSegments, tag):

    def func_ilb(s):
        return ee.String(s).cat('_'+tag)

    segmentTag = buildSegmentTag(nSegments).map(func_ilb)



    zeros = ee.Array(0).repeat(0, nSegments)
    magImg = fit.select(tag).arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)

    return magImg.arrayFlatten([segmentTag])



def buildCcdImage(fit, nSegments, bandList):
    magnitude = buildMagnitude(fit, nSegments, bandList)
    rmse = buildRMSE(fit, nSegments, bandList)

    coef = buildCoefs(fit, nSegments, bandList)
    tStart = buildStartEndBreakProb(fit, nSegments, 'tStart')
    tEnd = buildStartEndBreakProb(fit, nSegments, 'tEnd')
    tBreak = buildStartEndBreakProb(fit, nSegments, 'tBreak')
    probs = buildStartEndBreakProb(fit, nSegments, 'changeProb')
    nobs = buildStartEndBreakProb(fit, nSegments, 'numObs')
    return ee.Image.cat(coef, rmse, magnitude, tStart, tEnd, tBreak, probs, nobs)



def getSyntheticForYear(image, date, dateFormat, band, segs):
    tfit = date
    PI2 = 2.0 * math.pi
    OMEGAS = [PI2 / 365.25, PI2, PI2 / (1000 * 60 * 60 * 24 * 365.25)]
    omega = OMEGAS[dateFormat]
    imageT = ee.Image.constant([1, tfit,
    tfit.multiply(omega).cos(),
    tfit.multiply(omega).sin(),
    tfit.multiply(omega * 2).cos(),
    tfit.multiply(omega * 2).sin(),
    tfit.multiply(omega * 3).cos(),
    tfit.multiply(omega * 3).sin()]).float()

    # OLD CODE
    # Casting as ee string allows using this function to be mapped
    # selectString = ee.String('.*' + band + '_coef.*')
    # params = getSegmentParamsForYear(image, date)
    #                       .select(selectString)
    # return imageT.multiply(params).reduce('sum').rename(band)

    # Use new standard functions instead
    COEFS = ["INTP", "SLP", "COS", "SIN", "COS2", "SIN2", "COS3", "SIN3"]
    newParams = getMultiCoefs(image, date, [band], COEFS, False, segs, 'before')
    return imageT.multiply(newParams).reduce('sum').rename(band)



def getMultiSynthetic(image, date, dateFormat, bandList, segs):

    def func_old(band):
        return getSyntheticForYear(image, date, dateFormat, band, segs)

    retrieveSynthetic = func_old



    return ee.Image.cat(bandList.map(retrieveSynthetic))



def fillNoData(fit, nCoefs, nBands):
    d1 = ee.Image(ee.Array([0]).double())
    d2 = ee.Image(ee.Array([ee.List.repeat(-9999, nCoefs)])).double()

    upper = ee.Image([d1, d1, d1, d1.int32(), d1])

    # Create variable number of coef, rmse and change amplitude bands
    arrCenter = []
    arrBottom = []
    for i in range(0, nBands, 1):
        arrCenter.push(d2)
        arrBottom.push(d1, d1)

    center = ee.Image(arrCenter)
    bottom = ee.Image(arrBottom)

    mock = upper.addBands(center).addBands(bottom).rename(fit.bandNames()).updateMask(fit.mask())
    newimage = ee.ImageCollection([mock, fit]).mosaic()
    return newimage



def dateToDays(strDate):
    date = ee.Date(strDate)
    # Number of days since 01-01-0000 unti 01-01-1970
    epoch = ee.Number(719177)
    # Convert milis to days
    days = ee.Number(date.millis().divide(86400000))
    return days.add(epoch)



def dateToSegment(ccdResults, date, segNames):
    startBands = ccdResults.select(".*_tStart").rename(segNames)
    endBands = ccdResults.select(".*_tEnd").rename(segNames)

    start = startBands.lte(date)
    end = endBands.gte(date)

    segmentMatch = start.And(end)
    return segmentMatch



def filterCoefs(ccdResults, date, band, coef, segNames, behavior):

    startBands = ccdResults.select(".*_tStart").rename(segNames)
    endBands = ccdResults.select(".*_tEnd").rename(segNames)

    # Get all segments for a given band/coef. Underscore in concat ensures
    # that bands with similar names are not selected twice (e.g. GREEN, GREENNESS)
    selStr = ".*"+band+"_.*"+coef 
    coef_bands = ccdResults.select(selStr)

                # Select a segment based on conditions
    if (behavior == "normal"):
                    start = startBands.lte(date)
                    end = endBands.gte(date)
                    segmentMatch = start.And(end)
                    outCoef = coef_bands.updateMask(segmentMatch).reduce(ee.Reducer.firstNonNull())

    if (behavior == "after"):
                    segmentMatch = endBands.gt(date)
                    outCoef = coef_bands.updateMask(segmentMatch).reduce(ee.Reducer.firstNonNull())

    if (behavior ==  "before"):
                    # Mask start to avoid comparing against zero, mask after to remove zeros from logical comparison
                    segmentMatch = startBands.selfMask().lt(date).selfMask()
                    outCoef =  coef_bands.updateMask(segmentMatch).reduce(ee.Reducer.lastNonNull())


                # TODO: Add a "automatic" after, then before behavior
    return outCoef




def normalizeIntercept(intercept, start, end, slope):
    middleDate = ee.Image(start).add(ee.Image(end)).divide(2)
    slopeCoef = ee.Image(slope).multiply(middleDate)
    return ee.Image(intercept).add(slopeCoef)



def getCoef(ccdResults, date, bandList, coef, segNames, behavior):

    def func_glz(band):
        band_coef = filterCoefs(ccdResults, date, band, coef, segNames, behavior)
        return band_coef.rename(band+"_"+coef)

    inner = func_glz



    coefs = ee.Image(bandList.map(inner)) 
    return coefs



def applyNorm(bandCoefs, segStart, segEnd):
    intercepts = bandCoefs.select(".*INTP")
    slopes = bandCoefs.select(".*SLP")
    normalized = normalizeIntercept(intercepts, segStart, segEnd, slopes)
    return bandCoefs.addBands({'srcImg':normalized, 'overwrite':True})


def getMultiCoefs(ccdResults, date, bandList, coef_list, cond, segNames, behavior):
    # Non normalized

    def func_ukg(coef):
        inner_coef = getCoef(ccdResults, date, bandList, coef, segNames, behavior)
        return inner_coef

    inner = func_ukg




    coefs = ee.Image(coef_list.map(inner))

    # Normalized
    segStart = filterCoefs(ccdResults, date, "","tStart", segNames, behavior)
    segEnd = filterCoefs(ccdResults, date, "","tEnd", segNames, behavior)
    normCoefs = applyNorm(coefs, segStart, segEnd)

    out_coefs = ee.Algorithms.If(cond, normCoefs, coefs)
    return ee.Image(out_coefs)



def getChanges(ccdResults, startDate, endDate, segNames):
    breakBands = ccdResults.select(".*_tBreak").rename(segNames)
    segmentMatch = breakBands.gte(startDate).And(breakBands.lt(endDate))
    return segmentMatch



def filterMag(ccdResults, startDate, endDate, band, segNames):
    segMask = getChanges(ccdResults, startDate, endDate, segNames)
    selStr = ".*"+band+".*"+"MAG" 
    feat_bands = ccdResults.select(selStr)
    filteredMag = feat_bands.mask(segMask).reduce(ee.Reducer.max())
    numTbreak = ccdResults.select(".*tBreak").mask(segMask).reduce(ee.Reducer.count())
    filteredTbreak = ccdResults.select(".*tBreak").mask(segMask).reduce(ee.Reducer.max())
    return filteredMag.addBands(filteredTbreak) \
    .addBands(numTbreak) \
    .rename(['MAG', 'tBreak', 'numTbreak'])



def phaseAmplitude(img, bands, sinName, cosName):

    def func_sbb(x):
        return x+sinName

    sinNames = bands.map(func_sbb)



    def func_iev(x):
        return x+cosName

    cosNames = bands.map(func_iev)



    def func_oef(x):
        return x+'_PHASE'

    phaseNames = bands.map(func_oef)



    def func_lme(x):
        return x+'_AMPLITUDE'

    amplitudeNames = bands.map(func_lme)


    phase =  img.select(sinNames).atan2(img.select(cosNames)) \
    .unitScale(-math.pi, math.pi) \
    .multiply(365) \
    .rename(phaseNames)

    amplitude = img.select(sinNames).hypot(img.select(cosNames)).rename(amplitudeNames)
    return phase.addBands(amplitude)



def newPhaseAmplitude(img, sinExpr, cosExpr):
    sin = img.select(sinExpr)
    cos = img.select(cosExpr)

    phase = sin.atan2(cos) \
    .unitScale(-3.14159265359, 3.14159265359) \
    .multiply(365)

    amplitude = sin.hypot(cos)


    def func_ain(x):
        return ee.String(x).replace('_SIN', '_PHASE')

    phaseNames = phase.bandNames().map(func_ain)



    def func_gti(x):
        return ee.String(x).replace('_SIN', '_AMPLITUDE')

    amplitudeNames = amplitude.bandNames().map(func_gti)


    return phase.rename(phaseNames).addBands(amplitude.rename(amplitudeNames))
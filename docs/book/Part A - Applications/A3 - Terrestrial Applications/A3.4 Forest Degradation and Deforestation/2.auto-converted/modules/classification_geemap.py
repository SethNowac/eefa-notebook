import ee 
import math
import geemap


# Utility functions for classifying CCDC
from . import dates_geemap as dateUtils
from . import inputs_geemap as inputUtils
from . import ccdc_geemap as ccdcUtils

def getBinaryLabel(fc, property, targetClass):
    if (not fc):
        return('Required argument [fc] missing.')

    if (not targetClass):
        return('Required argument [targetClass] missing.')


    fc = ee.FeatureCollection(fc)


    def func_wan(i):
        return i.set(property, 1)

    targetFc = fc.filterMetadata(property,'equals',targetClass).map(func_wan)



    def func_yaf(i):
        return i.set(property, 0)

    notTargetFc = fc.filterMetadata(property,'not_equals',targetClass).map(func_yaf)



    return targetFc.merge(notTargetFc)




def getClassProbs(fc, coefsToClassify, classList, classifier, property):

    def func_dgi(num):
        return ee.String('probability_').cat(ee.String(ee.Number(num).format()))

    bandNames = classList.map(func_dgi)





    def func_bsm(num):
        fcBinary = getBinaryLabel(fc, property, num)
        trained = classifier.train(
            features=fcBinary,
            classProperty=property,
            inputProperties=coefsToClassify.bandNames()
            )
        return coefsToClassify.classify(trained)


    classProbs = classList.map(func_bsm)









    return ee.ImageCollection(ee.List(classProbs)).toBands().rename(bandNames)




def makeGrids(region, count, size, seed):

    if (seed == 'random'):
        seed = math.ceil(math.random() * 1000)


    # Create sample of random points within region
    randomPoints = ee.FeatureCollection.randomPoints(
    region=region,
    points=count,
    seed=seed
    )

    # Take bounding box of buffered samples

    def func_jvh(point):
        buffer = point.buffer(size/2)
        return buffer.bounds()

    bb =randomPoints.map(func_jvh)




    # Assign id
    bbList = bb.toList(bb.size())
    indexList = ee.List.sequence(1, bb.size())


    def func_hfg(i):
        return ee.Feature(bbList.get(
        ee.Number(i).subtract(1))) \
        .set( {'ID': i} )

    return ee.FeatureCollection(indexList.map(func_hfg



    ))




def newPhaseAmplitude(img, bands, sinName, cosName):

    def func_yph(x):
        return ee.String(x).cat(sinName)

    sinNames = bands.map(func_yph)



    def func_mwa(x):
        return ee.String(x).cat(cosName)

    cosNames = bands.map(func_mwa)



    def func_hyx(x):
        return ee.String(x).cat('_PHASE')

    phaseNames = bands.map(func_hyx)



    def func_vku(x):
        return ee.String(x).cat('_AMPLITUDE')

    amplitudeNames = bands.map(func_vku)


    phase =  img.select(sinNames).atan2(img.select(cosNames)) \
    .unitScale(-3.14159265359, 3.14159265359) \
    .multiply(365) \
    .rename(phaseNames)

    amplitude = img.select(sinNames).hypot(img.select(cosNames)).rename(amplitudeNames)
    return phase.addBands(amplitude)


def sampleResultProcedure(trainingData, coefNames, bandList, dateProperty, extraBands, ccdcImage, segs, ccdcDateFmt, trainingDateFmt, scale):
    ccdcDateFmt = float(ccdcDateFmt)
    uniqueYears = ee.Dictionary(
    ee.FeatureCollection(
    trainingData).aggregate_histogram(dateProperty)).keys()


    def func_mnm(strYear):
        # strYear = '2010'
        year = ee.Number.parse(strYear)
        fcYear = trainingData.filterMetadata(dateProperty,'equals',year)

        formattedDate = dateUtils.convertDate(
            inputFormat=trainingDateFmt,
            inputDate=year,
            outputFormat=ccdcDateFmt
            )
        coefs = ccdcUtils.getMultiCoefs(ccdcImage, formattedDate, bandList, coefNames, True, segs, 'after')

        # Use new code to reduce calculations
        phaseAmps = ccdcUtils.newPhaseAmplitude(coefs, '.*SIN.*', '.*COS.*')
        coefs = coefs.addBands(phaseAmps)
        if (extraBands):
                coefs = coefs.addBands(extraBands)

        return coefs.sampleRegions(
            collection=fcYear,
            scale=scale,
            tileScale=16,
            geometries=True
            )


    return ee.FeatureCollection(uniqueYears.map(func_mnm)).flatten()




def runCcdcProcedure(trainingData, coefNames, bandList, dateProperty, extraBands, landsatParams, segs):
    segs = segs or ["S1", "S2", "S3", "S4", "S5", "S6"]

    trainingCCDC = getTraining(
        trainingData=trainingData,
        extraBands=extraBands,
        landsatParams=landsatParams
    )


    def func_lqd(feat):
        year = ee.Number(feat.get(dateProperty)).add(2)
        year2 = ee.String(year)
        date =dateUtils.dateToJdays(year2)

        ccdImage = ccdcUtils.buildCcdImage(trainingCCDC, 6, bandList)

        coefs = ccdcUtils.getMultiCoefs(ccdImage, date, bandList, coefNames, True, segs)

        if (extraBands):
                coefs = coefs.addBands(extraBands)


        sampleCoefs = ee.Dictionary(coefs.reduceRegion({
            'reducer': ee.Reducer.mean(),
            'geometry': feat.geometry(),
            'scale': 30,
            'crs': 'EPSG:4326',
            'tileScale': 8,
            }))

        return ee.Feature(feat).setMulti(sampleCoefs)


    return trainingData.map(func_lqd)


























def getTrainingCoefsAtDate(trainingData, coefNames, bandList, dateProperty, extraBands, ccdcImage, segs, ccdcDateFmt, trainingDateFmt, scale, landsatParams):
    coefNames = coefNames or  ['INTP','SLP','COS','SIN','RMSE','COS2','SIN2','COS3','SIN3']
    bandList =  bandList or ['BLUE','GREEN','RED','NIR','SWIR1','SWIR2']
    dateProperty = dateProperty or 'Start_Year'
    landsatParams = landsatParams or {'start': '1990-01-01', 'end': '2020-01-01'}
    segs = segs or ["S1", "S2", "S3", "S4", "S5", "S6"]
    ccdcDateFmt = ccdcDateFmt or 1
    trainingDateFmt = trainingDateFmt or 1
    scale = scale or 30

    resultImage = ccdcImage or None

    if (resultImage):
        return sampleResultProcedure(trainingData, coefNames, bandList, dateProperty, extraBands,
        resultImage, segs, ccdcDateFmt, trainingDateFmt, scale)
    else:
        return runCcdcProcedure(trainingData, coefNames, bandList, dateProperty, extraBands,
        landsatParams, segs)




def remapLC(feats, inLabel, outLabel, inList, outList):
    inList = inList or ['Water','Snow/Ice','Built','Bare','Trees','Shrub','Herbaceous','Woodland',
    'Forest','Developed','Agriculture','Barren','Grass','Ice_and_Snow','Shrubs','Wetland']

    outList = outList or [1,2,3,4,5,6,7,8,5,3,7, 4, 7, 2, 6, 1]

    def func_epi(feat):
        return feat.set(outLabel,feat.get(inLabel))

    feats = feats.map(func_epi)



    return feats.remap(
    inList,
    outList,
    outLabel
    )




def assignIds(sample, attributeName):
    attributeName = attributeName or 'ID'

    withRandom = sample.randomColumn({'seed': 1})
    withRandom = withRandom.sort('random')
    withRandomList = withRandom.toList(withRandom.size())
    indexList = ee.List.sequence(1, withRandom.size())


    def func_jlq(i):
        return ee.Feature(withRandomList.get(
        ee.Number(i).subtract(1))) \
        .set( {attributeName: i} )

    return ee.FeatureCollection(indexList.map(func_jlq



    ))




def getMiddleDate(fc, startProp, endProp, middleProp):

    def func_xoy(feat):
        start = ee.Number(feat.get(startProp))
        end = ee.Number(feat.get(endProp))
        middle = (start.add(end)).divide(2).ceil().int16()
        return feat.set(middleProp,middle)

    return fc.map(func_xoy)









def makeRow(color, name):
    colorBox = ui.Label(
    style={
        'backgroundColor':color,
        'padding':'8px',
        'margin':'0 0 4px 0'
    }
    )

    description = ui.Label({
    'value':name,
    'style':{'margin':'0 0 4px 6px'}
    })

    return ui.Panel({
    'widgets':[colorBox, description],
    'layout':ui.Panel.Layout.Flow('horizontal')
    })



def makeLegend(classes, palette, title, width, position):
    width = width or '250px'
    title = title or 'Legend'
    position = position or 'bottom-right'

    legend = ui.Panel({'style': {'shown': True, 'width': width}})
    legend.add(ui.Label(title))
    legend.style().set({'position': position})
    for i in range(0, classes.length, 1):
        legend.add(makeRow(palette[i],classes[i]))

    return legend



def getInputFeatures(seg, imageToClassify, predictors, bandNames, ancillary):
    str = ee.String('S') \
    .cat(ee.String(ee.Number(seg).int8())) \
    .cat('_.*')
    # Another string to remove segment prefix
    str2 = ee.String('S') \
    .cat(ee.String(ee.Number(seg).int8())) \
    .cat('_')

    # Select bands to classify and add ancillary
    bands = imageToClassify.select([str])

    # Rename without prefix

    def func_evi(bn):
        newName = ee.String(bn).replace('_coef_','_').replace('_COEF_','_').split(str2).get(1)
        return ee.String(newName)

    renamedBands = bands.bandNames().map(func_evi)



    bands = bands.rename(renamedBands)

    # Mask where there's no model
    bands = bands.updateMask(bands.select('tStart').gt(0))

    # Normalize the intercepts
    bands = ccdcUtils.applyNorm(bands, bands.select('.*tStart'), bands.select('.*tEnd'))

    # Get phase and amplitude if necessary
    # phaseAmp = makePhaseAmp(bands, bandNames, ['_SIN','_SIN2','_SIN3'], ['_COS','_COS2','_COS3'])
    phaseAmp = ccdcUtils.newPhaseAmplitude(bands, '.*SIN.*','.*COS.*')

    if (isinstance(ancillary, ee.Image)):
        phaseAmp = phaseAmp.addBands(ancillary)


    # Add phase, amplitude, and ancillary
    bands = bands.addBands([phaseAmp]).select(predictors)

    # Remove non-inputs
    inputFeatures = bands.bandNames() \
    .removeAll(['tStart','tEnd','tBreak','changeProb',
    'BLUE_MAG','GREEN_MAG','RED_MAG','NIR_MAG','SWIR1_MAG','SWIR2_MAG','TEMP_MAG'])

    return [inputFeatures, bands]



def makePhaseAmp(img, bandNames):

    suffixList = ['','_1','_2']

    phaseAmp1 = newPhaseAmplitude(img, bandNames, '_SIN', '_COS')

    def func_cnt(b):
        return ee.String(b)

    bns = phaseAmp1.bandNames().map(func_cnt)


    phaseAmp1 = phaseAmp1.rename(bns)

    phaseAmp2 = newPhaseAmplitude(img, bandNames, '_SIN2', '_COS2')

    def func_zya(b):
        return ee.String(b).cat('_1')

    bns = phaseAmp2.bandNames().map(func_zya)


    phaseAmp1 = phaseAmp2.rename(bns)

    phaseAmp3 = newPhaseAmplitude(img, bandNames, '_SIN3', '_COS3')

    def func_nus(b):
        return ee.String(b).cat('_2')

    bns = phaseAmp3.bandNames().map(func_nus)


    phaseAmp3 = phaseAmp3.rename(bns)

    return ee.Image.cat([phaseAmp1, phaseAmp2, phaseAmp3])



def subsetTraining(trainingData, trainProp, seed, classProperty):
    classCounts = ee.Dictionary(trainingData.aggregate_histogram(classProperty))
    classes = classCounts.keys()

    def func_uia(c):
        subset = trainingData.filterMetadata(classProperty, 'equals',ee.Number.parse(c))
        
        # Withhold a selection of training data
        trainingSubsetWithRandom = subset.randomColumn('random',seed).sort('random')
        indexOfSplit = trainingSubsetWithRandom.size().multiply(trainProp).int32()
        numberOfTrain = trainingSubsetWithRandom.size().subtract(indexOfSplit).int32()
        
        def func_lax(feat):
            return feat.set('train', 0)
        
        subsetTest = ee.FeatureCollection(trainingSubsetWithRandom.toList(indexOfSplit)) \
        .map(func_lax)
        def func_mbq(feat):
            return feat.set('train', 1)
        
        subsetTrain = ee.FeatureCollection(trainingSubsetWithRandom.toList(numberOfTrain, indexOfSplit)) \
        .map(func_mbq)
        def func_bmz(feat):
            return feat.set('train', 1)
        
        return ee.Algorithms.If(subset.size().gt(10),
        subsetTest.merge(subsetTrain),
        subset.map(func_bmz)
        )

    subsets = classes.map(func_uia)
    return ee.FeatureCollection(subsets).flatten()
  


def accuracyProcedure(trainingData, imageToClassify, predictors, bandNames, ancillary, classifier, classProperty, seed, trainProp):
    trainProp =  .4
    seed =  seed or math.ceil(math.random() * 1000)
    classProperty = 'LC_Num'
    trainingData = trainingData.randomColumn('random',seed).sort('random')
    trainingData = subsetTraining(trainingData, trainProp, seed, classProperty)
    testSubsetTest = trainingData.filterMetadata('train','equals',0)

    testSubsetTrain = trainingData.filterMetadata('train','equals',1)

    inputList = getInputFeatures(1, imageToClassify, predictors, bandNames, ancillary)
    inputFeatures = ee.List(inputList).get(0)

    # inputFeatures = inputList[0]

    # Train the classifier
    trained = classifier.train(
    features=testSubsetTrain,
    classProperty=classProperty,
    inputProperties=inputFeatures
    )
    classified = testSubsetTest.classify(trained)
    confMatrix = classified.errorMatrix(classProperty, 'classification')
    # return [confMatrix, trained]
    return confMatrix




def classifyCoefs(imageToClassify, bandNames, ancillary, ancillaryFeatures, trainingData, classifier, studyArea, classProperty, coefs, trainProp, seed):
    trainProp = trainProp or None
    studyArea = studyArea or None
    trainingData = ee.FeatureCollection(trainingData)
    imageToClassify = ee.Image(imageToClassify)
    # print(imageToClassify.getInfo())
    # Subset training data to studyarea if specified
    if (studyArea):
            trainingData = trainingData.filterBounds(studyArea)

        # Test withholding subset of data and classifying
    if (trainProp):
            confMatrix = accuracyProcedure(trainingData, seed, trainProp)

    # Prector names selected for classification.
    def func_jqq(b):

        def func_xkx(i):
                return ee.String(b).cat('_').cat(i)

        return ee.List(coefs).map(func_xkx)



    predictors = ee.List(bandNames).map(func_jqq)


    # Train the classifier
    trained = classifier.train(**{
        'features': trainingData,
        'classProperty': classProperty,
        'inputProperties': predictors
        })

    bands = imageToClassify.addBands(ancillary)
    classified =  bands.select(predictors) \
    .classify(trained) \
    .int()

    return classified




def classifySegments(imageToClassify, numberOfSegments, bandNames, ancillary, ancillaryFeatures, trainingData, classifier, studyArea, classProperty, coefs, trainProp, seed, subsetTraining):
    trainProp = trainProp or None
    studyArea = studyArea or None
    # subsetTraining = subsetTraining or None
    trainingData = ee.FeatureCollection(trainingData)
    imageToClassify = ee.Image(imageToClassify)

    # Subset training data to studyarea if specified
    if (studyArea and subsetTraining != False):
            trainingData = trainingData.filterBounds(studyArea)
    else:
            trainingData = trainingData
        # Test withholding subset of data and classifying
    if (trainProp):
            confMatrix = accuracyProcedure(trainingData, seed, trainProp)


        # Input bands. All data will be initially queries and only these bands
        # will be eventually selected for classification.

    def func_zbb(b):

        def func_hkg(i):
                return ee.String(b).cat('_').cat(i)

        return ee.List(coefs).map(func_hkg)



    predictors = ee.List(bandNames).map(func_zbb)

    inputList = getInputFeatures(1, imageToClassify, predictors, bandNames, ancillary)
    inputFeatures = inputList[0]





        # Train the classifier
    trained = classifier.train(
        features=trainingData,
        classProperty=classProperty,
        inputProperties=inputFeatures
        )

    # Map over segments
    def func_gur(seg):

        # Get inputs bands for this segment # ERIC HERE
        inputList = getInputFeatures(seg, imageToClassify, predictors, bandNames, ancillary)
        inputFeatures = inputList[0]
        bands = inputList[1]
        segStr = ee.String('S').cat(ee.String(ee.Number(seg).int8()))
        className = segStr.cat('_classification')
        startName = segStr.cat('_tStart')
        tEnd = segStr.cat('_tEnd')

        return bands \
        .select(inputFeatures) \
        .classify(trained) \
        .updateMask(imageToClassify.select(startName).neq(0)) \
        .rename([className]) \
        .int()

    segmentsClassified = ee.List.sequence(1, numberOfSegments).map(func_gur)


    # segmentsClassified is returned as a list so first convert to Collection
    classified = ee.ImageCollection(segmentsClassified)

    # When reducing to bands the names change and gives an error upon export
    def func_nrb(i):
        return i.set('bn', i.bandNames())

    bns = ee.List(classified \
    .map(func_nrb) \
    .aggregate_array('bn')) \
    .flatten()

    # Reduce to bands and rename to original band names
    classified = classified.toBands().rename(bns)
    return classified



def parseConfMatrix(im, attribute):
    attribute = attribute or 'confMatrix'
    # Parse confusion matrix
    conf = ee.String(im.get(attribute))
    conf = conf.slice(1).slice(0, -2)

    def func_uzq(list):

        def func_azw(str):
                return ee.Number.parse(str)

        return ee.String(list).slice(1).split(',').map(func_azw)



    split = conf.split('],').map(func_uzq)

    confMatrix = ee.ConfusionMatrix(ee.Array(split))

    users = confMatrix.consumersAccuracy().project([1]).toList()

    def func_ipk(num):
        return ee.String(ee.Number(num).int8())

    keys = ee.List.sequence(0, users.length().subtract(1)).map(func_ipk)



    def func_gvz(key):
        return (ee.String('users_class_').cat(key))

    names = keys.map(func_gvz)


    usersDict = ee.Dictionary.fromLists(names, users)

    producers = confMatrix.producersAccuracy().project([0]).toList()

    def func_min(num):
        return ee.String(ee.Number(num).int8())

    keys = ee.List.sequence(0, users.length().subtract(1)).map(func_min)



    def func_rem(key):
        return (ee.String('producers_class_').cat(key))

    names = keys.map(func_rem)


    producersDict = ee.Dictionary.fromLists(names, producers)
    im = im.setMulti(producersDict.combine(usersDict))

    return im



def getLcAtDate(segs, date, numberOfSegments, ccdVersion, metadataFilter, behavior, bandNames, inputFeatures, specImage, dateFormat):

    segs = ee.Image(segs)
    # Hard code for now
    bandNames = bandNames or ["BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP"]
    inputFeatures = inputFeatures or ["INTP", "SLP","PHASE","AMPLITUDE","COS","SIN","COS2","SIN2"]
    numberOfSegments = numberOfSegments or ee.Image(segs).bandNames().length()
    ccdVersion = ccdVersion or 'v2'
    metadataFilter = metadataFilter or 'z'
    behavior = behavior or 'after'

    if (dateFormat == 0):
        dateFormat = 0
    if (dateFormat > 0):
        dateFormat = dateFormat
    else:
        dateFormat = 1
    # dateFormat = (dateFormat && dateFormat == 0) or 1

    # CCDC Collection and 'system:index' metadata ftilter
    ccdcCollection = ee.ImageCollection("projects/CCDC/" + ccdVersion)

    # Get CCDC coefficients
    ccdcCollectionFiltered = ccdcCollection \
    .filterMetadata('system:index', 'starts_with',metadataFilter)

    # CCDC mosaic image
    ccdc = ccdcCollectionFiltered.mosaic()

    # Turn array image into image
    specImage = specImage or ccdcUtils.buildCcdImage(ccdc, numberOfSegments, bandNames)

    tStarts = specImage.select('.*tStart')

    tEnds = specImage.select('.*tEnd')

    dateFormatted = dateUtils.convertDate(
    inputFormat=3,
    inputDate=date,
    outputFormat=dateFormat
    )

    if (behavior == 'before'):
        dateMask = tStarts.lt(dateFormatted)
        matchingDate =  segs.updateMask(dateMask).reduce(ee.Reducer.lastNonNull())
    if (behavior == 'after'):
        dateMask = tEnds.gt(dateFormatted)
        matchingDate =  segs.updateMask(dateMask).reduce(ee.Reducer.firstNonNull())
    else:
        dateMask = tStarts.lt(dateFormatted).And(tEnds.gt(dateFormatted))
        matchingDate =  segs.updateMask(dateMask).reduce(ee.Reducer.firstNonNull())

    return matchingDate



def getMode(folder, matchingString):

    list = ee.data.getList({'id': folder})
    ims = []

    for i in range(0, list.length):
        id = list[i]['id']
    if id.indexOf(matchingString) != -1:
            im = ee.Image(id)
            ims.push(im)


    return  ee.ImageCollection(ims).reduce(ee.Reducer.mode())


def getInputDict(bandNames, inputFeatures, ancillaryFeatures):

    # Which inputs were used
    allPossibleInputs = ["B1","B2","B3","B4","B5","B6","B7",
    "BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP", "INTP",
    "AMPLITUDE", "PHASE", "AMPLITUDE_1", "PHASE_1","AMPLITUDE_2",
    "PHASE_2", "SLP","COS", "SIN","COS2", "SIN2", "COS3","SIN3",
    "RMSE","ELEVATION","ASPECT","DEM_SLOPE","RAINFALL","TEMPERATURE",
    "AMPLITUDE2", "PHASE2","AMPLITUDE3",
    "PHASE3","WATER_OCCURRENCE","POPULATION", "TREE_COVER"]
    allActualInputs = bandNames+inputFeatures+ancillaryFeatures

    # Get dictionary with True or False for each input

    def func_lus(inp):
        return allActualInputs.index(inp) > 0

    inputBooleans = allPossibleInputs.map(func_lus)


    inputDict = ee.Dictionary.fromLists(allPossibleInputs, inputBooleans)

    def func_jxb(b):

        def func_gsm(i):
                return ee.String(b).cat('_').cat(i)

        return ee.List(inputFeatures).map(func_gsm)



    predictors = ee.List(bandNames).map(func_jxb) \
        .flatten().cat(ancillaryFeatures)

    return [inputDict, predictors]








def func_unp(bandNames, inputFeatures, ancillaryFeatures):

    def func_pes(b):

            def func_qfe(i):
                        return ee.String(b).cat('_').cat(i)

            return ee.List(inputFeatures).map(func_qfe)


    return ee.List(bandNames).map(func_pes) \
        .flatten().cat(ancillaryFeatures)


getPredictors = func_unp


def loadResults(resultFormat,changeResults, studyRegion, segs, bandNames):
    if (resultFormat == 'SegImage'):
        ccdImage =  ee.Image(changeResults)
    elif (resultFormat == 'SegCollection'):
        ccdImage = ee.ImageCollection(changeResults) \
        .filterBounds(studyRegion).mosaic()
    else:
        coefImage = ee.ImageCollection(changeResults) \
        .filterBounds(studyRegion).mosaic()
        ccdImage = utils.CCDC.buildCcdImage(
        coefImage, segs.length, bandNames)
    
    return ccdImage



def func_ukm(img, date):
        dateClassificationAfter = getLcAtDate(
        img,
        date,
        None,
        None,
        None,
        'after',
        None,
        None,
        None,
        1
        )

        dateClassificationBefore = getLcAtDate(
        img,
        date,
        None,
        None,
        None,
        'before',
        None,
        None,
        None,
        1
        )

        dateClassification = ee.Image.cat(
        [
        dateClassificationAfter,
        dateClassificationBefore,
        ]
        ) \
        .reduce(
        ee.Reducer.firstNonNull()
        )

        return dateClassification.rename([ee.String(date)])

getLC = func_ukm








































def makeYearlyMaps(results, years, month, day):
        years = years or ee.List.sequence(2000, 2020)
        month = month or 6
        day = day or 1


        def func_jqs(y):
                p1 = ee.String(ee.Number(y).int())
                p2 = ee.String('-')
                p3 = ee.String(ee.Number(month).int())
                p4 = ee.String(ee.Number(day).int())
                return p1.cat(p2).cat(p3).cat(p2).cat(p4)
                return ee.String(y)

        formatted = years.map(func_jqs)









        def func_ffo(y):

                lcImage = getLC(results, y) \
                .rename('lc')

                return lcImage


        ims = ee.List(formatted).map(func_ffo)









        return ee.List(ims)

def simpleClassification(fc, atts, prop, classifier):
  atts = atts or fc.first().propertyNames().removeAll([
    'ID','Start_Year','dataPath','End_Year','Level1_Ecoregion', 'landcover',
    'Dataset','system:index','LC_Class','Continent_Code','Glance_Class_ID_level1','Glance_Class_ID_level2',
    'Level1_Ecoregion','Level2_Ecoregion','Dataset_Code','Continent','Middle_Year','trainYear'])
  classifier = classifier or ee.Classifier.smileRandomForest(200)
  prop = prop or 'Glance_Class_ID_level1'
  
  ancillaryFeatures = ["ELEVATION","ASPECT","DEM_SLOPE","RAINFALL","POPULATION","WATER_OCCURRENCE"]
  ancillary = inputUtils.getAncillary()
  bandNames = ["BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP"]
  coefs =["INTP", "SLP","COS", "SIN","RMSE","COS2","SIN2","COS3","SIN3"]
  
  ccdcCollectionFiltered = ee.ImageCollection("projects/CCDC/v2") \
    .filterMetadata('system:index', 'starts_with',"z_") \
    .mosaic()
  ccdImage = ccdcUtils.buildCcdImage(ccdcCollectionFiltered, 1, bandNames)

  def func_kuq(b):
    def func_jhe(i):
      return ee.String(b).cat('_').cat(i)

    return ee.List(coefs).map(func_jhe)

  predictors = ee.List(bandNames).map(func_kuq) \
    .flatten().cat(ancillaryFeatures)

  
  inputList = ee.List(getInputFeatures(1, ccdImage, predictors, bandNames, ancillary))
  inputFeatures = ee.List(inputList.get(0))
  imageToClassify = ee.Image(inputList.get(1))

  # Train the classifier
  trained = classifier.train(**{
    'features': fc,
    'classProperty': prop,
    'inputProperties': inputFeatures
  })
  return imageToClassify.classify(trained)
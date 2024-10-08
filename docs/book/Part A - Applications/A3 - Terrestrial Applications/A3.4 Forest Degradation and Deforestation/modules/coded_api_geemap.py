import ee 
import geemap
from datetime import date

m = geemap.Map()

geometry = ee.Geometry.Point([-48.735319871564464, -3.9349915957792634])
lc8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
geometry2 = ee.Geometry.Point([178.06640625805346, -17.970112199227554])
geometry3 = \
    ee.Geometry.Polygon(
        [[[-48.02972284125171, -2.2204248963007274],
          [-48.02972284125171, -2.5991173403443737],
          [-47.54083123968921, -2.5991173403443737],
          [-47.54083123968921, -2.2204248963007274]]], None, False)
geometry4 = ee.Geometry.MultiPoint()

from ccdcUtilities import api_geemap as utils

def parameters():
    endmembers = {
        'gv': [.0500, .0900, .0400, .6100, .3000, .1000],
        'shade': [0, 0, 0, 0, 0, 0],
        'npv': [.1400, .1700, .2200, .3000, .5500, .3000],
        'soil': [.2000, .3000, .3400, .5800, .6000, .5800],
        'cloud': [.9000, .9600, .8000, .7800, .7200, .6500],
    }
    cloudThreshold = .1

PARAMETERS = {
    'endmembers': {
            'gv': [.0500, .0900, .0400, .6100, .3000, .1000],
            'shade': [0, 0, 0, 0, 0, 0],
            'npv': [.1400, .1700, .2200, .3000, .5500, .3000],
            'soil': [.2000, .3000, .3400, .5800, .6000, .5800],
            'cloud': [.9000, .9600, .8000, .7800, .7200, .6500],
        },
    'cloudThreshold': .1
}


def unmix(image, endmembers, cloudThreshold):
    endmembers = endmembers or PARAMETERS['endmembers']
    cloudThreshold = cloudThreshold or PARAMETERS['cloudThreshold']

    cfThreshold = ee.Image.constant(cloudThreshold)

    unmixImage = ee.Image(image).unmix(
    [endmembers.gv, endmembers.shade, endmembers.npv, endmembers.soil, endmembers.cloud], True,True) \
    .rename(['band_0', 'band_1', 'band_2','band_3','band_4'])

    imageWithFractions = ee.Image(image).addBands(unmixImage)

    cloudMask = imageWithFractions.select('band_4').lt(cfThreshold)

    ndfi = unmixImage.expression(
    '((GV / (1 - SHADE)) - (NPV + SOIL)) / ((GV / (1 - SHADE)) + NPV + SOIL)', {
        'GV': ee.Image(unmixImage).select('band_0'),
        'SHADE': ee.Image(unmixImage).select('band_1'),
        'NPV': ee.Image(unmixImage).select('band_2'),
    'SOIL': ee.Image(unmixImage).select('band_3')})

    return imageWithFractions.addBands(ndfi.rename(['NDFI'])) \
    .select(['band_0','band_1','band_2','band_3','NDFI']).rename(['GV','Shade','NPV','Soil','NDFI']) \
    .updateMask(cloudMask)



# Temperate forest mask
biomes = ee.Image("OpenLandMap/PNV/PNV_BIOME-TYPE_BIOME00K_C/v01")
temperate = biomes.gt(3)


def func_uff(image):

    tropicEndmembers = {
            'gv': [.0500, .0900, .0400, .6100, .3000, .1000],
            'shade': [0, 0, 0, 0, 0, 0],
            'npv': [.1400, .1700, .2200, .3000, .5500, .3000],
            'soil': [.2000, .3000, .3400, .5800, .6000, .5800],
            'cloud': [.9000, .9600, .8000, .7800, .7200, .6500],
        }


    temperateEndmembers = {
            'gv': [.0264, .0832, .0338, .4931, .1841, .0754],
            'shade': [0, 0, 0, 0, 0, 0],
            'npv': [.0192, .0476, .0929, .3007, .2613, .1243],
            'soil': [.0803, .1199, .1414, .2094, .3134, .2487],
            'cloud': [.1678, .1986, .1884, .4518, .3404, .2148],
        }

    tropicFractions = unmix(image, tropicEndmembers)
    temperateFractions = unmix(image, temperateEndmembers)

    return tropicFractions.where(temperate, temperateFractions)


prepInputForestTypes = func_uff



def func_ptn(img, thresholds):


    thresholds = thresholds or {
            'data': -2,
            'gvShadeForest': .85,
            'gvShadeNonForest': .5,
            'npvSoilNonForest': .15,
            'gvNonForest': .85,
            'ndfiForest': .6 
        }

    # More deg: ndfiForest ^
    # Less deg: ndfiForest v
    # More def: gvNonForest v
    # Less def: gvNonForest ^
    #   or:
    #      More def: gvShadeForest ^ (more decision 2 = 0)

    # Calculate GV Shade
    GVshade_num = img.select('GV')
    GVshade_den = ee.Image(1).subtract(img.select('Shade'))
    GVshade = GVshade_num.divide(GVshade_den)

    decision1 = img.select("GV").gt(thresholds.data)
    decision2 = GVshade.gt(thresholds.gvShadeForest)
    decision3 = GVshade.lt(thresholds.gvShadeNonForest)
    decision4 = img.select('NPV').add(img.select('Soil')).gt(thresholds.npvSoilNonForest)
    decision5 = img.select('GV').gt(thresholds.gvNonForest)
    decision6 = img.select('NDFI').gt(thresholds.ndfiForest)
    # decision7 = forestMask

    forest = decision1.And(
    decision2.And(decision5.eq(0)).And(
    decision6)).selfMask()

    degradation = decision1.And(
    decision2.And(decision5.eq(0)).And(
    decision6.eq(0))).multiply(4).selfMask()

    nonForest = decision1.And(
    decision2.And(decision5).Or(
    decision2.eq(0).And(decision3)).Or(
    decision2.eq(0).And(decision3.eq(0).And(decision4)))).selfMask()

    return forest.addBands([degradation, nonForest]).rename(['Forest','Degradation','NonForest'])


decisionTree = func_ptn



def func_kng(geo, start, end, treeCover, numPoints, mask):

    # Make forest non/forest mask
    gfwImage = ee.Image("UMD/hansen/global_forest_change_2019_v1_7").clip(geo)

    # Get areas of forest cover above threshold
    gfwMask = gfwImage.select('treecover2000').gte(treeCover)

    # Convert loss year to year format
    year = gfwImage.select('lossyear').add(2000)

    # Case 1: No loss
    case1 = gfwMask.And(gfwImage.select('loss').eq(0))

    # Case 2: Loss after start
    case2 = gfwMask.And(year.unmask().gt(end))

    # Mask is either case 1 or or case 2
    yearMask = case1.Or(case2)

    # Apply mask using multiplication to avoid no-data values
    gfwMask = gfwMask.multiply(yearMask).remap([0,1],[2,1]) \
    .updateMask(gfwImage.select('datamask').eq(1))

    if (mask):
            gfwMask = gfwMask.updateMask(mask)

    # m.addLayer(gfwMask.randomVisualizer(), {}, 'Forest Mask')
    # Make sample
    sample = gfwMask.rename('landcover').stratifiedSample(
        numPoints=numPoints,
        scale=30,
        region=geo,
        geometries=True,
        tileScale=4
        )
    results = {
            'mask': gfwMask,
            'sample': sample
        }

    return results

getTrainingFromHansen = func_kng



def func_hnn(params):

    # ------------------ Check Inputs
    if (not params):
            print('Missing parameter object')
            return


    # ------------------ Parse Parameters

    # Random Parameters
    generalParams = {}
    generalParams['segs'] = params['segs'] or ['S1','S2','S3','S4','S5']
    generalParams['classBands'] = params['classBands'] or utils.Inputs.getLandsat().filterBounds(generalParams.studyArea).first().bandNames().getInfo()
    generalParams['coefs'] = params['coefs'] or ['INTP','SIN','COS','RMSE','SLP']
    generalParams['forestValue'] = params['forestValue'] or 1
    generalParams['studyArea'] = params['studyArea'] or ee.Geometry(m.getBounds(True))
    generalParams['mask'] = params['forestMask'] 
    generalParams['landsatCollection'] = params['landsatCollection'] or 1

    # CODED Change Detection Parameters
    changeDetectionParams = {}
    changeDetectionParams['collection'] = params['collection'] or utils.Inputs.getLandsat({'collection': generalParams['landsatCollection']})


    changeDetectionParams['breakpointBands'] = params['breakpointBands'] or ['NDFI']

    # generalParams['allBands'] = generalParams.classBands+changeDetectionParams.breakpointBands

    changeDetectionParams['collection'] = changeDetectionParams['collection'] \
    .filterBounds(generalParams.studyArea).select(generalParams.classBands)

    changeDetectionParams['lambda'] = params['lambda'] or 20/10000
    changeDetectionParams['minNumOfYearsScaler'] = params['minNumOfYearsScaler'] or 1.33
    changeDetectionParams['dateFormat'] = 1
    changeDetectionParams['minObservations'] = params['minObservations'] or 3
    changeDetectionParams['chiSquareProbability'] = params['chiSquareProbability'] or .9

    # Classification Parameter
    classParams = {}
    classParams['imageToClassify'] = None
    classParams['numberOfSegments'] = generalParams.segs.__len__()
    classParams['bandNames'] =  generalParams.classBands
    classParams['ancillary'] = None
    classParams['ancillaryFeatures'] = None
    classParams['trainingData'] = None
    classParams['classifier'] = ee.Classifier.smileRandomForest(150)
    classParams['studyArea'] = generalParams['studyArea']
    classParams['classProperty'] = 'landcover'
    classParams['coefs'] = ['INTP','SIN','COS','RMSE']
    classParams['trainProp'] = None
    classParams['seed'] = None
    classParams['subsetTraining'] = False

    # Output Dictionary
    output = {}
    output['Change_Parameters'] = changeDetectionParams
    output['General_Parameters'] = generalParams
    output['Layers'] = {}

    if (params['forestMask']):
            output.Layers['mask'] = params['forestMask'].eq(params['forestValue'])


    # Some random editing of parameters

    def func_dja(img):
            return img.set('year', img.date().get('year'))

    dates = changeDetectionParams['collection'].filterBounds(generalParams['studyArea']).map(func_dja)


    generalParams['startYear'] = params['startYear'] or dates.aggregate_min('year')
    generalParams['endYear'] = params['endYear'] or  dates.aggregate_max('year')


    # ----------------- Run Analysis

    # Run CCDC/CODED
    output.Layers['rawChangeOutput'] = ee.Algorithms.TemporalSegmentation.Ccdc(changeDetectionParams)
    output.Layers['formattedChangeOutput'] = utils.CCDC.buildCcdImage(output.Layers.rawChangeOutput, generalParams.segs.__len__(), generalParams.classBands)
    # prepTraining = True
    if (params['prepTraining']):

            # Get training data coefficients

            def func_wqm(feat):
                    coefsForTraining = utils.CCDC.getMultiCoefs(output.Layers.formattedChangeOutput, ee.Image.constant(feat.getNumber('year')), 
                    generalParams.classBands, generalParams.coefs, True, generalParams.segs, 'before')

                    sampleForTraining = feat.setMulti(coefsForTraining.reduceRegion(
                            geometry=feat.geometry(),
                            scale=30,
                            reducer=ee.Reducer.mean(),
                            tileScale=4
                            ))
                    return sampleForTraining

            sampleForTraining = ee.FeatureCollection(params['training'].map(func_wqm










            )).filter(ee.Filter.notNull(['NDFI_INTP']))

            # print('Sample for training: ', sampleForTraining.first().getInfo())
            if (params['outId']):
                outId = params['outId']
            else:
                outId = 'sample_with_pred'
                        
            geemap.ee_export_vector_to_asset(
                collection=sampleForTraining,
                description='sample_with_pred',
                assetId=outId
                )

    else:
            sampleForTraining = params['training']
    # print(sampleForTraining.getInfo())

    # Format classification parameters and extract values  
    classParams['imageToClassify'] = output.Layers['formattedChangeOutput']
    classParams['trainingData'] = sampleForTraining
    def func_keyMap(key): return classParams[key]
    vals = classParams.keys().map(func_keyMap)

    # Run classification
    output.Layers['classificationRaw'] = utils.Classification.classifySegments.apply(None, vals)

    if (not output.Layers.mask):
        output.Layers.mask = output.Layers['classificationRaw'].select(0).eq(generalParams.forestValue)


    # Keep only negative NDFI breaks
    tMags = output.Layers['formattedChangeOutput'].select('.*NDFI_MAG').lt(0) \
    .select(ee.List.sequence(0, generalParams.segs.__len__() - 2)) 

    factor = ee.Image(1).addBands(tMags)
    output.Layers['classificationRaw'] = output.Layers['classificationRaw'].multiply(factor).selfMask()

    output.Layers['classification'] = output.Layers['classificationRaw'] \
    .select(ee.List.sequence(1, generalParams.segs.__len__() - 1)) \
    .int8()

    output.Layers['classification'] = output.Layers['classification'].updateMask(output.Layers.mask)
    output.Layers['magnitude'] = output.Layers['formattedChangeOutput'].select('.*NDFI_MAG')

    # ----------------- Post-process


    tBreaks = output.Layers['formattedChangeOutput'].select('.*tBreak').select(ee.List.sequence(0, generalParams.segs.__len__() - 2))
    tBreaksInterval = tBreaks.floor().gte(generalParams['startYear']).And(tBreaks.floor().lte(generalParams['endYear']))
    output.Layers['classificationStudyPeriod'] =  output.Layers['classification'].updateMask(tBreaksInterval)

    deg = output.Layers['classificationStudyPeriod'].eq(generalParams['forestValue']).reduce(ee.Reducer.max()).rename('Degradation')
    vDef = output.Layers['classificationStudyPeriod'].neq(generalParams['forestValue']).reduce(ee.Reducer.max()).rename('Deforestation')
    both = deg.And(vDef)

    output.Layers['Degradation'] = deg.And(both.Not()).selfMask().int8()
    output.Layers['Deforestation'] = vDef.And(both.Not()).selfMask().int8()
    output.Layers['Both'] = both.selfMask().int8()

    # dateOfDegradation = output.Layers['classificationStudyPeriod'].eq(generalParams['forestValue']).multiply(tBreaks).multiply(tBreaksInterval)
    # dateOfDeforestation = output.Layers['classificationStudyPeriod'].neq(generalParams['forestValue']).multiply(tBreaks).multiply(tBreaksInterval)
    dateOfDegradation = output.Layers['classificationStudyPeriod'] \
    .eq(generalParams['forestValue']) \
    .multiply(tBreaks) \
    .multiply(tBreaksInterval)

    dateOfDeforestation = output.Layers['classificationStudyPeriod'] \
    .neq(generalParams['forestValue']) \
    .multiply(tBreaks) \
    .multiply(tBreaksInterval)

    output.Layers['DatesOfDegradation'] = dateOfDegradation
    output.Layers['DatesOfDeforestation'] = dateOfDeforestation

    # 4-25-2022 Seperate magnitude by degradation and deforestation
    degMagBands = []
    defMagBands = []
    magIndices = []
    for i in range(1, generalParams.segs.__len__(), 1):
            degMagBands.push('DegradationMagnitude_' + i)
            defMagBands.push('DeforestationMagnitude_' + i)
            magIndices.push(i-1)

    degIndices = output.Layers['classificationStudyPeriod'] \
    .eq(generalParams['forestValue'])

    defIndices = output.Layers['classificationStudyPeriod'] \
    .neq(generalParams['forestValue'])

    magOfDegradation = output.Layers['magnitude'].select(magIndices) \
    .multiply(degIndices) \
    .rename(degMagBands)

    magOfDeforestation = output.Layers['magnitude'].select(magIndices) \
    .multiply(defIndices) \
    .rename(defMagBands)

    output.Layers['MagnitudeOfDegradation'] = magOfDegradation
    output.Layers['MagnitudeOfDeforestation'] = magOfDeforestation

    # Make single layer stratification
    stratification = output.Layers.mask.remap([0,1],[2,1]) \
    .where(output.Layers['Degradation'], 3) \
    .where(output.Layers['Deforestation'], 4) \
    .where(output.Layers['Both'], 5)

    output.Layers['Stratification'] = stratification.rename('stratification').int8()

    # Turn no data to non-forest
    stratificationNoData = output.Layers['Stratification'].mask().eq(0)
    stratificationGeo = output.Layers['Stratification'].geometry()
    output.Layers['Stratification'] = output.Layers['Stratification'].unmask().where(stratificationNoData, 2).clip(stratificationGeo)

    # Mask with forest mask
    return output

coded = func_hnn



def parameterization(training, testing, collection, chi2s, consecs, prepTraining, 
  forestMask, exportEach):

    listOfFeats = []


    for chi_index in range(0,chi2s.__len__()):
        chi = chi2s[chi_index]
        for consec_index in range(0, consecs.__len__()):

            # ------------- Set up parameters
            params = {
                'minObservations': consecs[consec_index], 
                'chiSquareProbability': chi,
                'training': training,
                'studyArea': training.geometry().bounds(),
                'forestValue': 1,
                'forestMask': forestMask,
                'classBands': ['NDFI','GV','Shade','NPV','Soil'],
                'collection':  collection,
                'startYear': 1994,
                'endYear': 2017,
                'prepTraining': prepTraining
            }


            # -------------- Run CODED
            results = coded(params)
            classification = results.Layers['classificationStudyPeriod']
            stratification = results.Layers['Stratification']

            # -------------- Extract results at samples
            testingResults = stratification.sampleRegions(
            collection=testing,
            scale=30,
            geometries=False,
            tileScale=16
            )
            confusionMatrix = testingResults.errorMatrix('reference','stratification')

            users = confusionMatrix.consumersAccuracy()
            users_forest = users.get([0, 1])
            users_nonforest = users.get([0, 2])
            users_deg = users.get([0, 3])
            users_def = users.get([0, 4])
            users_both = users.get([0, 5])

            producers = confusionMatrix.producersAccuracy()
            producers_forest = producers.get([1, 0])
            producers_nonforest = producers.get([2, 0])
            producers_deg = producers.get([3, 0])
            producers_def = producers.get([4, 0])
            producers_both = producers.get([5, 0])


            # -------------- Do it again for change only
            testingResults2 = stratification.remap([1,2,3,4,5],[1,2,3,3,3]).rename('stratification').sampleRegions(
            collection=testing.remap([1,2,3,4,5],[1,2,3,3,3],'reference'),
            scale=30,
            geometries=False,
            tileScale=16
            )
            confusionMatrix2 = testingResults2.errorMatrix('reference','stratification')

            users2 = confusionMatrix2.consumersAccuracy()
            users_change = users2.get([0, 3])

            producers2 = confusionMatrix2.producersAccuracy()
            producers_change = producers2.get([3, 0])


            # ----------- Save
            outParams = {
                'minObservations': consecs[consec_index],
                'chiSquareProbability': chi,
                'users_forest': users_forest,
                'users_nonforest': users_nonforest,
                'users_deg': users_deg,
                'users_def': users_def,
                'users_both': users_both,
                'users_change': users_change,
                'producers_forest': producers_forest,
                'producers_nonforest': producers_nonforest,
                'producers_deg': producers_deg,
                'producers_def': producers_def,
                'producers_both': producers_both,
                'producers_change': producers_change
            }

            outGeo = training.first().geometry()
            outFeat = ee.Feature(outGeo).setMulti(outParams)
            listOfFeats.push(outFeat)
            if (exportEach):
                geemap.ee_export_vector_to_asset(
                collection=ee.FeatureCollection([outFeat,outFeat]),
                description='parameter_testing_point',
                assetId='amazon/results_2021/parameters_' + chi_index + '_' + consec_index
                )

    return ee.FeatureCollection(listOfFeats)




def func_pzd(fc, attribute, value, count):
    return ee.FeatureCollection(fc.filterMetadata(attribute, 'equals',value).toList(count))

subsetFC = func_pzd






def func_hej():


    trainingAmazon = ee.FeatureCollection('users/bullocke/amazon/results_2021/training_coefs_2010')

    # def func_uhk(feat): return feat.set('landcover',feat.getNumber('label'))
    # .map(function(feat) {return feat.set('landcover',feat.getNumber('label'))}
    # .map(func_uhk)

    referenceAmazon = ee.FeatureCollection('users/bullocke/amazon/public/reference_sample_final') \
    .remap([1,2,3,4,5,6],[1,2,4,3,5,6],'reference')

    parameterTesting = parameterization(
    trainingAmazon,
    referenceAmazon,
    utils.Inputs.getLandsat().filterDate('2000-01-01','2020-01-01'),
    [.85, .9, .95, .99],
    [3, 4, 5, 6],
    False,
    None
    )
    print('Parameter Testing (First Feature)', parameterTesting.getInfo())
    currentdate = date.today()
    datetime = str(currentdate.day) + "_"
    + str(currentdate.month)  + "_"
    + str(currentdate.year) + "_"
    + currentdate.strftime('%H') + "_"
    + currentdate.strftime('%M') + "_"
    + currentdate.strftime('%S')

    geemap.ee_export_vector_to_asset(
        collection=parameterTesting,
        description='parameter_testing',
        assetId='codedExamples/parameters_' + datetime
        )


testParameters = func_hej







def func_zse(geo, start, end, layer):
    # geo = geometry3
    forestInfo = getTrainingFromHansen(geo, 2000, 2018, 80, 50)
    params = {
            'minObservations': 3,
            'chiSquareProbability': .87,
            'training': ee.FeatureCollection(forestInfo.sample),
            'studyArea': geo,
            'classBands': ['NDFI','GV','Shade','NPV','Soil'],
            'forestValue': 1,
            'forestMask': forestInfo.mask,
            'startYear': start or 2000,
            'endYear': end or 2019,
            'col': utils.Inputs.getLandsat().filterDate('2000-01-01','2020-01-01')
        }
    testOutput = coded(params)
    currentdate = date.today()
    datetime = str(currentdate.day) + "_"
    + str(currentdate.month)  + "_"
    + str(currentdate.year) + "_"
    + currentdate.strftime('%H') + "_"
    + currentdate.strftime('%M') + "_"
    + currentdate.strftime('%S')
    deg = ee.Image(testOutput.Layers['Degradation'])
    _def = ee.Image(testOutput.Layers['Deforestation'])
    both = ee.Image(testOutput.Layers['Both'])

    geemap.ee_export_image_to_asset(
        image=ee.Image(testOutput.Layers[layer]),
        scale=30,
        description='im',
        region='geometry3',
        maxPixels=1e13,
        assetId='codedExamples/coded_test_' + datetime
        )

fastCODED = func_zse














def func_ard(results, folder, geo, size, asset, prefix, min, max,startPrefix):
    startPrefix = startPrefix or 0
    size = size or .5

    if (asset):
            exportGrid = ee.FeatureCollection(asset)
    else:
            # m.addLayer(geo, {}, 'Export geo')
            exportGrid = utils.Inputs.makeAutoGrid(geo.bounds().buffer(1000000), size).filterBounds(geo)

            
            # Map.addLayer(geo, {}, 'Export geo')
            def func_lkp(f): return f.intersection(geo,1)

            exportGrid = utils.Inputs.makeAutoGrid(geo.bounds().buffer(1000000), size).filterBounds(geo) \
            .map(func_lkp)
            print('Export grids: ', exportGrid.size())

    m.addLayer(exportGrid, {}, 'Export grids')

    exportList = exportGrid.toList(1000)

    assetList = ee.data.listAssets(folder).assets
    if (assetList and assetList.__len__() > 0):
        def func_aat(i): return i.id
        folderAssets = assetList.map(func_aat)
    else:
        folderAssets = ['']

    def func_ncr(obj):
        for i in range(0, obj, 1):
            i_adj = i + startPrefix
            outName = folder + '/' + prefix + '_' + i_adj

            outGeo = ee.Feature(exportList.get(i)).geometry()
            if (i >= min and i <= max and folderAssets.indexOf(outName)):
                m.addLayer(outGeo, {}, 'task_' + i)
                geemap.ee_export_image_to_asset(
                    image=results,
                    scale=30,
                    pyramidingPolicy={
                        '.default':'mean'
                    },
                    description='task_' + i_adj,
                    assetId=outName,
                    region=outGeo,
                    maxPixels=1e13
                    )



    exportGrid.size().evaluate(func_ncr)



exportGrids = func_ard




def removeStorms(collection, storms, months):
    for i in range(0, storms.length):
        d = storms[i]
        startH = ee.Date(d)
        endH = startH.advance(months,'month')
        collection = collection.filter(ee.Filter.date(startH, endH).Not())
    return collection



def prepOutput(results, layers, numChanges, dateInt, maskProb,yearSubtract, flipMag, magFactor):
  # flipMag = flipMag || true
    yearSubtract = yearSubtract or 1990
    magFactor = magFactor or 10
  
    changeIndices = []
    outLayers = []
    for i in range(0,numChanges):
        changeIndices.push(i)

    degradation = results.Layers.DatesOfDegradation.rename(['degradation_1','degradation_2','degradation_3','degradation_4']).select(changeIndices)
    deforestation = results.Layers.DatesOfDeforestation.rename(['deforestation_1','deforestation_2','deforestation_3','deforestation_4']).select(changeIndices)
    if (dateInt):
        degradation = degradation.subtract(yearSubtract).int8()
        deforestation = deforestation.subtract(yearSubtract).int8()

    forestMask = results.Layers.mask.rename('mask').int8()
    magnitude = results.Layers.magnitude.select([0,1,2,3]).rename(['magnitude_1','magnitude_2','magnitude_3','magnitude_4']).select(changeIndices)
    magDegradation = results.Layers.MagnitudeOfDegradation.select(changeIndices)
    magDeforestation = results.Layers.MagnitudeOfDeforestation.select(changeIndices)

    if (flipMag):
        magnitude = magnitude.multiply(-1).multiply(magFactor).int8()
        magDegradation = magDegradation.multiply(-1).multiply(magFactor).int8()
        magDeforestation = magDeforestation.multiply(-1).multiply(magFactor).int8()

    else:
        magnitude = magnitude.multiply(magFactor).int8()
        magDegradation = magDegradation.multiply(magFactor).int8()
        magDeforestation = magDeforestation.multiply(magFactor).int8()

    probability = results.Layers.formattedChangeOutput.select('S.*_changeProb').select([0,1,2,3]).rename(['probability_1','probability_2','probability_3','probability_4']).select(changeIndices).int8()

    if (maskProb):
        degradation = degradation.updateMask(probability.eq(1))
        deforestation = deforestation.updateMask(probability.eq(1))



    stratification = results.Layers.Stratification
    classification = results.Layers.classification
    classificationRaw = results.Layers.classificationRaw
    classificationStudyPeriod = results.Layers.classificationStudyPeriod
    raw = results.Layers.rawChangeOutput

    if (layers.degradation):
        outLayers.push(degradation)

    if (layers.deforestation):
        outLayers.push(deforestation)

    if (layers.forestMask):
        outLayers.push(forestMask)

    if (layers.magnitude):
        outLayers.push(magnitude)

    if (layers.magnitudeDegradation):
        outLayers.push(magDegradation)

    if (layers.magnitudeDeforestation):
        outLayers.push(magDeforestation)

    if (layers.probability):
        outLayers.push(probability)

    if (layers.rawOutput):
        outLayers.push(raw)

    if (layers.stratification):
        outLayers.push(stratification)

    if (layers.classification):
        outLayers.push(classification)

    if (layers.classificationRaw):
        outLayers.push(classificationRaw)

    if (layers.classificationStudyPeriod):
        outLayers.push(classificationStudyPeriod)


    return ee.Image.cat(outLayers).selfMask()




#-------------------- Sentinel 1
composite = require("users/google/toolkits:landcover/impl/composites.js").Composites
slope_lib = require('users/andreasvollrath/radar:slope_correction_lib.js')
s1Lib = require('users/andreasvollrath/radar:s1Lib.js')
sarLib = require('users/andreasvollrath/radar:sarLib.js')





def func_wek(geo, params):

    #------------------- Parse parameters
    interval = params and params['interval'] or None 
    intervalSize = params and params['intervalSize'] or 2
    intervalCount = params and params['intervalCount'] or 1000
    kernelSize = params and params['kernelSize'] or 3
    reducer = params and params['reducer'] or ee.Reducer.mean()
    kernel = params and params['kernel'] or 'circle'
    start = params and params['start'] or '2014-01-01'
    end = params and params['end'] or '2021-01-01'
    correctionMethod = params and params['correctionMethod'] or 'None'
    rawPower = params and params['rawPower'] or None
    boxcar = params and params['boxcar'] or None
    lee = params and params['lee'] or None
    scaleFactor = params and params['scaleFactor'] or 30
    correctionMethod = ee.String(correctionMethod)
    bands = ['VH', 'VV', 'ratio']


    #------------------- Get S1 collection and filter by geometry
    s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .select(['V.','angle']) \
    .filterBounds(geo) \
    .filterDate(start, end)

    def func_uhx(img):
            geom = img.geometry()
            angle = img.select('angle')
            edge = img.select('VV').lt(-30.0); 
            ratio = img.select('VH').divide(img.select('VV')).rename('ratio').multiply(scaleFactor)
            return img.select('V.*').addBands(ratio).addBands(angle) \
    .map(func_uhx)







    #------------------- Optionally apply focal mean
    if (kernelSize and kernelSize > 1):

            def func_ugj(img):
                    fmean = img.focal_mean(kernelSize, kernel)
                    return img.select().addBands(fmean)


            s1 = s1.map(func_ugj)







    #------------------- Get dominant orbital pass
    passCount = ee.Dictionary(s1.aggregate_histogram('orbitProperties_pass'))
    passValues = passCount.values().sort().reverse()
    higherCount = passValues.get(0)
    orbitPass = passCount.keys().get(passCount.values().indexOf(higherCount))
    s1Pass = s1.filter(ee.Filter.eq('orbitProperties_pass', orbitPass))


    #------------------- Radiometric slope correction from Vollrath et al., 2020

    # Either do volume or slope correction method

    def func_njj(img):
            return img.addBands(img.select('VH').divide(img.select('VV')).rename('ratio').multiply(scaleFactor)) \
        .set('system:time_start',img.get('segmentStartTime')).set('cMethod','volume')
    volumeCorrected = slope_lib.slope_correction(s1Pass).map(func_njj)



    slopeParams = {
            'model': 'surface',
            'elevation': ee.Image('USGS/SRTMGL1_003'),
        'buffer': 75}


    def func_lps(img):
            return img.addBands(img.select('VH').divide(img.select('VV')).rename('ratio').multiply(scaleFactor)) \
        .set('system:time_start',img.get('segmentStartTime')).set('cMethod','slope')
    slopeCorrected = slope_lib.slope_correction(s1Pass, slopeParams).map(func_lps)



    # Pick correction method based on correctionMethod parameter
    s1Pass = ee.Algorithms.If(correctionMethod.compareTo('volume').eq(0), volumeCorrected, s1Pass)
    s1Pass = ee.Algorithms.If(correctionMethod.compareTo('surface').eq(0), slopeCorrected, s1Pass)
    s1Pass = ee.ImageCollection(s1Pass)



    #------------------- Optionally create temporal composites
    if (interval):
            print('Doing temporal composite....')
            s1Pass = composite.createTemporalComposites(s1Pass, start, intervalCount, intervalSize, interval, reducer)


    #------------------- Optionally do Boxcar or Lee filters
    if (boxcar):

            def func_cre(image):
                    VV = sarLib.toDB(sarLib.boxcarFlt(sarLib.toNatural(image.select('VV'))))
                    VH = sarLib.toDB(sarLib.boxcarFlt(sarLib.toNatural(image.select('VH'))))
                    ratio = VH.divide(VV).rename('ratio').multiply(scaleFactor)
                    return image.select().addBands(ee.Image.cat([VV, VH, ratio]).rename(['VV','VH','ratio']))
            s1Pass = s1Pass.map(func_cre)


# Master function for processing S2 imagery with s2cloudless

def func_ixl(aoi, startDate, endDate, startDOY, endDOY, cloudFilter, cloudProbThresh, NirDarkThresh, cloudPrjDist, buffer):
    startDate = startDate or '2015-01-01'
    endDate = endDate or '2023-01-01'
    cloudFilter = cloudFilter or 90
    cloudProbThresh = cloudProbThresh or 50
    NirDarkThresh = NirDarkThresh or 0.15
    cloudPrjDist = cloudPrjDist or 1
    buffer = buffer or 50

    # Import and filter S2
    s2_sr_col = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(aoi) \
    .filterDate(startDate, endDate) \
    .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloudFilter)) \
    .filter(ee.Filter.dayOfYear(startDOY, endDOY))

    # Import and filter s2cloudless.
    s2_cloudless_col = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY') \
    .filterBounds(aoi) \
    .filterDate(startDate, endDate) \
    .filter(ee.Filter.dayOfYear(startDOY, endDOY))


    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    s2_joined_col = ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary':s2_sr_col,
        'secondary':s2_cloudless_col,
        'condition':ee.Filter.equals(**{
            'leftField':'system:index',
            'rightField':'system:index'
            })
        }))


    def func_gho(img):
            # Add cloud component bands.
            img_cloud = addCloudBands(img, cloudProbThresh)

            # Add cloud shadow component bands.
            img_cloud_shadow = addShadowBands(img_cloud, NirDarkThresh, cloudPrjDist)

            # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
            is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)

            # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
            # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
            is_cld_shdw2 = (is_cld_shdw.focal_min(2).focal_max(buffer*2/20) \
            .reproject(**{'crs': img.select([0]).projection(), 'scale': 20}) \
            .rename('cloudmask'))

            # Add the final cloud-shadow mask to the image.
            img_with_masks = img_cloud_shadow.addBands(is_cld_shdw2)

            mask = img_with_masks.select(['cloudmask']).eq(0)

            img_to_return = ee.Image(img_with_masks.updateMask(mask) \
            .select('B2', 'B3', 'B4','B8','B11','B12') \
            .rename(['BLUE','GREEN','RED','NIR','SWIR1','SWIR2']) \
            .divide(10000) \
            .copyProperties(img))

            return img_to_return.set('system:time_start', ee.Image(img_to_return.get('s2cloudless')).get('system:time_start'))

    s2_with_cloud_bands = s2_joined_col.map(func_gho)


    s2_with_cloud_bands = glance.Inputs.doIndices(s2_with_cloud_bands)

    def func_gft(img):
            return img.addBands(original_DI(img, 'BRIGHTNESS','GREENNESS','WETNESS','DI_TC_BEFORE'))

    s2_with_cloud_bands = s2_with_cloud_bands.map(func_gft)




    return s2_with_cloud_bands

getS2Cloudless = func_ixl

# Default S2 collection. 
def defaultS2(params):
  return getS2Cloudless(params['studyArea'], params['start'], params['end'], params['startDOY'], params['endDOY'])



prep = {
  'unmix': unmix,
  'parameters': parameters,
  'getTrainingFromHansen': getTrainingFromHansen,
  'subsetFC': subsetFC,
  'removeStorms': removeStorms,
  'prepInputForestTypes': prepInputForestTypes,
  'defaultS2': defaultS2,
  'functions': ['unmix, parameters, getTrainingFromHansen, subsetFC','removeStorms','prepInputForestTypes','defaultS2']
} 

change = {
  'decisionTree': decisionTree,
  'coded': coded,
  'fastCODED': fastCODED,
  'parameterization': parameterization,
  'functions': ['decisionTree','coded','fastCODED','parameterization']

}

postProcess = {
  'exportGrids': exportGrids,
  'prepOutput': prepOutput,
  'functions': ['exportGrids','prepOutput']
}
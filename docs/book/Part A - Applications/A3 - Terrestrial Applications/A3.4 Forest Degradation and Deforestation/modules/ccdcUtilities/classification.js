

// Utility functions for classifying CCDC
var inputUtils = require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/inputs.js')
var dateUtils = require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/dates.js')
var ccdcUtils = require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/ccdc.js')



function getBinaryLabel(fc, property, targetClass) {
  if (!fc) {
    return('Required argument [fc] missing.')
  }
  if (!targetClass) {
    return('Required argument [targetClass] missing.')
  }
  
  fc = ee.FeatureCollection(fc)
  
  var targetFc = fc.filterMetadata(property,'equals',targetClass).map(function(i) {
    return i.set(property, 1)
  })
  var notTargetFc = fc.filterMetadata(property,'not_equals',targetClass).map(function(i) {
    return i.set(property, 0)
  })

  return targetFc.merge(notTargetFc)
}



function getClassProbs(fc, coefsToClassify, classList, classifier, property) {
  var bandNames = classList.map(function(num) {
    return ee.String('probability_').cat(ee.String(ee.Number(num)))
  })
  

  var classProbs = classList.map(function(num) {
    var fcBinary = getBinaryLabel(fc, property, num)
    var trained = classifier.train({
        features: fcBinary,
        classProperty: property,
        inputProperties: coefsToClassify.bandNames()
      })
    return coefsToClassify.classify(trained)//.rename(ee.String('probability_').cat(ee.String(num)))
    
  })
  return ee.ImageCollection(ee.List(classProbs)).toBands().rename(bandNames)
}



function makeGrids(region, count, size, seed) {
  
  if (seed == 'random') {
    seed = Math.ceil(Math.random() * 1000)
  }

  // Create sample of random points within region
  var randomPoints = ee.FeatureCollection.randomPoints({
    region: region,
    points: count,
    seed: seed
  })
  
  // Take bounding box of buffered samples
  var bb =randomPoints.map(function(point) {
    var buffer = point.buffer(size/2)
    return buffer.bounds()
  })
  
  // Assign id
  var bbList = bb.toList(bb.size());
  var indexList = ee.List.sequence(1, bb.size());
  
  return ee.FeatureCollection(indexList.map(function(i) {
    return ee.Feature(bbList.get(
      ee.Number(i).subtract(1)))
      .set( {ID: i} );
  }))
  
}


function newPhaseAmplitude(img, bands, sinName, cosName){
    var sinNames = bands.map(function(x){
      return ee.String(x).cat(sinName)
    })
    var cosNames = bands.map(function(x){
      return ee.String(x).cat(cosName)
    })
    var phaseNames = bands.map(function(x){
      return ee.String(x).cat('_PHASE')
    })
    var amplitudeNames = bands.map(function(x){
      return ee.String(x).cat('_AMPLITUDE')
    })
    var phase =  img.select(sinNames).atan2(img.select(cosNames))
      // Scale to [0, 1] from radians. 
      .unitScale(-3.14159265359, 3.14159265359)
      .multiply(365) // To get phase in days!
      .rename(phaseNames)
    
    var amplitude = img.select(sinNames).hypot(img.select(cosNames)).rename(amplitudeNames)
    return phase.addBands(amplitude)
  }



function sampleResultProcedure(trainingData, coefNames, bandList, dateProperty, extraBands, ccdcImage, segs, ccdcDateFmt, trainingDateFmt, scale) {
  ccdcDateFmt = Number(ccdcDateFmt)
  var uniqueYears = ee.Dictionary(
    ee.FeatureCollection(
      trainingData).aggregate_histogram(dateProperty)).keys()

  return ee.FeatureCollection(uniqueYears.map(function(strYear) {
    // var strYear = '2010'
    var year = ee.Number.parse(strYear)
    var fcYear = trainingData.filterMetadata(dateProperty,'equals',year)
 
    var formattedDate = dateUtils.convertDate({
      inputFormat: trainingDateFmt,
      inputDate: year,
      outputFormat: ccdcDateFmt 
    })
    var coefs = ccdcUtils.getMultiCoefs(ccdcImage, formattedDate, bandList, coefNames, true, segs, 'after')
  
    // Use new code to reduce calculations
    var phaseAmps = ccdcUtils.newPhaseAmplitude(coefs, '.*SIN.*', '.*COS.*')
    coefs = coefs.addBands(phaseAmps)
    if (extraBands) {
      coefs = coefs.addBands(extraBands)
    }
    return coefs.sampleRegions({
      collection: fcYear,
      scale: scale,
      tileScale: 16,
      geometries: true
    })

  })).flatten()

}


function runCcdcProcedure(trainingData, coefNames, bandList, dateProperty, extraBands, landsatParams, segs) {
  var segs = segs || ["S1", "S2", "S3", "S4", "S5", "S6"]
  
  var trainingCCDC = getTraining({
    trainingData: trainingData, 
    extraBands: extraBands, 
    landsatParams: landsatParams
  })
  
  return trainingData.map(function(feat) { 
    var year = ee.Number(feat.get(dateProperty)).add(2)
    var year2 = ee.String(year)
    var date =dateUtils.dateToJdays(year2)
  
    var ccdImage = ccdcUtils.buildCcdImage(trainingCCDC, 6, bandList)
  
    var coefs = ccdcUtils.getMultiCoefs(ccdImage, date, bandList, coefNames, true, segs)
    
    if (extraBands) {
      coefs = coefs.addBands(extraBands)
    }
    
    var sampleCoefs = ee.Dictionary(coefs.reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: feat.geometry(),
        scale: 30,
        crs: 'EPSG:4326',
        tileScale: 8,
      }))
  
  return ee.Feature(feat).setMulti(sampleCoefs)
  
  })
}


function getTrainingCoefsAtDate(trainingData, coefNames, bandList, dateProperty, extraBands, ccdcImage, segs, ccdcDateFmt, trainingDateFmt, scale, landsatParams) {
    coefNames = coefNames ||  ['INTP','SLP','COS','SIN','RMSE','COS2','SIN2','COS3','SIN3'];
    bandList =  bandList || ['BLUE','GREEN','RED','NIR','SWIR1','SWIR2']
    dateProperty = dateProperty || 'Start_Year'
    landsatParams = landsatParams || {start: '1990-01-01',end: '2020-01-01'}
    segs = segs || ["S1", "S2", "S3", "S4", "S5", "S6"]
    ccdcDateFmt = ccdcDateFmt || 1
    trainingDateFmt = trainingDateFmt || 1
    scale = scale || 30
  
    var resultImage = ccdcImage || null
  
    if (resultImage) {
      return sampleResultProcedure(trainingData, coefNames, bandList, dateProperty, extraBands,
        resultImage, segs, ccdcDateFmt, trainingDateFmt, scale)
    } else {
      return runCcdcProcedure(trainingData, coefNames, bandList, dateProperty, extraBands,
        landsatParams, segs)
    }
}



function remapLC(feats, inLabel, outLabel, inList, outList) {
  var inList = inList || ['Water','Snow/Ice','Built','Bare','Trees','Shrub','Herbaceous','Woodland',
    'Forest','Developed','Agriculture','Barren','Grass','Ice_and_Snow','Shrubs','Wetland']

  var outList = outList || [1,2,3,4,5,6,7,8,5,3,7, 4, 7, 2, 6, 1]
  var feats = feats.map(function(feat) {
    return feat.set(outLabel,feat.get(inLabel))
  })
  
  return feats.remap(
    inList,
    outList,
    outLabel
  )  
}



function assignIds(sample, attributeName) {
  attributeName = attributeName || 'ID'
  
  var withRandom = sample.randomColumn({seed: 1})
  withRandom = withRandom.sort('random')
  var withRandomList = withRandom.toList(withRandom.size());
  var indexList = ee.List.sequence(1, withRandom.size());
  
  return ee.FeatureCollection(indexList.map(function(i) {
    return ee.Feature(withRandomList.get(
      ee.Number(i).subtract(1)))
      .set( {attributeName: i} );
  }))
}



function getMiddleDate(fc, startProp, endProp, middleProp) {
  return fc.map(function(feat) {
    var start = ee.Number(feat.get(startProp))
    var end = ee.Number(feat.get(endProp))
    var middle = (start.add(end)).divide(2).ceil().int16()
    return feat.set(middleProp,middle)
  })
}



function makeRow(color, name) {
  var colorBox = ui.Label({
    style: {
      backgroundColor: color,
      padding: '8px',
      margin: '0 0 4px 0'
    }
  });

  var description = ui.Label({
    value: name,
    style: {margin: '0 0 4px 6px'}
  });

  return ui.Panel({
    widgets: [colorBox, description],
    layout: ui.Panel.Layout.Flow('horizontal')
  });
};


function makeLegend(classes, palette, title, width, position) {
  width = width || '250px'
  title = title || 'Legend'
  position = position || 'bottom-right'
  
  var legend = ui.Panel({style: {shown: true, width: width}});
  legend.add(ui.Label(title))
  legend.style().set({position: position});
  for (var i = 0; i < classes.length; i++) {
    legend.add(makeRow(palette[i],classes[i]))
  }
  return legend
}


function getInputFeatures(seg, imageToClassify, predictors, bandNames, ancillary) {
  var str = ee.String('S')
        .cat(ee.String(ee.Number(seg).int8()))
        .cat('_.*')
  // Another string to remove segment prefix
  var str2 = ee.String('S')
    .cat(ee.String(ee.Number(seg).int8()))
    .cat('_')

  // Select bands to classify and add ancillary
  var bands = imageToClassify.select([str])

  // Rename without prefix
  var renamedBands = bands.bandNames().map(function(bn) {
    var newName = ee.String(bn).replace('_coef_','_').replace('_COEF_','_').split(str2).get(1)
    return ee.String(newName)//.replace('_coef_','_').replace('_COEF_','_')
  })
  bands = bands.rename(renamedBands)

  // Mask where there's no model
  bands = bands.updateMask(bands.select('tStart').gt(0))
  
  // Normalize the intercepts
  bands = ccdcUtils.applyNorm(bands, bands.select('.*tStart'), bands.select('.*tEnd'))
  
  // Get phase and amplitude if necessary
  // var phaseAmp = makePhaseAmp(bands, bandNames, ['_SIN','_SIN2','_SIN3'], ['_COS','_COS2','_COS3'])
  var phaseAmp = ccdcUtils.newPhaseAmplitude(bands, '.*SIN.*','.*COS.*')

  if (ancillary instanceof ee.Image) {
    phaseAmp = phaseAmp.addBands(ancillary)
  }
  
  // Add phase, amplitude, and ancillary
  bands = bands.addBands([phaseAmp]).select(predictors)

  // Remove non-inputs
  var inputFeatures = bands.bandNames()
    .removeAll(['tStart','tEnd','tBreak','changeProb',
      'BLUE_MAG','GREEN_MAG','RED_MAG','NIR_MAG','SWIR1_MAG','SWIR2_MAG','TEMP_MAG'])

  return [inputFeatures, bands]
}


function makePhaseAmp(img, bandNames) {

  var suffixList = ['','_1','_2']

  var phaseAmp1 = newPhaseAmplitude(img, bandNames, '_SIN', '_COS')
  var bns = phaseAmp1.bandNames().map(function(b) {
    return ee.String(b)
  })
  phaseAmp1 = phaseAmp1.rename(bns)

  var phaseAmp2 = newPhaseAmplitude(img, bandNames, '_SIN2', '_COS2')
  var bns = phaseAmp2.bandNames().map(function(b) {
    return ee.String(b).cat('_1')
  })
  phaseAmp1 = phaseAmp2.rename(bns)

  var phaseAmp3 = newPhaseAmplitude(img, bandNames, '_SIN3', '_COS3')
  var bns = phaseAmp3.bandNames().map(function(b) {
    return ee.String(b).cat('_2')
  })
  phaseAmp3 = phaseAmp3.rename(bns)

  return ee.Image.cat([phaseAmp1, phaseAmp2, phaseAmp3])
}


function subsetTraining(trainingData, trainProp, seed, classProperty) {

  var classCounts = ee.Dictionary(trainingData.aggregate_histogram(classProperty))
  var classes = classCounts.keys()

  var subsets = classes.map(function(c) {
    var subset = trainingData.filterMetadata(classProperty, 'equals',ee.Number.parse(c))
    
    //  Withhold a selection of training data
    var trainingSubsetWithRandom = subset.randomColumn('random',seed).sort('random')
    var indexOfSplit = trainingSubsetWithRandom.size().multiply(trainProp).int32()
    var numberOfTrain = trainingSubsetWithRandom.size().subtract(indexOfSplit).int32()
    
    var subsetTest = ee.FeatureCollection(trainingSubsetWithRandom.toList(indexOfSplit))
      .map(function(feat) {
        return feat.set('train', 0)
      })
    var subsetTrain = ee.FeatureCollection(trainingSubsetWithRandom.toList(numberOfTrain, indexOfSplit))
      .map(function(feat) {
        return feat.set('train', 1)
      })
    return ee.Algorithms.If(subset.size().gt(10),
    subsetTest.merge(subsetTrain),
    subset.map(function(feat) {
        return feat.set('train', 1)
      })
    )
  })
  return ee.FeatureCollection(subsets).flatten()
  
}



function accuracyProcedure(trainingData, imageToClassify, predictors, bandNames, ancillary, classifier, classProperty, seed, trainProp) {
  trainProp =  .4
  seed =  seed || Math.ceil(Math.random() * 1000)
  classProperty = 'LC_Num'
  trainingData = trainingData.randomColumn('random',seed).sort('random')
  trainingData = subsetTraining(trainingData, trainProp, seed, classProperty) 
  var testSubsetTest = trainingData.filterMetadata('train','equals',0)

  var testSubsetTrain = trainingData.filterMetadata('train','equals',1)

  var inputList = getInputFeatures(1, imageToClassify, predictors, bandNames, ancillary)
  var inputFeatures = ee.List(inputList).get(0)

    // var inputFeatures = inputList[0]

  // Train the classifier
  var trained = classifier.train({
    features: testSubsetTrain,
    classProperty: classProperty,
    inputProperties: inputFeatures
  })
  var classified = testSubsetTest.classify(trained)
  var confMatrix = classified.errorMatrix(classProperty, 'classification')
  // return [confMatrix, trained]
  return confMatrix

}


function classifyCoefs(imageToClassify, bandNames, ancillary, ancillaryFeatures, trainingData, classifier, studyArea, classProperty, coefs, trainProp, seed) {
  trainProp = trainProp || null
  studyArea = studyArea || null
  trainingData = ee.FeatureCollection(trainingData)
  imageToClassify = ee.Image(imageToClassify)
  // print(imageToClassify)
  // Subset training data to studyarea if specified
  if (studyArea) {
    trainingData = trainingData.filterBounds(studyArea)
  }
  // Test withholding subset of data and classifying
  if (trainProp) {
    var confMatrix = accuracyProcedure(trainingData, seed, trainProp)
  }

  // Prector names selected for classification. 
  var predictors = ee.List(bandNames).map(function(b) {
    return ee.List(coefs).map(function(i) {
      return ee.String(b).cat('_').cat(i)
    })
  }).flatten().cat(ancillaryFeatures)
  
  // Train the classifier
  var trained = classifier.train({
    features: trainingData,
    classProperty: classProperty,
    inputProperties: predictors
  })

  var bands = imageToClassify.addBands(ancillary)
  var classified =  bands.select(predictors)
                         .classify(trained)
                         .int()
                         
  return classified
}



function classifySegments(imageToClassify, numberOfSegments, bandNames, ancillary, ancillaryFeatures, trainingData, classifier, studyArea, classProperty, coefs, trainProp, seed, subsetTraining) {
  trainProp = trainProp || null
  studyArea = studyArea || null
  // subsetTraining = subsetTraining || null
  trainingData = ee.FeatureCollection(trainingData)
  imageToClassify = ee.Image(imageToClassify)

  // Subset training data to studyarea if specified
  if (studyArea && subsetTraining !== false) {
    trainingData = trainingData.filterBounds(studyArea)
  } else {
    trainingData = trainingData
  }
  // Test withholding subset of data and classifying
  if (trainProp) {
    var confMatrix = accuracyProcedure(trainingData, seed, trainProp)
  }

  // Input bands. All data will be initially queries and only these bands
  // will be eventually selected for classification. 
  var predictors = ee.List(bandNames).map(function(b) {
    return ee.List(coefs).map(function(i) {
      return ee.String(b).cat('_').cat(i)
    })
  }).flatten().cat(ancillaryFeatures)
  var inputList = getInputFeatures(1, imageToClassify, predictors, bandNames, ancillary)
  var inputFeatures = inputList[0]

  // Train the classifier
  var trained = classifier.train({
    features: trainingData,
    classProperty: classProperty,
    inputProperties: inputFeatures
  })

  // Map over segments
  var segmentsClassified = ee.List.sequence(1, numberOfSegments).map(function(seg) {
      
      // Get inputs bands for this segment # ERIC HERE
      var inputList = getInputFeatures(seg, imageToClassify, predictors, bandNames, ancillary)
      var inputFeatures = inputList[0]
      var bands = inputList[1]
      var segStr = ee.String('S').cat(ee.String(ee.Number(seg).int8()))
      var className = segStr.cat('_classification')
      var startName = segStr.cat('_tStart')
      var tEnd = segStr.cat('_tEnd')
      
      return bands
        .select(inputFeatures)
        .classify(trained)
        .updateMask(imageToClassify.select(startName).neq(0))
        .rename([className])
        .int()
    })
    
    // segmentsClassified is returned as a list so first convert to Collection
    var classified = ee.ImageCollection(segmentsClassified)

    // When reducing to bands the names change and gives an error upon export
    var bns = ee.List(classified
      .map(function(i) {
        return i.set('bn', i.bandNames())
      })
      .aggregate_array('bn'))
      .flatten()

    // Reduce to bands and rename to original band names
    classified = classified.toBands().rename(bns)
    return classified
}


function parseConfMatrix(im, attribute) {
  attribute = attribute || 'confMatrix'
  // Parse confusion matrix
  var conf = ee.String(im.get(attribute))
  conf = conf.slice(1).slice(0, -2);
  var split = conf.split('],').map(function(list) {
    return ee.String(list).slice(1).split(',').map(function(str){
      return ee.Number.parse(str)
    })
  })
  var confMatrix = ee.ConfusionMatrix(ee.Array(split))
  
  // Now create dictionary of users and producers acc
  var users = confMatrix.consumersAccuracy().project([1]).toList()
  var keys = ee.List.sequence(0, users.length().subtract(1)).map(function(num) {
    return ee.String(ee.Number(num).int8())
  })
  var names = keys.map(function(key) {
    return (ee.String('users_class_').cat(key))
  })
  var usersDict = ee.Dictionary.fromLists(names, users)
  
  var producers = confMatrix.producersAccuracy().project([0]).toList()
  keys = ee.List.sequence(0, users.length().subtract(1)).map(function(num) {
    return ee.String(ee.Number(num).int8())
  })
  names = keys.map(function(key) {
    return (ee.String('producers_class_').cat(key))
  })
  var producersDict = ee.Dictionary.fromLists(names, producers)
  im = im.setMulti(producersDict.combine(usersDict))

  return im
}


function getLcAtDate(segs, date, numberOfSegments, ccdVersion, metadataFilter, behavior, bandNames, inputFeatures, specImage, dateFormat) {
  
  segs = ee.Image(segs)
  // Hard code for now
  var bandNames = bandNames || ["BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP"]
  var inputFeatures = inputFeatures || ["INTP", "SLP","PHASE","AMPLITUDE","COS","SIN","COS2","SIN2"]
  numberOfSegments = numberOfSegments || ee.Image(segs).bandNames().length()
  ccdVersion = ccdVersion || 'v2'
  metadataFilter = metadataFilter || 'z'
  behavior = behavior || 'after'
    
  if (dateFormat === 0){
    dateFormat = 0
  } else if (dateFormat > 0) {
    dateFormat = dateFormat
  } else {
    dateFormat = 1
  }
  // dateFormat = (dateFormat && dateFormat === 0) || 1

  // CCDC Collection and 'system:index' metadata ftilter
  var ccdcCollection = ee.ImageCollection("projects/CCDC/" + ccdVersion)

  // Get CCDC coefficients
  var ccdcCollectionFiltered = ccdcCollection
    .filterMetadata('system:index', 'starts_with',metadataFilter)

  // CCDC mosaic image
  var ccdc = ccdcCollectionFiltered.mosaic()

  // Turn array image into image
  specImage = specImage || ccdcUtils.buildCcdImage(ccdc, numberOfSegments, bandNames)

  var tStarts = specImage.select('.*tStart')

  var tEnds = specImage.select('.*tEnd')

  var dateFormatted = dateUtils.convertDate({
    inputFormat: 3,
    inputDate: date,
    outputFormat: dateFormat
  })

  if (behavior == 'before') {
    var dateMask = tStarts.lt(dateFormatted)
    var matchingDate =  segs.updateMask(dateMask).reduce(ee.Reducer.lastNonNull())
  } else if (behavior == 'after') {
    var dateMask = tEnds.gt(dateFormatted)
    var matchingDate =  segs.updateMask(dateMask).reduce(ee.Reducer.firstNonNull()) 
  } else {
    var dateMask = tStarts.lt(dateFormatted).and(tEnds.gt(dateFormatted))
    var matchingDate =  segs.updateMask(dateMask).reduce(ee.Reducer.firstNonNull()) 
  }

  return matchingDate
}


function getMode(folder, matchingString) {
  
  var list = ee.data.getList({id: folder})
  var ims = []
  
  for (var i = 0; i < list.length; i++ ) {
    var id = list[i]['id']
    if (id.indexOf(matchingString) != -1) {
      var im = ee.Image(id)
      ims.push(im)
    }
  }  
   return  ee.ImageCollection(ims).reduce(ee.Reducer.mode())
}

function getInputDict(bandNames, inputFeatures, ancillaryFeatures) {
  
  // Which inputs were used
  var allPossibleInputs = ["B1","B2","B3","B4","B5","B6","B7",
                           "BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP", "INTP",
                           "AMPLITUDE", "PHASE", "AMPLITUDE_1", "PHASE_1","AMPLITUDE_2",
                           "PHASE_2", "SLP","COS", "SIN","COS2", "SIN2", "COS3","SIN3",
                           "RMSE","ELEVATION","ASPECT","DEM_SLOPE","RAINFALL","TEMPERATURE",
                           "AMPLITUDE2", "PHASE2","AMPLITUDE3",
                           "PHASE3","WATER_OCCURRENCE","POPULATION", "TREE_COVER"]
  var allActualInputs = bandNames.concat(inputFeatures).concat(ancillaryFeatures)
  
  // Get dictionary with true or false for each input
  var inputBooleans = allPossibleInputs.map(function(inp) {
    return allActualInputs.indexOf(inp) > 0
  })
  var inputDict = ee.Dictionary.fromLists(allPossibleInputs, inputBooleans)  
  var predictors = ee.List(bandNames).map(function(b) {
    return ee.List(inputFeatures).map(function(i) {
      return ee.String(b).cat('_').cat(i)
    })
  }).flatten().cat(ancillaryFeatures)
  
  return [inputDict, predictors]
}


var getPredictors = function(bandNames, inputFeatures, ancillaryFeatures) {
  return ee.List(bandNames).map(function(b) {
    return ee.List(inputFeatures).map(function(i) {
      return ee.String(b).cat('_').cat(i)
    })
  }).flatten().cat(ancillaryFeatures)
}


var loadResults = function(resultFormat,changeResults, studyRegion, segs, bandNames) {
  if (resultFormat == 'SegImage') {
    var ccdImage =  ee.Image(changeResults)
  } else if (resultFormat == 'SegCollection') {
    var ccdImage = ee.ImageCollection(changeResults)
      .filterBounds(studyRegion).mosaic()
  } else {
    var coefImage = ee.ImageCollection(changeResults)
      .filterBounds(studyRegion).mosaic()
    var ccdImage = utils.CCDC.buildCcdImage(
      coefImage, segs.length, bandNames)
  }
  return ccdImage
}

var getLC = function(img, date) {
    var dateClassificationAfter = getLcAtDate(
      img, 
      date, 
      null, 
      null, 
      null, 
      'after',
      null, 
      null,
      null, 
      1
    )
    
    var dateClassificationBefore = getLcAtDate(
      img, 
      date,
      null, 
      null, 
      null, 
      'before', 
      null, 
      null,
      null, 
      1
    )
    
    var dateClassification = ee.Image.cat(
      [
        dateClassificationAfter,
        dateClassificationBefore, 
      ]
    )
    .reduce(
      ee.Reducer.firstNonNull()
    )

    return dateClassification.rename([ee.String(date)])
  }
  
var makeYearlyMaps = function(results, years, month, day) {
  var years = years || ee.List.sequence(2000, 2020)
  var month = month || 6
  var day = day || 1
  
  var formatted = years.map(function(y) {
    var p1 = ee.String(ee.Number(y).int())
    var p2 = ee.String('-')
    var p3 = ee.String(ee.Number(month).int())
    var p4 = ee.String(ee.Number(day).int())
    return p1.cat(p2).cat(p3).cat(p2).cat(p4)
    return ee.String(y)
  })

  var ims = ee.List(formatted).map(function(y) {
      
      var lcImage = getLC(results, y)
        .rename('lc')
        
      return lcImage
      
  })
    
    
  return ee.List(ims)
}


var simpleClassification = function(fc, atts, prop, classifier) {
  atts = atts || fc.first().propertyNames().removeAll([
    'ID','Start_Year','dataPath','End_Year','Level1_Ecoregion', 'landcover',
    'Dataset','system:index','LC_Class','Continent_Code','Glance_Class_ID_level1','Glance_Class_ID_level2',
    'Level1_Ecoregion','Level2_Ecoregion','Dataset_Code','Continent','Middle_Year','trainYear'])
  classifier = classifier || ee.Classifier.smileRandomForest(200)
  prop = prop || 'Glance_Class_ID_level1'
  
  var ancillaryFeatures = ["ELEVATION","ASPECT","DEM_SLOPE","RAINFALL","POPULATION","WATER_OCCURRENCE"]
  var ancillary = inputUtils.getAncillary()
  var bandNames = ["BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP"]
  var coefs =["INTP", "SLP","COS", "SIN","RMSE","COS2","SIN2","COS3","SIN3"]
  
  var ccdcCollectionFiltered = ee.ImageCollection("projects/CCDC/v2")
    .filterMetadata('system:index', 'starts_with',"z_")
    .mosaic()
  var ccdImage = ccdcUtils.buildCcdImage(ccdcCollectionFiltered, 1, bandNames)
  var predictors = ee.List(bandNames).map(function(b) {
    return ee.List(coefs).map(function(i) {
      return ee.String(b).cat('_').cat(i)
  })}).flatten().cat(ancillaryFeatures)

  
  var inputList = ee.List(getInputFeatures(1, ccdImage, predictors, bandNames, ancillary))
  var inputFeatures = ee.List(inputList.get(0))
  var imageToClassify = ee.Image(inputList.get(1))

  // Train the classifier
  var trained = classifier.train({
    features: fc,
    classProperty: prop,
    inputProperties: inputFeatures
  })
  return imageToClassify.classify(trained)
}

exports = {
  getMiddleDate: getMiddleDate,
  makeGrids: makeGrids,
  getBinaryLabel: getBinaryLabel,
  getClassProbs: getClassProbs,
  getTrainingCoefsAtDate: getTrainingCoefsAtDate,
  remapLC: remapLC,
  assignIds: assignIds,
  makeLegend: makeLegend,
  classifyCoefs: classifyCoefs,
  classifySegments: classifySegments,
  parseConfMatrix: parseConfMatrix,
  accuracyProcedure: accuracyProcedure,
  getLcAtDate: getLcAtDate,
  getMode: getMode,
  getInputDict: getInputDict,
  getPredictors: getPredictors,
  makePhaseAmp: makePhaseAmp,
  getInputFeatures: getInputFeatures,
  loadResults: loadResults,
  makeYearlyMaps: makeYearlyMaps,
  simpleClassification: simpleClassification
}







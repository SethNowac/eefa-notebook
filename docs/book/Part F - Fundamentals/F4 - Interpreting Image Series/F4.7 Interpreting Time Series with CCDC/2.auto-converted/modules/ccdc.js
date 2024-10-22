
function buildSegmentTag(nSegments) {
  return ee.List.sequence(1, nSegments).map(function(i) {
    return ee.String('S').cat(ee.Number(i).int())
  })
}

function buildBandTag(tag, bandList) {
  var bands = ee.List(bandList)
  return bands.map(function(s) {
    return ee.String(s).cat('_' + tag)
  })
}

function buildMagnitude(fit, nSegments, bandList){
  var segmentTag = buildSegmentTag(nSegments)
  var zeros = ee.Image(ee.Array(ee.List.repeat(0, nSegments)))
  // Pad zeroes for pixels that have less than nSegments and then slice the first nSegment values
  var retrieveMags = function(band){
    var magImg = fit.select(band + '_magnitude').arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)
    var tags = segmentTag.map(function(x){
      return ee.String(x).cat('_').cat(band).cat('_MAG')
    })
    return magImg.arrayFlatten([tags])
  }
  return ee.Image(bandList.map(retrieveMags))
}

function buildRMSE(fit, nSegments, bandList){
  var segmentTag = buildSegmentTag(nSegments)
  var zeros = ee.Image(ee.Array(ee.List.repeat(0, nSegments)))
  // Pad zeroes for pixels that have less than 6 segments and then slice the first 6 values
  var retrieveMags = function(band){
    var magImg = fit.select(band + '_rmse').arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)
    var tags = segmentTag.map(function(x){ 
      return ee.String(x).cat('_').cat(band).cat('_RMSE')
    })
    return magImg.arrayFlatten([tags])
  }
  return ee.Image(bandList.map(retrieveMags))
}

function buildCoefs(fit, nSegments, bandList) {
  var nBands = bandList.length
  var segmentTag = buildSegmentTag(nSegments)
  var bandTag = buildBandTag('coef', bandList)
  var harmonicTag = ['INTP','SLP','COS','SIN','COS2','SIN2','COS3','SIN3']
  
  var zeros = ee.Image(ee.Array([ee.List.repeat(0, harmonicTag.length)])).arrayRepeat(0, nSegments)
  var retrieveCoefs = function(band){
    var coefImg = fit.select(band + '_coefs').arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)
    var tags = segmentTag.map(function(x){
      return ee.String(x).cat('_').cat(band).cat('_coef')
    })
    return coefImg.arrayFlatten([tags, harmonicTag])
  }
  
  return ee.Image(bandList.map(retrieveCoefs))
}


function buildStartEndBreakProb(fit, nSegments, tag) {
  var segmentTag = buildSegmentTag(nSegments).map(function(s) {
    return ee.String(s).cat('_'+tag)
  })
  
  var zeros = ee.Array(0).repeat(0, nSegments)
  var magImg = fit.select(tag).arrayCat(zeros, 0).float().arraySlice(0, 0, nSegments)
  
  return magImg.arrayFlatten([segmentTag])
}


function buildCcdImage(fit, nSegments, bandList) {
  var magnitude = buildMagnitude(fit, nSegments, bandList)
  var rmse = buildRMSE(fit, nSegments, bandList)

  var coef = buildCoefs(fit, nSegments, bandList)
  var tStart = buildStartEndBreakProb(fit, nSegments, 'tStart')
  var tEnd = buildStartEndBreakProb(fit, nSegments, 'tEnd')
  var tBreak = buildStartEndBreakProb(fit, nSegments, 'tBreak')
  var probs = buildStartEndBreakProb(fit, nSegments, 'changeProb')
  var nobs = buildStartEndBreakProb(fit, nSegments, 'numObs')
  return ee.Image.cat(coef, rmse, magnitude, tStart, tEnd, tBreak, probs, nobs)
}


function getSyntheticForYear(image, date, dateFormat, band, segs) {
  var tfit = date
  var PI2 = 2.0 * Math.PI
  var OMEGAS = [PI2 / 365.25, PI2, PI2 / (1000 * 60 * 60 * 24 * 365.25)]
  var omega = OMEGAS[dateFormat];
  var imageT = ee.Image.constant([1, tfit,
                                tfit.multiply(omega).cos(),
                                tfit.multiply(omega).sin(),
                                tfit.multiply(omega * 2).cos(),
                                tfit.multiply(omega * 2).sin(),
                                tfit.multiply(omega * 3).cos(),
                                tfit.multiply(omega * 3).sin()]).float()
                                
  // OLD CODE
  // Casting as ee string allows using this function to be mapped
  // var selectString = ee.String('.*' + band + '_coef.*')
  // var params = getSegmentParamsForYear(image, date) 
  //                       .select(selectString)
  // return imageT.multiply(params).reduce('sum').rename(band)
                        
  // Use new standard functions instead
  var COEFS = ["INTP", "SLP", "COS", "SIN", "COS2", "SIN2", "COS3", "SIN3"]
  var newParams = getMultiCoefs(image, date, [band], COEFS, false, segs, 'before')
  return imageT.multiply(newParams).reduce('sum').rename(band)
  
}

function getMultiSynthetic(image, date, dateFormat, bandList, segs){
  var retrieveSynthetic = function(band){
    return getSyntheticForYear(image, date, dateFormat, band, segs)
  }
  
  return ee.Image.cat(bandList.map(retrieveSynthetic))
}


function fillNoData(fit, nCoefs, nBands){
  var d1 = ee.Image(ee.Array([0]).double())
  var d2 = ee.Image(ee.Array([ee.List.repeat(-9999, nCoefs)])).double() 
  
  var upper = ee.Image([d1, d1, d1, d1.int32(), d1])
  
  // Create variable number of coef, rmse and change amplitude bands
  var arrCenter = []
  var arrBottom = []
  for (var i = 0; i < nBands; i++) {
    arrCenter.push(d2)
    arrBottom.push(d1, d1)
  } 
  var center = ee.Image(arrCenter)
  var bottom = ee.Image(arrBottom)
  
  var mock = upper.addBands(center).addBands(bottom).rename(fit.bandNames()).updateMask(fit.mask())
  var newimage = ee.ImageCollection([mock, fit]).mosaic()
  return newimage
  
}

function dateToDays(strDate){
  var date = ee.Date(strDate)
  // Number of days since 01-01-0000 unti 01-01-1970
  var epoch = ee.Number(719177)
  // Convert milis to days
  var days = ee.Number(date.millis().divide(86400000))
  return days.add(epoch)
}


function dateToSegment(ccdResults, date, segNames){
  var startBands = ccdResults.select(".*_tStart").rename(segNames)
  var endBands = ccdResults.select(".*_tEnd").rename(segNames)
  
  var start = startBands.lte(date)
  var end = endBands.gte(date)
  
  var segmentMatch = start.and(end)
  return segmentMatch
}


function filterCoefs(ccdResults, date, band, coef, segNames, behavior){

  var startBands = ccdResults.select(".*_tStart").rename(segNames)
  var endBands = ccdResults.select(".*_tEnd").rename(segNames)
  
  // Get all segments for a given band/coef. Underscore in concat ensures
  // that bands with similar names are not selected twice (e.g. GREEN, GREENNESS)
  var selStr = ".*".concat(band).concat("_.*").concat(coef) // Client side concat
  var coef_bands = ccdResults.select(selStr)
  
  // Select a segment based on conditions
  if (behavior == "normal"){
    var start = startBands.lte(date)
    var end = endBands.gte(date)
    var segmentMatch = start.and(end)
    var outCoef = coef_bands.updateMask(segmentMatch).reduce(ee.Reducer.firstNonNull())
    
  } else if (behavior == "after"){
    var segmentMatch = endBands.gt(date)
    var outCoef = coef_bands.updateMask(segmentMatch).reduce(ee.Reducer.firstNonNull())
    
  } else if (behavior ==  "before"){
    // Mask start to avoid comparing against zero, mask after to remove zeros from logical comparison
    var segmentMatch = startBands.selfMask().lt(date).selfMask()
    var outCoef =  coef_bands.updateMask(segmentMatch).reduce(ee.Reducer.lastNonNull())
  } 
  
  // TODO: Add a "automatic" after, then before behavior
  return outCoef
  
}


function normalizeIntercept(intercept, start, end, slope) {
  var middleDate = ee.Image(start).add(ee.Image(end)).divide(2)
  var slopeCoef = ee.Image(slope).multiply(middleDate)
  return ee.Image(intercept).add(slopeCoef)
}


function getCoef(ccdResults, date, bandList, coef, segNames, behavior){
  var inner = function(band){
    var band_coef = filterCoefs(ccdResults, date, band, coef, segNames, behavior)
    return band_coef.rename(band.concat("_").concat(coef)) // Client side concat
  }
  var coefs = ee.Image(bandList.map(inner)) // Client side map
  return coefs
}


function applyNorm(bandCoefs, segStart, segEnd){
  var intercepts = bandCoefs.select(".*INTP")
  var slopes = bandCoefs.select(".*SLP")
  var normalized = normalizeIntercept(intercepts, segStart, segEnd, slopes)
  return bandCoefs.addBands({srcImg:normalized, overwrite:true})
}

function getMultiCoefs(ccdResults, date, bandList, coef_list, cond, segNames, behavior){
  // Non normalized
  var inner = function(coef){
    var inner_coef = getCoef(ccdResults, date, bandList, coef, segNames, behavior)
    return inner_coef
  }

  var coefs = ee.Image(coef_list.map(inner))

  // Normalized
  var segStart = filterCoefs(ccdResults, date, "","tStart", segNames, behavior)
  var segEnd = filterCoefs(ccdResults, date, "","tEnd", segNames, behavior)
  var normCoefs = applyNorm(coefs, segStart, segEnd)
  
  var out_coefs = ee.Algorithms.If(cond, normCoefs, coefs)
  return ee.Image(out_coefs)
}


function getChanges(ccdResults, startDate, endDate, segNames){
  var breakBands = ccdResults.select(".*_tBreak").rename(segNames)
  var segmentMatch = breakBands.gte(startDate).and(breakBands.lt(endDate))
  return segmentMatch
}


function filterMag(ccdResults, startDate, endDate, band, segNames){
  var segMask = getChanges(ccdResults, startDate, endDate, segNames)
  var selStr = ".*".concat(band).concat(".*").concat("MAG") // Client side concat
  var feat_bands = ccdResults.select(selStr)
  var filteredMag = feat_bands.mask(segMask).reduce(ee.Reducer.max())
  var numTbreak = ccdResults.select(".*tBreak").mask(segMask).reduce(ee.Reducer.count())
  var filteredTbreak = ccdResults.select(".*tBreak").mask(segMask).reduce(ee.Reducer.max())
  return filteredMag.addBands(filteredTbreak) 
                    .addBands(numTbreak)
                    .rename(['MAG', 'tBreak', 'numTbreak'])
}


function phaseAmplitude(img, bands, sinName, cosName){
    var sinNames = bands.map(function(x){
      return x.concat(sinName)
    })
    var cosNames = bands.map(function(x){
      return x.concat(cosName)
    })
    var phaseNames = bands.map(function(x){
      return x.concat('_PHASE')
    })
    var amplitudeNames = bands.map(function(x){
      return x.concat('_AMPLITUDE')
    })
    var phase =  img.select(sinNames).atan2(img.select(cosNames))
      .unitScale(-Math.PI, Math.PI)
      .multiply(365)
      .rename(phaseNames)
    
    var amplitude = img.select(sinNames).hypot(img.select(cosNames)).rename(amplitudeNames)
    return phase.addBands(amplitude)
  }

  
function newPhaseAmplitude(img, sinExpr, cosExpr){
    var sin = img.select(sinExpr)
    var cos = img.select(cosExpr)
    
    var phase = sin.atan2(cos)
      .unitScale(-3.14159265359, 3.14159265359)
      .multiply(365)
    
    var amplitude = sin.hypot(cos)
    
    var phaseNames = phase.bandNames().map(function(x){
      return ee.String(x).replace('_SIN', '_PHASE')
    })
    var amplitudeNames = amplitude.bandNames().map(function(x){
      return ee.String(x).replace('_SIN', '_AMPLITUDE')
    })
    return phase.rename(phaseNames).addBands(amplitude.rename(amplitudeNames))
  }


exports = {
  buildSegmentTag: buildSegmentTag,
  buildBandTag: buildBandTag,
  buildMagnitude: buildMagnitude,
  buildRMSE: buildRMSE,
  buildCoefs: buildCoefs,
  buildStartEndBreakProb: buildStartEndBreakProb,
  buildCcdImage: buildCcdImage,
  getSyntheticForYear: getSyntheticForYear,
  getMultiSynthetic: getMultiSynthetic,
  fillNoData: fillNoData,
  dateToDays: dateToDays, 
  filterCoefs: filterCoefs,
  normalizeIntercept: normalizeIntercept,
  getCoef: getCoef,
  applyNorm: applyNorm,
  getMultiCoefs: getMultiCoefs,
  getChanges: getChanges,
  filterMag: filterMag,
  phaseAmplitude: phaseAmplitude,
  newPhaseAmplitude: newPhaseAmplitude
  
}

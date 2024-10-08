#*
# Copyright (c) 2018 Gennadii Donchyts. All rights reserved.

# This work is licensed under the terms of the MIT license.  
# For a copy, see <https://opensource.Org/licenses/MIT>.
#

import ee
import geemap
import array
import math

#***
#  * Code adapted from https://developers.google.com/earth-engine/guides/arrays_eigen_analysis
#  * 
#  * original code was by Nick(?)
 #
def PCA(image, region, scale):
  # Get some information about the input to be used later.
  #scale = image.projection().nominalScale()
  bandNames = image.bandNames()
  
  # Mean center the data to enable a faster covariance reducer
  # and an SD stretch of the principal components.
  meanDict = image.reduceRegion(**{
      'reducer': ee.Reducer.mean(),
      'geometry': region,
      'scale': scale,
      'maxPixels': 1e10
  })
  means = ee.Image.constant(meanDict.values(bandNames))
  centered = image.subtract(means)

  # This helper function returns a list of new band names.
  def getNewBandNames(prefix):
    seq = ee.List.sequence(1, bandNames.length())
    def func_laq(b):
      return ee.String(prefix).cat(ee.Number(b).int())
    return seq.map(func_laq)

  
  # This function accepts mean centered imagery, a scale and
  # a region in which to perform the analysis.  It returns the
  # Principal Components (PC) in the region as a new image.
  def getPrincipalComponents(centered, scale, region):
    
    # Collapse the bands of the image into a 1D array per pixel.
    arrays = centered.toArray()
  
    # Compute the covariance of the bands within the region.
    covar = arrays.reduceRegion(**{
      'reducer': ee.Reducer.centeredCovariance(),
      'geometry': region,
      'scale': scale,
      'maxPixels': 1e10
    })

    # Get the 'array' covariance result and cast to an array.
    # This represents the band-to-band covariance within the region.
    covarArray = ee.Array(covar.get('array'))
    #print('covarArray')
    #print(covarArray)
    
    # Perform an eigen analysis and slice apart the values and vectors.
    eigens = covarArray.eigen()
    #print('eigens')
    #print(eigens)
    
    # This is a P-length vector of Eigenvalues.
    eigenValues = eigens.slice(1, 0, 1)
    #print('eigenValues')
    #print(eigenValues)
    
    # This is a PxP matrix with eigenvectors in rows.
    eigenVectors = eigens.slice(1, 1)
    #print('eigenVectors')
    #print(eigenVectors)

    # Convert the array image to 2D arrays for matrix computations.
    arrayImage = arrays.toArray(1)
    #print('arrayImage')
    #print(arrayImage)
    
    # Left multiply the image array by the matrix of eigenvectors.
    principalComponents = ee.Image(eigenVectors).matrixMultiply(arrayImage)
    #print('principalComponents')
    #print(principalComponents)

    # Turn the square roots of the Eigenvalues into a P-band image.
    sdImage = ee.Image(eigenValues.sqrt()) \
      .arrayProject([0]).arrayFlatten([getNewBandNames('sd')])
    #print('sdImage')
    #print(sdImage) 
    
    # Turn the PCs into a P-band image, normalized by SD.
    result = (principalComponents
      # Throw out an an unneeded dimension, [[]] -> [].
      .arrayProject([0])
      # Make the one band array image a multi-band image, [] -> image.
      .arrayFlatten([getNewBandNames('pc')])
      # Normalize the PCs by their SDs.
      .divide(sdImage))
    #print('result')
    #print(result)
    
    return result

  
  # Get the PCs at the specified scale and in the specified region
  pcImage = getPrincipalComponents(centered, scale, region)
  return pcImage


#***
#  * Multiteporal speckle filter: image is the original image, images is the temporal collection of images
#  * 
#  * Version: 1.0
#  * 
#  * by Genadii Donchyts https://groups.google.com/d/msg/google-earth-engine-developers/umGlt5qIN1I/jQ4Scd_pAAAJ
#  *
#  * Example: https://code.earthengine.google.com/52c695b6fe7c25b5cdc1f16c8dd0f17e
 #
def multitemporalDespeckle(images, radius, units, opt_timeWindow):
  timeWindow = opt_timeWindow or { 'before': -3, 'after': 3, 'units': 'month' }
  bandNames = ee.Image(images.first()).bandNames()
  def func_uea(b): return ee.String(b).cat('_mean') 
  def func_ueb(b): return ee.String(b).cat('_ratio')
  bandNamesMean = bandNames.map(func_uea)
  bandNamesRatio = bandNames.map(func_ueb)
  
  # compute space-average for all images
  def func_jhy(i):
    reducer = ee.Reducer.mean()
    kernel = ee.Kernel.square(radius, units)
    
    mean = i.reduceNeighborhood(reducer, kernel).rename(bandNamesMean)
    ratio = i.divide(mean).rename(bandNamesRatio)

    return i.addBands(mean).addBands(ratio)
  
  meanSpace = images.map(func_jhy)

  #***
  # * computes a multi-temporal despeckle function for a single image
  #
  def multitemporalDespeckleSingle(image):
    t = image.date()
    from_py = t.advance(ee.Number(timeWindow.before), timeWindow.units)
    to = t.advance(ee.Number(timeWindow.after), timeWindow.units)
    
    meanSpace2 = ee.ImageCollection(meanSpace).select(bandNamesRatio).filterDate(from_py, to) \
      .filter(ee.Filter.eq('relativeOrbitNumber_start', image.get('relativeOrbitNumber_start'))) # use only images from the same cycle
    
    b = image.select(bandNamesMean)

    return b.multiply(meanSpace2.sum()).divide(meanSpace2.count()).rename(bandNames) \
      .copyProperties(image, ['system:time_start'])
  
  
  return meanSpace.map(multitemporalDespeckleSingle).select(bandNames)


#***
#  * Removes low-entropy edges
 #
def maskLowEntropy(image):
  bad = image.select(0).multiply(10000).toInt().entropy(ee.Kernel.circle(5)).lt(3.2)
 
  return image.updateMask(image.mask().multiply(bad.focal_max(5).Not()))

# perform hit-or-miss
def hitOrMiss(image, se1, se2, crs, crs_transform):
  if (type(crs) is None): crs = None

  e1 = image.reduceNeighborhood(ee.Reducer.min(), se1)
  e2 = image.Not().reduceNeighborhood(ee.Reducer.min(), se2)
  result = e1.And(e2)
  
  if(crs != None):
    result = result.reproject(crs, crs_transform)
  
  return result

def splitKernel(kernel, value):
  result = []
  for r in range(len(kernel)):
      row = []
      for c in range(len(kernel)):
          row.append(1 if kernel[r][c] == value else 0)
      result.append(row)
  
  return result


#*** 
 # * Generates skeleton using morphological thining
 #
def skeletonize(image, iterations, method, crs, crs_transform):
  if (type(crs) is None): crs = None

  se1w = [[2, 2, 2], 
              [0, 1, 0], 
              [1, 1, 1]]
  
  if(method == 2):
    se1w = [[2, 2, 2], 
            [0, 1, 0], 
            [0, 1, 0]]
  se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
  se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))
  
  se2w = [[2, 2, 0], 
              [2, 1, 1], 
              [0, 1, 0]]
  
  if(method == 2):
       se2w = [[2, 2, 0], 
               [2, 1, 1], 
               [0, 1, 1]]
  
  se21 = ee.Kernel.fixed(3, 3, splitKernel(se2w, 1))
  se22 = ee.Kernel.fixed(3, 3, splitKernel(se2w, 2))
  
  result = image
  
  if (crs != None):
    # ee.Image(0).Or(image)
    
    result = image.reproject(crs, crs_transform)

  for i in range(iterations):
    for j in range(4):
      result = result.subtract(hitOrMiss(result, se11, se12, crs, crs_transform))
      se11 = se11.rotate(1)
      se12 = se12.rotate(1)
  
      result = result.subtract(hitOrMiss(result, se21, se22, crs, crs_transform))
      se21 = se21.rotate(1)
      se22 = se22.rotate(1)

      #result = result.mask(mask)
    
  
#*
# if (i%5 == 0) {
#       color = 'fec4' + pad(parseInt(100.0 * i/iterations), 2)
#       print(color)
#       Map.addLayer(result.mask(result), {palette:color, opacity: 0.5}, 'thining' + i)
#     }  
#
  
  
  return result


# I(n+1, i, j) = I(n, i, j) + lambda * (cN * dN(I) + cS * dS(I) + cE * dE(I), cW * dW(I))
def peronaMalikFilter(I, iter, opt_K, opt_method):
  method = opt_method or 1
  K = opt_K or 10

  dxW = ee.Kernel.fixed(3, 3,
                           [[ 0,  0,  0],
                            [ 1, -1,  0],
                            [ 0,  0,  0]])
  
  dxE = ee.Kernel.fixed(3, 3,
                           [[ 0,  0,  0],
                            [ 0, -1,  1],
                            [ 0,  0,  0]])
  
  dyN = ee.Kernel.fixed(3, 3,
                           [[ 0,  1,  0],
                            [ 0, -1,  0],
                            [ 0,  0,  0]])
  
  dyS = ee.Kernel.fixed(3, 3,
                           [[ 0,  0,  0],
                            [ 0, -1,  0],
                            [ 0,  1,  0]])

  lambda_py = 0.2

  if(method == 1):
    k1 = ee.Image(-1.0/K)

    for i in range(iter):
      dI_W = I.convolve(dxW)
      dI_E = I.convolve(dxE)
      dI_N = I.convolve(dyN)
      dI_S = I.convolve(dyS)
      
      cW = dI_W.multiply(dI_W).multiply(k1).exp()
      cE = dI_E.multiply(dI_E).multiply(k1).exp()
      cN = dI_N.multiply(dI_N).multiply(k1).exp()
      cS = dI_S.multiply(dI_S).multiply(k1).exp()
  
      I = I.add(ee.Image(lambda_py).multiply(cN.multiply(dI_N).add(cS.multiply(dI_S)).add(cE.multiply(dI_E)).add(cW.multiply(dI_W))))

  elif(method == 2):
    k2 = ee.Image(K).multiply(ee.Image(K))

    for i in range(iter):
      dI_W = I.convolve(dxW)
      dI_E = I.convolve(dxE)
      dI_N = I.convolve(dyN)
      dI_S = I.convolve(dyS)
      
      # cW = ee.Image(1.0).divide(ee.Image(1.0).add(dI_W.multiply(dI_W).divide(k2)))
      # cE = ee.Image(1.0).divide(ee.Image(1.0).add(dI_E.multiply(dI_E).divide(k2)))
      # cN = ee.Image(1.0).divide(ee.Image(1.0).add(dI_N.multiply(dI_N).divide(k2)))
      # cS = ee.Image(1.0).divide(ee.Image(1.0).add(dI_S.multiply(dI_S).divide(k2)))

      # bugfix by Daniele Rossi
      cW = ee.Image(-1.0).multiply(dI_W.multiply(dI_W).divide(k2)).exp() 
      cE = ee.Image(-1.0).multiply(dI_E.multiply(dI_E).divide(k2)).exp() 
      cN = ee.Image(-1.0).multiply(dI_N.multiply(dI_N).divide(k2)).exp() 
      cS = ee.Image(-1.0).multiply(dI_S.multiply(dI_S).divide(k2)).exp() 
   
      I = I.add(ee.Image(lambda_py).multiply(cN.multiply(dI_N).add(cS.multiply(dI_S)).add(cE.multiply(dI_E)).add(cW.multiply(dI_W))))
  
  return I

#***
#  * pad(0,3) --> '003'
 #
def pad(n, width, z):
  z = z or '0'
  n = n + ''
  return n if n.length >= width else array.array(width - n.length + 1).join(z) + n

#***
 # * Clips and rescales image using a given range of values
 # 
def rescale(img, exp, thresholds):
  return img.expression(exp, { 'img': img }).subtract(thresholds[0]).divide(thresholds[1] - thresholds[0])

#*** 
 # * Convet image from degrees to radians
 #
def radians(img): return img.toFloat().multiply(3.1415927).divide(180)

#***
 # * Computes hillshade
 #
def hillshade(az, ze, slope, aspect):
  azimuth = radians(ee.Image.constant(az))
  zenith = radians(ee.Image.constant(90).subtract(ee.Image.constant(ze)))
  return azimuth.subtract(aspect).cos().multiply(slope.sin()).multiply(zenith.sin()) \
      .add(zenith.cos().multiply(slope.cos()))

def Terrain(elevation):
  step = ee.Image.pixelArea().sqrt()
  
  def radians(img):
    return img.toFloat().multiply(math.pi).divide(180) 
  
  k_dx = ee.Kernel.fixed(3, 3,
                         [[ 1/8,  0,  -1/8],
                          [ 2/8,  0,  -2/8],
                          [ 1/8,  0,  -1/8]])
  
  k_dy = ee.Kernel.fixed(3, 3,
                         [[ -1/8, -2/8,  -1/8],
                          [ 0,    0,    0],
                          [ 1/8, 2/8,   1/8]])
  
  
  dx = elevation.convolve(k_dx)
  dy = elevation.convolve(k_dy)
  
  slope = ee.Image().expression("sqrt((x*x + y*y)/(step*step))", {x: dx, y: dy, step: step}).atan()

  aspect = dx.atan2(dy).add(math.PI)

  return {'aspect': aspect, 'slope': slope}


#***
 # * Styles RGB image using hillshading, mixes RGB and hillshade using HSV<->RGB transform
 #
def hillshadeRGB(image, elevation, weight, height_multiplier, azimuth, zenith, contrast, brightness, saturation, castShadows, customTerrain):
  weight = 1 if type(weight) is None else weight
  brightness = 0 if type(brightness) is None else brightness
  contrast = 1 if type(contrast) is None else contrast
  height_multiplier = height_multiplier or 5
  azimuth = azimuth or 0
  zenith = zenith or 45
  saturation = 1 if type(saturation) is None else saturation

  hsv = image.unitScale(0, 255).rgbToHsv()#.reproject(ee.Projection('EPSG:3857').atScale(Map.getScale()))
 
  z = elevation.multiply(ee.Image.constant(height_multiplier))

  if(customTerrain):
    terrain = Terrain(z)
    slope = terrain.slope.resample('bicubic')
    aspect = terrain.aspect.resample('bicubic')
  else:
    terrain = ee.Algorithms.Terrain(z)
    slope = radians(terrain.select(['slope'])).resample('bicubic')
    aspect = radians(terrain.select(['aspect'])).resample('bicubic')

  hs = hillshade(azimuth, zenith, slope, aspect).resample('bicubic')

  if(castShadows):
    hysteresis = True
    neighborhoodSize = 512

    hillShadow = ee.Algorithms.HillShadow(elevation, azimuth, ee.Number(90).subtract(zenith), neighborhoodSize, hysteresis).float()

    hillShadow = ee.Image(1).float().subtract(hillShadow)
    
    # opening
    # hillShadow = hillShadow.multiply(hillShadow.focal_min(3).focal_max(6))    
  
    # cleaning
    hillShadow = hillShadow.focal_mode(3)
  
    # smoothing  
    hillShadow = hillShadow.convolve(ee.Kernel.gaussian(5, 3))
  
    # transparent
    hillShadow = hillShadow.multiply(0.7)
  
    hs = hs.subtract(hillShadow).rename('shadow')

  intensity = hs.multiply(ee.Image.constant(weight)) \
    .add(hsv.select('value').multiply(ee.Image.constant(1).subtract(weight)))
    
  sat = hsv.select('saturation').multiply(saturation)
  
  hue = hsv.select('hue')

  result = ee.Image.cat(hue, sat, intensity).hsvToRgb().multiply(ee.Image.constant(1).float().add(contrast)).add(ee.Image.constant(brightness).float())

  if(customTerrain):
    mask = elevation.mask().focal_min(2)
    # proj = mask.projection()
    # mask = mask
    #   .And(mask.changeProj(proj, proj.translate(500, 500)))
    #   .And(mask.changeProj(proj, proj.translate(-500, -500)))
      
    result = result \
      .updateMask(mask)
  
  return result

hillshadeit = hillshadeRGB # backward-compabitility

#***
 # * Adds a features layer as an image
 #
def func_addAsImage(features, name, options):
    fill = True
    outline = True
    palette = ['555555', '000000','ffff00']
    image = True
    opacity = 1
  
    fill = fill if type(options['fill']) is None else options['fill']
    outline = outline if type(options['outline']) is None else options['outline']
    palette = options['palette'] or palette
    opacity = options['opacity'] or opacity

    if(type(features) is None):
      raise 'Please specify features'
    
    if(type(name) is None):
      raise 'Please specify name'
    
    image = ee.Image().byte()
    
    if(fill):
      image = image \
        .paint(features, 1)
      
    if(outline):
      image = image \
        .paint(features, 2, 1)
  
    layer = {
      'visible': True,
      'opacity': 1.0,
      'name': name
    }  
    
    if(type(options['layer']) is not None):
      layer['visible'] = options['layer']['visible'] if type(options['layer']['visible']) is not None else layer['visible']
      layer['opacity'] = options['layer']['opacity'] if type(options['layer']['opacity']) is not None != 'undefined' else layer['opacity']
  
    Map.addLayer(image, { palette: palette, min:0, max:2, opacity: opacity}, 
      layer.name, layer.visible, layer.opacity)


Map = {
  'addAsImage': func_addAsImage
} 

# exports.focalMin = function(image, radius) {
#   erosion = image.Not().fastDistanceTransform(radius).sqrt().lte(radius).Not()

#   return erosion
# }

# exports.focalMax = function(image, radius) {
#   dilation = image.fastDistanceTransform().sqrt().lte(radius)

#   return dilation
# }
  
# exports.focalMaxWeight = function(image, radius) {
#   distance = image.fastDistanceTransform(radius).sqrt()
#   dilation = distance.where(distance.gte(radius), radius)
  
#   dilation = ee.Image(radius).subtract(dilation).divide(radius)
  
#   return dilation
# }

# function getIsolines(image, opt_levels) {
#   addIso = function(image, level) {
#     crossing = image.subtract(level).focal_median(3).zeroCrossing()
#     exact = image.eq(level)
    
#     return ee.Image(level).float().mask(crossing.Or(exact)).set({level: level})
#   }
  
#   levels = opt_levels or ee.List.sequence(0, 1, 0.1)
  
#   levels = ee.List(levels)
  
#   isoImages = ee.ImageCollection(levels.map(function(l) {
#     return addIso(image, ee.Number(l))
#   }))

#   return isoImages
# }

# exports.getIsolines = getIsolines


# function addIsolines(image, levels) {
#   colors = ['f7fcf0','e0f3db','ccebc5','a8ddb5','7bccc4','4eb3d3','2b8cbe','0868ac','084081']

#   isoImages = getIsolines(image, levels)
  
#   isolinesLayer = ui.Map.Layer(isoImages.mosaic(), {min: 0, max: 1, palette: colors}, 'isolines', false, 0.3)
  
#   Map.layers().add(isolinesLayer)
# }

# exports.addIsolines = addIsolines


# #***
#  * Generates image collection gallery.
#  #
# function ImageGallery(images, region, rows, columns, options) {
#   throw('use: users/gena/packages:gallery')
# }

# exports.ImageGallery = ImageGallery


# #***
#  * Computes export video / image parameters: scale, rect.
#  #
# function generateExportParameters(bounds, w, h, crs, scale) {
#   crs = crs or 'EPSG:4326'
  
#   scale = scale or 10
  
#   bounds = ee.Geometry(bounds).bounds(scale).transform(crs, scale)
  
#   # get width / height
#   coords = ee.List(bounds.coordinates().get(0))
#   ymin = ee.Number(ee.List(coords.get(0)).get(1))
#   ymax = ee.Number(ee.List(coords.get(2)).get(1))
#   xmin = ee.Number(ee.List(coords.get(0)).get(0))
#   xmax = ee.Number(ee.List(coords.get(1)).get(0))
#   width = xmax.subtract(xmin)
#   height = ymax.subtract(ymin)

#   # compute new height, ymin, ymax and bounds
#   ratio = ee.Number(w).divide(h)
#   ycenter = ymin.add(height.divide(2.0))
#   xcenter = xmin.add(width.divide(2.0))
  
#   width = width.max(height.multiply(ratio))
#   height = height.max(width.divide(ratio))

#   ymin = ycenter.subtract(height.divide(2))
#   ymax = ycenter.add(height.divide(2))
#   xmin = xcenter.subtract(width.divide(2))
#   xmax = xcenter.add(width.divide(2))

#   bounds = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], crs, false)
  
#   scale = bounds.projection().nominalScale().multiply(width.divide(w))

#   return {scale: scale, bounds: bounds, width: width, height: height} 
# }

# exports.generateExportParameters = generateExportParameters

# #***
#  * Generates line features for line string
#  #
# function lineToPoints(lineString, count) {
#   length = lineString.length()
#   step = lineString.length().divide(count)
#   distances = ee.List.sequence(0, length, step)

#   function makePointFeature(coord, offset) {
#     pt = ee.Algorithms.GeometryConstructors.Point(coord)
#     return new ee.Feature(pt).set('offset', offset)
#   }
  
#   lines = lineString.cutLines(distances).geometries()

#   points = lines.zip(distances).map(function(s) {
#     line = ee.List(s).get(0)
#     offset = ee.List(s).get(1)
#     return makePointFeature(ee.Geometry(line).coordinates().get(0), offset)
#   })
  
#   points = points.add(makePointFeature(lineString.coordinates().get(-1), length))

#   return new ee.FeatureCollection(points)
# }

# exports.lineToPoints = lineToPoints

# #***
#  * Reduces image values along the given line string geometry using given reducer.
#  * 
#  * Samples image values using image native scale, or opt_scale
#  #
# function reduceImageProfile(image, line, reducer, scale, crs, buffer) {
#   length = line.length()
#   distances = ee.List.sequence(0, length, scale)
#   lines = line.cutLines(distances, ee.Number(scale).divide(5)).geometries()
#   lines = lines.zip(distances).map(function(l) { 
#     l = ee.List(l)
    
#     geom = ee.Geometry(l.get(0))
#     distance = ee.Number(l.get(1))
    
#     geom = ee.Algorithms.GeometryConstructors.LineString(geom.coordinates())
    
#     if(buffer) {
#       geom = geom.buffer(buffer, 1)
#     }
    
#     return ee.Feature(geom, {distance: distance})
#   })
#   lines = ee.FeatureCollection(lines)

#   # reduce image for every segment
#   values = image.reduceRegions( {
#     collection: ee.FeatureCollection(lines), 
#     reducer: reducer, 
#     scale: scale, 
#     crs: crs
#   })
  
#   return values
# }

# exports.reduceImageProfile = reduceImageProfile

# #*** 
# #  * Exports a video, annotates images if needed, previews a few frame.
#  #
# exports.exportVideo = function(images, options) {
#   label = (options and options.label) or None
#   bounds = (options and options.bounds) or Map.getBounds(true)
#   w = (options and options.width) or 1920
#   h = (options and options.height) or 1080
#   previewFrames = (options and options.previewFrames) or 0
#   maxFrames = (options and options.maxFrames) or 100
#   framesPerSecond = (options and options.framesPerSecond) or 5
#   name = (options and options.name) or 'ee-animation'
#   crs = 'EPSG:3857'
  
#   # expand bounds to ensure w/h ratio
#   p = generateExportParameters(bounds, w, h, crs)

#   if(label) {
#     annotations = [{
#       position: 'left', offset: '1%', margin: '1%', property: label, scale: ee.Number(p.scale).multiply(2)
#     }]
    
#     text = require('users/gena/packages:text')

#     images = images.map(function(i) {
#       return text.annotateImage(i, {}, p.bounds, annotations)
#     })
#   }

#   Export.video.toDrive({ 
#     collection: images, 
#     description: name, 
#     fileNamePrefix: name, 
#     framesPerSecond: framesPerSecond, 
#     dimensions: w, 
#     region: p.bounds,
#     maxFrames: maxFrames
#   })
  
#   if(previewFrames) {
#     frames = images.toList(previewFrames)
#     ee.List.sequence(0, ee.Number(previewFrames).subtract(1)).evaluate(function(indices) {
#       indices.map(function(i) {
#         image = ee.Image(frames.get(i)).clip(p.bounds)
#         Map.addLayer(image, {}, i.toString(), false)
#       })
#     })
#   }
# }
 
# # backward-compatibility 
# exports.addImagesToMap = function() {
#   throw "utils.addImagesToMap is obsolete, use require('users/gena/package:animation').animate(images) instead"
# }


# # returns random image with normally distributed values
# exports.norm = function(seed) {
#   seed = ee.Algorithms.If(ee.Algorithms.IsEqual(seed, None), 42, seed)
#   u1 = ee.Image.random(ee.Number(1000).add(seed))
#   u2 = ee.Image.random(ee.Number(2000).add(seed))

#   # https://en.wikipedia.Org/wiki/Box%E2%80%93Muller_transform
#   n = u1.log().multiply(-2).sqrt().multiply(u2.multiply(2 * Math.PI).cos())

#   return n
# }

# exports.generateHexagonalSeeds = function(size, crs, scale) {
#   crs = crs or 'EPSG:3857'

#   scale = scale or Map.getScale()
  
#   step = ee.Number(scale).multiply(size)

#   image1 = ee.Image.pixelCoordinates(crs)
#     .mod(ee.Image.constant([step.multiply(2), step.multiply(3)]))
#     .abs()
#     .gt(scale)
#     .reduce(ee.Reducer.anyNonZero())
#     .Not()

#   image2 = ee.Image.pixelCoordinates(crs).add(ee.Image.constant([step, step.multiply(1.5)]))
#     .mod(ee.Image.constant([step.multiply(2), step.multiply(3)]))
#     .abs()
#     .gt(scale)
#     .reduce(ee.Reducer.anyNonZero())
#     .Not()

#   return ee.Image([image1, image2]).reduce(ee.Reducer.anyNonZero())
# }

# function fillGaps(image, radius, iterations) {
#   function fillGapsSingle(image) {
#     fill = image //.where(image.mask().lt(1), image.convolve(ee.Kernel.gaussian(5, 3, 'meters')))
#       .reduceNeighborhood({
#         reducer: ee.Reducer.median(), 
#         kernel: ee.Kernel.circle(radius, 'meters'),
#         inputWeight: 'mask',
#         skipMasked: false
#       })
      
#     return image.unmask(fill)
#   }

#   result = ee.List.sequence(1, iterations).iterate(function(curr, prev) {
#     image = ee.Image(prev)
#     return fillGapsSingle(image)
#   }, image)
  
#   return ee.Image(result)
# }

# exports.fillGaps = fillGaps



# #***
#  * Timer
#  #
# function Timer() {
#   t = None
# }  

# Timer.prototype.start = function() {
#   this.t = Date.now()
  
#   return this
# }
  
# Timer.prototype.elapsed = function() {
#   return Date.now() - this.t
# }

# exports.Timer = Timer


# function getFolderImages(path) {
#   items = ee.data.getList({ id: path })
#   images = items.map(function(i) { return ee.Image(i.id) })
  
#   return ee.ImageCollection(images)
# }

# exports.getFolderImages = getFolderImages 

# #***
#  * Converts feature collection to DataTable compatible with charting API
#  #
# function featureCollectionToDataTable(features, xProperty) {
#   feature = ee.Feature(features.first())
#   propertyNames = feature.propertyNames().remove(xProperty).remove('system:index').insert(0, xProperty)

#   function toTableColumns(s) {
#     return {id: s, label: s, type: 'number', role: ee.Algorithms.If(ee.Algorithms.IsEqual(s, xProperty), 'domain', 'data') } 
#   }

#   columns = propertyNames.map(toTableColumns)

#   function featureToTableRow(f) {
#     return {c: propertyNames.map(function(c) { 
#         v = ee.Feature(f).get(c)

#         # v = ee.Algorithms.If(ee.Algorithms.IsEqual(v, None), '', v)
      
#         return {v: v}
#       })
#     }
#   }
  
#   rows = features.toList(5000).map(featureToTableRow)

#   return ee.Dictionary({cols: columns, rows: rows})
# }

# exports.featureCollectionToDataTable = featureCollectionToDataTable

# function range(count) {
#     a = []
#     for (i = 0 i < count i++) {
#         a.append(i)
#     }
#     return a
# }

# exports.range = range                                                                  

# function isCommandLine() {
#   try { 
#     commandLine 
#   }
#   catch(e) {
#       if(e.name == "ReferenceError") {
#           return false
#       }
#   }
  
#   return true
# }

# exports.isCommandLine = isCommandLine

# function stretchImage(image, options) {
#   percentiles = [0, 99]
#   bandNames = image.bandNames()
  
#   scale = 30
#   bounds = None
  
#   imageMask = image.select(0).mask()

#   if(options) {
#     if(options.percentiles) {
#       percentiles = options.percentiles
#     }
    
#     if(options.scale) {
#       scale = options.scale
#     } else {
#       scale = Map.getScale()
#     }

#     if(options.bounds) {
#       bounds = options.bounds
#     } else {
#       bounds = Map.getBounds(true)
#     }
    
#     if(options.max) {
#       imageMask = image.select(0).mask().multiply(image.lt(options.max).reduce(ee.Reducer.max()))
#     }
#   }
  
#   minMax = image.updateMask(imageMask).reduceRegion(**{
#     reducer: ee.Reducer.percentile(percentiles),
#     geometry: bounds, 
#     scale: scale
#   })
  
#   bands = bandNames.map(function(bandName) {
#     bandName = ee.String(bandName)
#     min = ee.Number(minMax.get(bandName.cat('_p').cat(ee.Number(percentiles[0]).format())))
#     max = ee.Number(minMax.get(bandName.cat('_p').cat(ee.Number(percentiles[1]).format())))
    
#     min = ee.Number(ee.Algorithms.If(ee.Algorithms.IsEqual(min, None), 0, min))
#     max = ee.Number(ee.Algorithms.If(ee.Algorithms.IsEqual(max, None), 1, max))
    
#     return image.select(bandName).subtract(min).divide(max.subtract(min).max(0.001))
#   })
  
#   areaNotMasked = ee.Image.pixelArea().updateMask(imageMask.Not()).reduceRegion(**{ reducer: ee.Reducer.sum(), geometry: bounds, scale: scale }).values().get(0)
#   area = ee.Image.pixelArea().updateMask(image.select(0).mask()).reduceRegion(**{ reducer: ee.Reducer.sum(), geometry: bounds, scale: scale }).values().get(0)
#   maskedFraction = ee.Number(areaNotMasked).divide(area)
  
#   return ee.ImageCollection(bands).toBands().rename(bandNames)
#     .set({ maskedFraction: maskedFraction })
# }

# exports.stretchImage = stretchImage
# #***
#  * k-fold cross validation
#  #
# function KFold(splits, randomState) {
#     this.splits = splits or 5
#     this.randomState = typeof (randomState) == 'undefined' or 42
# }

# #***
#  * Splits feature collection into k folds and return a list of pairs (training, validation) as dictionaries
#  #
# KFold.prototype.split = function (features) {
#     step = ee.Number(1).divide(this.splits)
#     thresholds = ee.List.sequence(0, ee.Number(1).subtract(step), step)

#     features = features.randomColumn('e', this.randomState)

#     return thresholds.map(function (threshold) {
#         return {
#             training: features.filter(ee.Filter.Or(
#                 ee.Filter.lt('e', threshold),
#                 ee.Filter.gte('e', ee.Number(threshold).add(step))
#             )),
#             validation: features.filter(ee.Filter.And(
#                 ee.Filter.gt('e', threshold),
#                 ee.Filter.lte('e', ee.Number(threshold).add(step))
#             ))
#         }
#     })
# }
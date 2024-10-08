#------------------------------------------------------------
# General helper functions for pre-processing of SAR data
# written by: Andreas Vollrath & Daniel Wiell, FAO - with generous support from Adugna Mulissa, WUR
# last edited: 09.01.2023
#------------------------------------------------------------

import ee
import geemap
import math

#------------------------------------------------------------
# Conversion functions to convert from/to dB

def getDataBands(bandlist, keepRatios):
  # This def will get allbands tha actually contain data 
  
  keepRatios = keepRatios or False
  
  # get bands that need to be removed
  toBeRemoved = bandlist.removeAll(['HH', 'HV', 'VH', 'VV'])
  
  if (keepRatios):
    toBeRemoved = toBeRemoved.removeAll(['HH_filtered_ratio', 'HV_filtered_ratio', 'VH_filtered_ratio', 'VV_filtered_ratio'])
  
  # use that list to only get data bands
  return bandlist.removeAll(toBeRemoved)



def addRatio(image, power):
  # a generic def that adds the power ratio
  
  # get band names for co- and cross-pol channels
  bands = getDataBands(image.bandNames())
  
  # extract co- and crosspol, and construct a band name
  coPolBand = ee.String(bands.removeAll(['HV', 'VH']).get(0))
  crossPolBand = ee.String(bands.removeAll(['HH', 'VV']).get(0))
  ratioBandName = coPolBand.cat('_').cat(crossPolBand).cat('_ratio')
  
  # apply ratio based on log or power and return as added band to base image
  if (power):
    return image.addBands(
      image.select(coPolBand).divide(image.select(crossPolBand)).rename(ratioBandName)
    )
  
  else:
    return image.addBands(
      image.select(coPolBand).subtract(image.select(crossPolBand)).rename(ratioBandName)
    )
  

def addNormalizedRatio(image):
  
  # get band names for co and cross-pol channels
  bands = getDataBands(image.bandNames())
  
  # extract co- and crosspol, and construct a band name
  coPolBand = ee.String(bands.removeAll(['HV', 'VH']).get(0))
  crossPolBand = ee.String(bands.removeAll(['HH', 'VV']).get(0))
  ratioBandName = coPolBand.cat('_').cat(crossPolBand).cat('_ND_ratio')
  
  # return image with added ND band
  return image.addBands(image.normalizedDifference([coPolBand, crossPolBand]).rename(ratioBandName))



def addDateBands(image):
  date = image.date()
  day_of_year = date.getRelative('day', 'year')
  millisPerDay = 1000 * 60 * 60 * 24
  unix_time_days = date.millis().divide(millisPerDay)
  years = date.difference(ee.Date('1970-01-01'), 'year')
  return (image
      .addBands(ee.Image(day_of_year).uint16().rename('dayOfYear'))
      .addBands(ee.Image(unix_time_days).uint16().rename('unixTimeDays'))
      .addBands(ee.Image(years).rename('t')).float())


#------------------------------------------------------------
# Conversion functions to convert from/to dB
def toNatural(image):
  # from decibel to natural
  
  # get data bands
  bands = getDataBands(image.bandNames())
  nat = ee.Image(10.0).pow(image.select(bands).divide(10.0)).rename(bands)
  return image.addBands(nat, None, True)


def toDecibel(image):
  # from natural to decibel
  
  # get data bands
  bands = getDataBands(image.bandNames())
  db = image.select(bands).log10().multiply(10).rename(bands)
  return image.addBands(db, None, True)


# sigma0 to gamma0 conversion, based on Incidence Angle
def sigma2gamma(image, angleBand):
  
  bands = getDataBands(image.bandNames())
  gamma0 = image.expression('i/(cos(angle * pi / 180))', {
          'i': image.select(bands),
          'angle': image.select(angleBand),
          'pi': ee.Number(math.PI)
      })
  return image.addBands(gamma0, None, True)

#------------------------------------------------------------


#------------------------------------------------------------
# multi-temporal
def removeOutliers2(collection, stdDevs):

  # get data bands
  bands = getDataBands(collection.first().bandNames())
  
  # get stats over time
  stats  = collection.select(bands).reduce({
    'reducer': ee.Reducer.median().combine(ee.Reducer.stdDev(), '', True),
    'parallelScale': 4
  })
  
  # get stdDev over time
  median = stats.select('.*median').rename(bands)
  stdDev = stats.select('.*stdDev').rename(bands)
  
  # now mask based on stdDevs
  def func_std(image):
    
    value = image.select(bands)
    mask = value.subtract(median).abs().lte(stdDev.multiply(stdDevs)).reduce(ee.Reducer.min())
    
    return image.addBands(image.select(bands).updateMask(mask), None, True)
  

  return collection.map(func_std)



#------------------------------------------------------------
#multi-temporal
def removeOutliers(collection):

  # get data bands
  bands = getDataBands(collection.first().bandNames())
  s1_perc = collection.select(bands).reduce({'reducer': ee.Reducer.percentile([1,99]), 'parallelScale':4})
  def func_dbs(image):
    _image = image.select(bands)
    return image.addBands(
      _image.updateMask(_image.gt(s1_perc.select('.*p1')).And(_image.lt(s1_perc.select('.*p99')))), 
      None, True)
  return collection.map(func_dbs)

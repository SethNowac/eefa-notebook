import ee 
import math
import geemap
import geemap.chart as chart

Map = geemap.Map()

# BAP____________________________________________________________________________________________________________
doc = 'This is the BAP library'

# getCollection functions________________________________________________________________________________________

def func_roo(img, sensor):
    img = ee.Image(img)
    cloudM = None

    qualityBand = img.select('pixel_qa')
    shadow = qualityBand.bitwiseAnd(8).neq(0);  
    cloud = qualityBand.bitwiseAnd(32).neq(0);  

    # Cloud confidence is comprised of bits 6-7.
    # Add the two bits and interpolate them to a range from 0-3.
    # 0 = None, 1 = Low, 2 = Medium, 3 = High.
    cloudConfidence = qualityBand.bitwiseAnd(64) \
    .add(qualityBand.bitwiseAnd(128)) \
    .interpolate([0, 64, 128, 192], [0, 1, 2, 3], 'clamp').int()
    cloudConfidenceMediumHigh = cloudConfidence.gte(2)

    cloudM = shadow.Or(cloud).Or(cloudConfidenceMediumHigh) \
    .select([0], ['cloudM'])

    # add cirrus confidence to cloud mask (cloudM)
    if (sensor == 'LC08'):
            cirrusConfidence = qualityBand.bitwiseAnd(256) \
            .add(qualityBand.bitwiseAnd(512)) \
            .interpolate([0, 256, 512, 768], [0, 1, 2, 3], 'clamp').int()
            cirrusConfidenceMediumHigh = cirrusConfidence.gte(2)
            cloudM = cloudM.Or(cirrusConfidenceMediumHigh)


    cloudM = cloudM.Not();  

    # mask image with cloud mask
    imageCloudMasked = img.mask(img.mask(cloudM));  

    # add cloud mask as band
    imageCloudMasked = imageCloudMasked.addBands(cloudM)

    return imageCloudMasked

cloudMask = func_roo


def func_vjj(I_aoi, sensor, I_cloudThreshold, SLCoffPenalty):

    collection = ee.ImageCollection('LANDSAT/'+sensor+'/C01/T1_SR')

    bands = None
    SensorBand = None
    collectionFiltered = None
    if (sensor == 'LT05'):
            bands = ['B1',   'B2',    'B3',  'B4',  'B5',  'B7', 'pixel_qa', 'sr_atmos_opacity']
            SensorBand = 5
            collectionFiltered = collection.filterMetadata('CLOUD_COVER', 'less_than', I_cloudThreshold) \
            .select(bands, ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'pixel_qa', "opacity"])

    if (sensor == 'LE07'):
            bands = ['B1',   'B2',    'B3',  'B4',  'B5',  'B7', 'pixel_qa', 'sr_atmos_opacity']
            SensorBand = 7
            collectionFiltered = collection.filterMetadata('CLOUD_COVER', 'less_than', I_cloudThreshold) \
            .select(bands, ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'pixel_qa', "opacity"])

    if (sensor == 'LC08'):
            bands = ['B2',   'B3',    'B4',  'B5',  'B6',  'B7', 'pixel_qa']
            SensorBand = 8
            collectionFiltered = collection.filterMetadata('CLOUD_COVER', 'less_than', I_cloudThreshold) \
            .select(bands, ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'pixel_qa',])
            # add dummy opacity band

            def func_ika(img):
                    return img.addBands(ee.Image(250).int16().rename(["opacity"]))

            collectionFiltered = collectionFiltered.map(func_ika)




    if (I_aoi != None):
            collectionFiltered = collectionFiltered.filterBounds(ee.FeatureCollection(I_aoi))


    # Add a band with the sensor on each image in the image collection

    def func_pag(image):
            image = ee.Image(image)
            SensorImage = ee.Image(SensorBand).select([0], ['sensor']).int16()
            return image.addBands(SensorImage)

    collectionFilteredWithSensor = collectionFiltered.map(func_pag)





    # Add band with sensorWeight
    collectionFilteredWithSensorAndSensorWeight = None

    # prepare SLCoff score
    SLCoffScore = ee.Number(1000).subtract(ee.Number(SLCoffPenalty).multiply(1000))

    if (sensor == 'LE07'):

            # note that sensor weights are muptiplied by 10 here to obatin int16() bands
            # Will be rescaled before the final score calculation
            SLCoffCollection = collectionFilteredWithSensor.filter(ee.Filter.date('2003-05-31', "2030-01-01"))
            SLConCollection = collectionFilteredWithSensor.filter(ee.Filter.date('1984-01-01', '2003-05-31'))


            def func_rmz(image):
                    image = ee.Image(image)
                    SensorWeightImage = ee.Image(1000).select([0], ['sensorScore']).int16()
                    return image.addBands(SensorWeightImage)

            SLConCollection = SLConCollection.map(func_rmz)

            def func_hdu(image):
                    image = ee.Image(image)
                    SensorWeightImage = ee.Image(SLCoffScore).select([0], ['sensorScore']).int16()
                    return image.addBands(SensorWeightImage)

            SLCoffCollection = SLCoffCollection.map(func_hdu)

            collectionFilteredWithSensorAndSensorWeight = SLCoffCollection.merge(SLConCollection)
    else:
            def func_hqx(image):
                        image = ee.Image(image)
                        SensorWeightImage = ee.Image(1000).select([0], ['sensorScore']).int16()
                        return image.addBands(SensorWeightImage)

            collectionFilteredWithSensorAndSensorWeight = collectionFilteredWithSensor.map(func_hqx)

    return ee.ImageCollection(collectionFilteredWithSensorAndSensorWeight)

FilterAndAddSensorBands = func_vjj


def getCollection(I_aoi, I_cloudThreshold, SLCoffPenalty):
  
    # create collections
    LT5 = FilterAndAddSensorBands(I_aoi, 'LT05', I_cloudThreshold, SLCoffPenalty) 
    LE7 = FilterAndAddSensorBands(I_aoi, 'LE07', I_cloudThreshold, SLCoffPenalty)
    LC8 = FilterAndAddSensorBands(I_aoi, 'LC08', I_cloudThreshold, SLCoffPenalty)
    
    # remove clouds
    def func_cr1(image): return cloudMask(image, 'LT05')
    def func_cr2(image): return cloudMask(image, 'LE07')
    def func_cr3(image): return cloudMask(image, 'LC08')
    
    LT5cloudsMasked = LT5.map(func_cr1); 
    LE7cloudsMasked = LE7.map(func_cr2); 
    LC8cloudsMasked = LC8.map(func_cr3); 
    
    return ee.ImageCollection(LT5cloudsMasked.merge(LE7cloudsMasked).merge(LC8cloudsMasked))

# createBAPcomposites functions__________________________________________________________________________________
def calculateCloudWeightAndDist(imageWithCloudMask, cloudDistMax):

    cloudM = imageWithCloudMask.select('cloudM').unmask(0).eq(0)
    nPixels = ee.Number(cloudDistMax).divide(30).toInt()
    cloudDist = cloudM.fastDistanceTransform(nPixels, "pixels",  'squared_euclidean')
    # fastDistanceTransform max distance (i.e. 50*30 = 1500) is approzimate. Correcting it...
    cloudDist = cloudDist.where(cloudDist.gt(ee.Image(cloudDistMax)), cloudDistMax)
  
    deltaCloud = (ee.Image(1).toDouble().divide((ee.Image(ee.Number(-0.008)) 
    .multiply(cloudDist.subtract(ee.Number(cloudDistMax/2)))).exp().add(1)) 
    .unmask(1) 
    .select([0], ['cloudScore']))
    
    cloudDist = ee.Image(cloudDist).int16().rename('cloudDist')

    keys = ['cloudScore', 'cloudDist']
    values = [deltaCloud, cloudDist]
    
    return ee.Dictionary.fromLists(keys, values)


def func_pfj(imageWithOpacityBand, opacityScoreMin, opacityScoreMax):

    opacity = imageWithOpacityBand.select('opacity').multiply(0.001)

    opacityScore = ee.Image(1).subtract(ee.Image(1).divide(ee.Image(1).add(
    ee.Image(-0.2).multiply(opacity.subtract(ee.Image(0.05))).exp() 
    )))

    # opacity smaller than 0.2 -> score = 1
    opacityScore = opacityScore.where(opacity.lt(ee.Image(opacityScoreMin)), 1)
    # opacity larger than 0.3 -> score = 0
    opacityScore = opacityScore.where(opacity.gt(ee.Image(opacityScoreMax)), 0)
    #return opacity.rename(["opacityScore"])
    return opacityScore.rename(["opacityScore"])

calculateOpacityWeight = func_pfj


def func_lrg(image, I_targetDay):
    image = ee.Image(image)

    Year_i = image.date().get("year")
    targetDate =  ee.Date(ee.String(ee.Number(Year_i)) \
    .cat(ee.String("-")) \
    .cat(ee.String(I_targetDay)))
    eeDateImage = ee.Date(image.get('system:time_start'))

    deltaDay = ((ee.Number(0.01049848)) \
    .multiply(ee.Number(math.e).pow(ee.Number(-0.5) \
    .multiply (((eeDateImage.difference(targetDate, 'day')).divide(38)).pow(2))))) \
    .divide(0.01049848); 

    # create doy band
    dayOfYearImage = eeDateImage.getRelative('day', 'year')

    doy = ee.Image(1).add(dayOfYearImage) \
    .mask(image.select('cloudM')) \
    .int16().select([0], ['doy'])

    # deltaDayImg
    deltaDayImg = ee.Image(deltaDay).rename(["doyScore"])

    keys = ['doyScore', 'doy']

    # convert delta Day to image and add
    values = [deltaDayImg, doy]

    return ee.Dictionary.fromLists(keys, values)

calculateDayWeightAndDoy = func_lrg


def func_lcz(collection, I_targetDay, opacityScoreMin, opacityScoreMax, cloudDistMax):

    # returns an image with the delta (quality) band.

    def func_pvo(image):
            image = ee.Image(image)

            # distance to I_targetDay
            deltaDayAndDoy = calculateDayWeightAndDoy(image, I_targetDay)
            doy = ee.Image(deltaDayAndDoy.get('doy'))
            doyScore = ee.Image(deltaDayAndDoy.get('doyScore'))

            # opacity score
            opacityScore = calculateOpacityWeight(image, opacityScoreMin, opacityScoreMax)
            # mask the image where the opacity score is 0
            image = image.updateMask(opacityScore)

            # cloud distance
            deltaCloudAndDist = calculateCloudWeightAndDist(image, cloudDistMax)
            cloudDist = ee.Image(deltaCloudAndDist.get('cloudDist'))
            cloudScore = ee.Image(deltaCloudAndDist.get('cloudScore'))

            # sensor weight
            deltaSensor = ee.Image(image.select('sensorScore'))

            # create delta band based on weights
            score = doyScore \
            .add(cloudScore) \
            .add(deltaSensor.divide(1000)) \
            .add(opacityScore) \
            .divide(4) \
            .multiply(1000) \
            .select([0], ['score']).int16()

            # Add information bands
            imageWithBands = image.addBands(doy).addBands(doyScore.multiply(1000)).addBands(cloudDist) \
            .addBands(cloudScore.multiply(1000)) \
            .addBands(opacityScore.multiply(1000)).addBands(score)

            # Return the image and remove the cloud mask 'cloudM' and pixel_qa
            imageWithBands = imageWithBands.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2',
            'sensor', 'sensorScore', 'doy', "doyScore",
            'cloudDist', "cloudScore", "opacityScore", 'score']).int16()
            return imageWithBands

    addDoyAndDeltaBandToImage = func_pvo







































    

    # apply addDoyAndDeltaBandToImage to each image in collection

    def func_iwp(image):
            return addDoyAndDeltaBandToImage(image)

    collectionWithWeightsBands = collection.map(func_iwp)



    return collectionWithWeightsBands

addWeightBandsToCollection = func_lcz

def createBAPcomposites(collection, I_targetDay, I_daysRange, opacityScoreMin, opacityScoreMax, cloudDistMax):
  
    I_startYear = 1984                              
    I_endYear   = 2021

    # add day of year and delta (quality) bands to each image of the collection 
    collection = addWeightBandsToCollection(collection, I_targetDay, opacityScoreMin, opacityScoreMax, cloudDistMax)

    # create list of years for which generating the BAP
    years = ee.List.sequence(I_startYear, I_endYear)

    def filterAndComposite(year):

        yearString = ee.String(str(year)).slice(0,4)   # remove unnecessary .0 which is added by string conversion

        I_targetDayAdjusted = ee.Date(yearString.cat('-').cat(ee.String(I_targetDay)))
 
        startDateWithYear =  I_targetDayAdjusted.advance(-I_daysRange, "day")
        endDateWithYear   =  I_targetDayAdjusted.advance(I_daysRange, "day")

        filteredCollectionByDate = ee.ImageCollection(collection.filterDate(startDateWithYear, endDateWithYear))

        dateString = yearString.cat("-").cat(I_targetDay)

        def calculateAndStackComposite(filteredCollectionByDate):
     
            def func_udm(img): return img.updateMask(img.select([0, 1, 2, 3, 4, 5]).reduce(ee.Reducer.min()))

            filteredCollectionByDate = filteredCollectionByDate \
            .map(func_udm)
            # mosaic collection with delta band
            composite = filteredCollectionByDate.qualityMosaic('score')

            # mask missing values
            # composite = composite.updateMask(composite)
            composite = composite.updateMask(composite.select([0, 1, 2, 3, 4, 5]).reduce(ee.Reducer.min()))

            # select output bands 
            #composite = composite.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 
            #                            'sensor', 'sensorScore', 'doy', "doyScore", 
            #                            'cloudDist', "cloudScore", 'score']).int16();

            #  composite = composite.set('system:time_start', dateString);
            composite = composite.set({
            'system:time_start': ee.Date(dateString).millis(),
            'system:id': dateString
            })
            return composite
        # end calculateAndStackComposite()

        return ee.Algorithms.If(
            condition = filteredCollectionByDate.size().gt(0),
            trueCase = calculateAndStackComposite(filteredCollectionByDate),
            falseCase = ee.Image.cat(0,0,0,0,0,0,0,0,0,0,0,0,0,0).int16() \
                .rename(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'sensor', 'sensorScore', 
                    'doy', "doyScore", 'cloudDist', "cloudScore", "opacityScore", 'score']) \
                    .set({'system:time_start': ee.Date(dateString).millis(),'system:id': dateString})
        )
  
    # out = years.iterate(filterAndComposite, BAPCollection)
    out = ee.List.sequence(I_startYear, I_endYear)
    for i in range(len(years.getInfo())):
        out.set(i, filterAndComposite(years.getInfo()[i]))
        

  
    return ee.ImageCollection(out)

def BAP(I_aoi, I_targetDay, I_daysRange, I_cloudThreshold, 
                   SLCoffPenalty, opacityScoreMin, opacityScoreMax, cloudDistMax):
                     
    collection = getCollection(I_aoi, I_cloudThreshold, SLCoffPenalty)#, opacityScoreMin, opacityScoreMax)
    return createBAPcomposites(collection, I_targetDay, I_daysRange, opacityScoreMin, opacityScoreMax, cloudDistMax)


# Despike function_______________________________________________________________________________________________

def func_ixm (DespikeThreshold, NbandsThreshold, collection, I_startYear, I_endYear, I_maskSpikes):

    # select Landsat bands to detect outliers and spikes
    # collection = collection.select([0, 1, 2, 3, 4, 5])

    # count the number of images in the collection
    nImages = (I_endYear-I_startYear)+1

    # Produce a list -> 1:(nImages-2)
    # This list exclude the first (0) and the last (nImages-1) images
    ImagesToDespikeList = ee.List.sequence(1, nImages-2)

    # Convert image collection into list to get elements iteratively
    collectionList = collection.toList(nImages)

    # DespikeImage function

    def func_dmo(nImg):

            # to ee object
            nImgEE = ee.Number(nImg)
            oneEE  = ee.Number(1)

            # for each image (ImgY) three images are required:
            ImgYbefore = ee.Image(collectionList.get(nImgEE.subtract(oneEE))).int16().select([0, 1, 2, 3, 4, 5])
            ImgY = ee.Image(collectionList.get(nImgEE)).int16().select([0, 1, 2, 3, 4, 5])
            ImgYafter = ee.Image(collectionList.get(nImgEE.add(oneEE))).int16().select([0, 1, 2, 3, 4, 5])

            # Despike conditions
            # #1# "The value of the spilke detected in that band is greater than 100"
            spike_value = ImgY.subtract(ImgYbefore.add(ImgYafter).divide(2)).abs()
            condition1 = spike_value.gt(100)

            # #2# "spikes are dampened if the spectral value difference between spectral values on either side
            # of the spike is less than 1-despike desawtooth proportion of the spike itself" (Landtrendr)
            despikeProportion = ImgYbefore.subtract(ImgYafter).abs().divide(spike_value)
            condition2 = despikeProportion.lt(ee.Image(1).subtract(DespikeThreshold))

            # #3# The number of bands in which condition 1 AND 2 are meet is greater than NbandsThreshold
            condition1ANDcondition2 = condition1.And(condition2)
            nBandsInWhichcondition1ANDcondition2 = condition1ANDcondition2.reduce(ee.Reducer.sum())
            detectedSpiked = nBandsInWhichcondition1ANDcondition2.gte(NbandsThreshold).rename('spikes') \
            .updateMask(ImgYbefore.select([0]).unmask(0)) \
            .updateMask(ImgYafter.select([0]).unmask(0))

            # Prepare a cloudMask
            cloudMask = ImgY.select(["red"]).unmask(0)

            if (I_maskSpikes==True):
                        # noiseLayer
                        despikeMask = detectedSpiked.unmask(0).eq(0); 
                        # Apply the noiseLayer
                        ImgY = ee.Image(collectionList.get(nImgEE)).int16().updateMask(despikeMask)


            # produce an image to point the despiked pixels: 1 = despiked, 0 = validpixels, 2 = clouds
            noiseLayer = detectedSpiked.unmask(0).updateMask(cloudMask).unmask(2).int16().rename('noiseLayer')

            return ImgY.addBands(noiseLayer)

    DespikeImage = func_dmo

    # Apply DespikeImage function over the collection
    DespikedCollection =  ee.ImageCollection(ImagesToDespikeList.map(DespikeImage))

    # Add first and last images
    firstImage = ee.Image([collectionList.get(ee.Number(0))])
    firstImageNoiseLayer = firstImage.select([0]).unmask(0).eq(0).multiply(2).int16().rename("noiseLayer")
    firstImage = firstImage.addBands(firstImageNoiseLayer)
    lastImage = ee.Image([collectionList.get(ee.Number(nImages-1))])
    lastImageNoiseLayer = lastImage.select([0]).unmask(0).eq(0).multiply(2).int16().rename("noiseLayer")
    lastImage = lastImage.addBands(lastImageNoiseLayer)

    return ee.ImageCollection(firstImage).merge(DespikedCollection).merge(lastImage)

despikeCollection = func_ixm

# calculateProxyCollection________________________________________________________________________
def infill(collection, I_startYear, I_endYear, image, justFill):
    # collection must have a "noiseLayer" band in which "0" points valid observations
    # the first band of imagery in collection must be the year
    # image may have as many bands as many imagery are in collection
    # Each band should be a mask pointing with values greather than 0
    # pixels that should be used to interpolate (e.g. the C2C "duration" band)
    # if img = false a linear interpolation is performed
    # if justFill = true the function is applied just on data gaps. 
    bandNames = collection.first().select([0, 1, 2, 3, 4, 5]).bandNames()
    def func_cb1(img):
        yr = (ee.Image(ee.Date(img.get('system:time_start')).get("year"))
                            .select([0], ['year']) 
                            .int16()
                            .set('system:time_start', img.get('system:time_start'))
                            .set('system:id', img.get('system:id')))
        return yr.addBands(img)

    collection2 = collection.map(func_cb1) # add year band
    def maskCollection(collection, image):
        collectionList = collection.toList(9999)
        ids = ee.List.sequence(1, collectionList.size().subtract(1))
        def maskImage(id):
            img = ee.Image(collectionList.get(id))
            mask = ee.Image(image.select([id]))
            return img.updateMask(mask)

        return ee.ImageCollection(collection.first()) \
        .merge(ee.ImageCollection(ids.map(maskImage)))
    # mask collection using image function
    if (image != False):
        collection2 = maskCollection(collection2, image) # use maskCollection()

    def linearInterpolation(year):
        year = ee.Number(year)
        currentImage         = collection.filter(ee.Filter.calendarRange(year, year, "year")).first()
        previousCollection   = collection2.filter(ee.Filter.calendarRange(I_startYear, year.subtract(1), "year"))
        subsequentCollection = collection2.filter(ee.Filter.calendarRange(year.add(1), I_endYear, "year"))
        beforeImage          = previousCollection.reduce(ee.Reducer.lastNonNull())
        nextImage            = subsequentCollection.reduce(ee.Reducer.firstNonNull())
        difference = nextImage.select([1, 2, 3, 4, 5, 6]).subtract(beforeImage.select([1, 2, 3, 4, 5, 6]))
        yearsProp = (ee.Image(year).subtract(beforeImage.select([0]))) \
        .divide(nextImage.select([0]).subtract(beforeImage.select([0])))
        proxyImage = beforeImage.select([1, 2, 3, 4, 5, 6]).add(difference.multiply(yearsProp)).rename(bandNames)
        if (justFill):
            return (currentImage.select(0, 1, 2, 3, 4, 5).unmask(0).where(currentImage.select(["noiseLayer"]).neq(0), proxyImage)
            .set('system:time_start', currentImage.get('system:time_start'))
            .set('system:id', ee.String(year).slice(0,4)))
        else:
            return proxyImage.set('system:time_start', currentImage.get('system:time_start')) \
            .set('system:id', ee.String(year).slice(0,4))
        
    linearInterpolated = ee.ImageCollection(ee.List.sequence(I_startYear+1, I_endYear-1).map(linearInterpolation))
    firstImage = collection.filter(ee.Filter.calendarRange(I_startYear, I_startYear, "year")).first() \
    .set('system:id', ee.String(ee.Number(I_startYear)).slice(0,4))
    lastImage  = collection.filter(ee.Filter.calendarRange(I_endYear, I_endYear, "year")).first() \
    .set('system:id', ee.String(ee.Number(I_endYear)).slice(0,4))
    firstExtrapolated = firstImage.select([0, 1, 2, 3, 4, 5]).unmask(0) \
    .where(firstImage.select(["noiseLayer"]).neq(0), linearInterpolated.reduce(ee.Reducer.firstNonNull()))
    lastExtrapolated = lastImage.select([0, 1, 2, 3, 4, 5]).unmask(0) \
    .where(lastImage.select(["noiseLayer"]).neq(0), linearInterpolated.reduce(ee.Reducer.lastNonNull()))
    return ee.ImageCollection(firstExtrapolated).merge(linearInterpolated).merge(lastExtrapolated)

# Function to calculate several indices and select bands_________________________________________________________

def func_qsx(collection, index, reverseIndex, skipeNoiseLayer):


    def func_itk(img):

            imgSpectralBands = img.select([0,1,2, 3, 4, 5])

            out = None

            if (index == "NDVI"):
                        NDVI = imgSpectralBands.normalizedDifference(['nir', 'red']) \
                        .rename('NDVI') \
                        .multiply(1000).int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        out = NDVI


            if (index == "EVI"):
                        EVI = ee.Image(0).expression(
                        '2.5 * ((float(NIR - RED) / float((NIR) + (6.0 * RED - 7.5 * BLUE) + 1.0)))',{
                                    'NIR': imgSpectralBands.select('nir'),
                                    'RED': imgSpectralBands.select('red'),
                                    'BLUE': imgSpectralBands.select('blue')
                                }) \
                        .rename('EVI') \
                        .multiply(1000).int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        out = EVI


            if (index == "NBR"):
                        nbr = imgSpectralBands.normalizedDifference(['nir', 'swir2']) \
                        .multiply(1000) \
                        .select([0], ['NBR']) \
                        .int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        # img = img.addBands(nbr)
                        out = nbr


            if (index == "TCB"):
                        brt_coeffs = ee.Image.constant([0.2043, 0.4158, 0.5524, 0.5741, 0.3124, 0.2303])
                        brightness = imgSpectralBands.multiply(brt_coeffs).reduce(ee.Reducer.sum()) \
                        .rename(["TCB"]).int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        # img = img.addBands(brightness)
                        out = brightness


            if (index == "TCG"):
                        grn_coeffs = ee.Image.constant([-0.1603, -0.2819, -0.4934, 0.7940, -0.0002, -0.1446])
                        greenness = imgSpectralBands.multiply(grn_coeffs).reduce(ee.Reducer.sum()) \
                        .rename(["TCG"]).int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        # img = img.addBands(greenness)
                        out = greenness


            if (index == "TCW"):
                        wet_coeffs = ee.Image.constant([0.0315, 0.2021, 0.3102, 0.1594, -0.6806, -0.6109])
                        wetness = imgSpectralBands.multiply(wet_coeffs).reduce(ee.Reducer.sum()) \
                        .rename(["TCW"]).int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        # img = img.addBands(wetness)
                        out = wetness


            if (index == "TCA"):
                        grn_coeffs = ee.Image.constant([-0.1603, -0.2819, -0.4934, 0.7940, -0.0002, -0.1446])
                        greenness = imgSpectralBands.multiply(grn_coeffs).reduce(ee.Reducer.sum())
                        brt_coeffs = ee.Image.constant([0.2043, 0.4158, 0.5524, 0.5741, 0.3124, 0.2303])
                        brightness = imgSpectralBands.multiply(brt_coeffs).reduce(ee.Reducer.sum())
                        angle = (greenness.divide(brightness)).atan().multiply(180/math.pi).multiply(100) \
                        .rename(["TCA"]).int16() \
                        .set('system:time_start', imgSpectralBands.get('system:time_start')) \
                        .set('system:id', imgSpectralBands.get('system:id'))
                        # img = img.addBands(angle)
                        out = angle


            if (index == 'blue') : out = img.select(['blue'])
            if (index == 'green'): out = img.select(['green'])
            if (index == 'red')  : out = img.select(['red'])
            if (index == 'nir')  : out = img.select(['nir'])
            if (index == 'swir1'): out = img.select(['swir1'])
            if (index == 'swir2'): out = img.select(['swir2'])

            if (reverseIndex):
                        out = out.multiply(-1).int16()


            yr = ee.Image(ee.Date(img.get('system:time_start')).get("year")) \
            .select([0], ['year']) \
            .int16() \
            .set('system:time_start', img.get('system:time_start')) \
            .set('system:id', img.get('system:id'))

            if (skipeNoiseLayer):
                        return ee.Image(yr.addBands(out))
            else:
                noiseLayer = img.select(["noiseLayer"])
                return ee.Image(yr.addBands(out).addBands(noiseLayer))


    SelectBandsAndAddIndicesImg = func_itk

    return ee.ImageCollection(collection.map(SelectBandsAndAddIndicesImg))


SelectBandsAndAddIndices = func_qsx

# mapping and export functions___________________________________________________________________________________
def ShowCollection(collection,I_startYear,I_endYear,I_aoi,I_showMissingData,I_band,minCol,maxCol):
    # Create viridis palette
    viridis = [
    "#440154FF", "#460A5DFF", "#471366FF", "#481C6EFF", "#482475FF", "#472C7AFF",
    "#46337FFF", "#443A84FF", "#414287FF", "#3E4989FF", "#3C508BFF", "#39578CFF",
    "#355E8DFF", "#32648EFF", "#306A8EFF", "#2D708EFF", "#2B768EFF", "#287C8EFF",
    "#26828EFF", "#24878EFF", "#228D8DFF", "#20938CFF", "#1F998AFF", "#1F9F88FF",
    "#20A486FF", "#25AA83FF", "#2AB07FFF", "#32B67AFF", "#3BBB75FF", "#47C06FFF",
    "#53C568FF", "#60CA60FF", "#6ECE58FF", "#7DD250FF", "#8CD645FF", "#9CD93BFF",
    "#ADDC30FF", "#BDDF26FF", "#CEE11DFF", "#DEE318FF", "#EEE51CFF", "#FDE725FF"
    ]
    # Map.setOptions("HYBRID")
    for year_i in range(I_startYear, I_endYear + 1):
        image = collection.filter(
        ee.Filter.calendarRange(ee.Number(year_i), ee.Number(year_i), "year")).first()
        if(I_aoi != None): image = image.clip(I_aoi)
        if (I_band == None):
            if (I_showMissingData):image = image.unmask(0) # if I_showMissingData = TRUE then use unmask to show missing data as black pixels
            Map.addLayer(ee_object=image,vis_params= {"bands":['red', 'green', 'blue'],"min":0,"max":2000},name= str(year_i))
        else:
            idx = image.select(I_band).unitScale(minCol, maxCol)
            Map.addLayer(ee_object= idx,vis_params= {"palette": viridis},name= str(year_i))

    # end loop

def Downloadcollection(collection,bandsToDownload,I_startYear,I_endYear,region,foldername):
    for year_i in range(I_startYear, I_endYear + 1):
        image = collection.filter(ee.Filter.calendarRange(ee.Number(year_i), ee.Number(year_i), "year")).first();
        if (bandsToDownload!=None): image = image.select(bandsToDownload)
        region_info = region.getInfo()
        dimensions = region_info.bands[0].dimensions[0]+"x"+region_info.bands[0].dimensions[1]
        crs_transform = region_info.bands[0].crs_transform
        geemap.ee_export_image_to_drive(image = image.int16(), description = str(year_i), folder = foldername, maxPixels = 1e13,
                            dimensions = dimensions,crs = region.projection().crs(), crsTransform = crs_transform)


def DownloadCollectionAsImage(collection, imageAoi, bandName, startYear, endYear, folderName):
    collection = collection.filter(ee.Filter.calendarRange(ee.Number(startYear), ee.Number(endYear), "year"))
    def func_lke(image): return ee.String(ee.Image(image).get('system:id'))
    bandNames = collection.toList(999).map(func_lke)
    imageToDownload = collection.select([bandName]).toBands().rename(bandNames)
    region_info = imageAoi.getInfo()
    dimensions = region_info.bands[0].dimensions[0]+"x"+region_info.bands[0].dimensions[1]
    crs_transform = region_info.bands[0].crs_transform
    geemap.ee_export_image_to_drive(image= imageToDownload,description= bandName,fileNamePrefix= bandName,folder= folderName,
                            maxPixels= 1e13,dimensions= dimensions,crs= imageAoi.projection().crs(),crsTransform= crs_transform)
    #  Export.image.toAsset({image: imageToDownload.regexpRename('^(.*)', 'b_$1'),
    #                        description: bandName+"ToAssets",
    #                        assetId: bandName,
    #                        maxPixels: 1e13,
    #                        dimensions: dimensions,
    #                        crs: imageAoi.projection().crs(),
    #                        crsTransform: crs_transform
    #                        });


# deprecated?
def DownloadImage(image, imageAoi, bandNames, filename, folderName):
    if (bandNames!=None):image = image.select(bandNames)
    image = image.int16()
    region_info = imageAoi.getInfo()
    dimensions = region_info.bands[0].dimensions[0]+"x"+region_info.bands[0].dimensions[1]
    crs_transform = region_info.bands[0].crs_transform
    geemap.ee_export_image_to_drive(image= image,
                        description= filename,#+"ToDrive",
                        folder= folderName,
                        maxPixels= 1e13,
                        dimensions= dimensions,
                        crs= imageAoi.projection().crs(),
                        crsTransform= crs_transform
                        )
    geemap.ee_export_image_to_drive(image= image,
                        description= filename+"ToAssets",
                        assetId= filename,
                        maxPixels= 1e13, 
                        dimensions= dimensions,
                        crs= imageAoi.projection().crs(),
                        crsTransform= crs_transform
                        )


def AddSLider(I_startYear, I_endYear):
    if(ui.root.widgets().length() > 2): ui.root.remove(ui.root.widgets().get(3))
    header = ui.Label('BAP composites time series', {'fontWeight': 'bold', 'fontSize': 40})
    toolPanel = ui.Panel([header], 'flow')
    nlayers = Map.layers().length()
    slider = ui.Slider({'min':I_startYear,'max': I_endYear,'value': I_startYear,'step': 1,
                            'style': {'width':'200px', 'height':'40px', 'color':'blue'}})
    
    def func_sgc(value):
        value_normalized = (value - (I_startYear-1))/(I_endYear-(I_startYear-1))
        int_value = value_normalized * (nlayers - 1) >> 0
        Map.layers().get(int_value).setOpacity(1)
        for i in range(int_value + 1, nlayers):
            Map.layers().get(i).setOpacity(0)
        
    slider.onSlide(func_sgc)
    Map.add(slider)


# Use this function so show index time series???
def plotTS(image, fit_variable, I_startYear, I_endYear):
    if(ui.root.widgets().length() > 3):
        ui.root.remove(ui.root.widgets().get(3))
    
    Map.style().set('cursor', 'crosshair')
    Map.setOptions("HYBRID")
    header = ui.Label('Please click on the map.', {'fontWeight': 'bold', 'fontSize': '16px', 'color': 'blue'})
    toolPanel = ui.Panel([header], 'flow', {'width': '400px'})

    def func_ccw(coords):
        click_point = ee.Geometry.Point(coords.lon, coords.lat)
        Map.addLayer(click_point, {'color': 'red'})
        pixel = ee.Image(image).reduceRegion(ee.Reducer.first(), click_point, 30)
        year = pixel.get("x")
        y = ee.Array(pixel.get("y"))
        y_fitted = ee.Array(pixel.get("y_fitted"))
        RMSE = ee.Array(pixel.get("RMSE"))
        vertex = ee.Array(pixel.get("vertex")).multiply(100)
        # despikedMask = ee.Array(pixel.get("despikedMask"))
        # yearTot = pixel.get("year")
        
        plot1 = chart.array_values(
              array=ee.Array.cat([y, y_fitted], 1),
              axis=0,
              x_labels=year,
              series_names=["y", 'y_fit'],
              kwargs={
                'lineWidth': 3,
                'title': 'Temporal Segmentation',
                'hAxis': {'title': 'year', 'minValue': I_startYear, 'maxValue': I_endYear},
                'vAxis': {'title': fit_variable},
                'pointSize': 2,
                'series': {
                        0: { 'color': 'pink', 'lineWidth': 0.1, 'pointSize': 4 },
                        1: { 'color': 'gold', 'lineWidth': 2, 'pointSize': 0 },
                    }
            }
        )

        toolPanel.widgets().set(1, plot1)

    Map.onClick(func_ccw)
    ui.root.add(toolPanel)

# // // Test the functions______________________________________________________________________________________________
# // var I_aoi = ee.Image('users/sfrancini/C2C/mask_template').geometry().bounds();
# // Map.centerObject(I_aoi, 7);
# // // I_aoi = null;
# // var bapTs = BAP(I_aoi,"12-15",60,70,0.3).aside(print, "BAP time series");
# // ShowCollection(bapTs, 1985, 2019, I_aoi, true, null);
# // // ShowCollection(C2CBAPtimeSeries, 2019, 2019, I_aoi, true, "doy", 0, 365);
# // // AddSLider(1985, 2019);

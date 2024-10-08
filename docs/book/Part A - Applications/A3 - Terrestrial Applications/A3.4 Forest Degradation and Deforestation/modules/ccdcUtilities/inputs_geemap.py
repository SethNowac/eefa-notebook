import ee 
import geemap

m = geemap.Map()


from . import dates_geemap as dateUtils
from . import ccdc_geemap as ccdcUtils

def getLandsat(options):
    start = (options is not None and options['start']) or '1980-01-01'
    end = (options is not None and options['end']) or '2021-01-01'
    startDoy = (options is not None and options['startDOY']) or 1
    endDoy = (options is not None and options['endDOY']) or 366
    region = (options is not None and options['region']) or None
    targetBands = (options is not None and options['targetBands']) or ['BLUE','GREEN','RED','NIR','SWIR1','SWIR2','TEMP','NBR','NDFI','NDVI','GV','NPV','Shade','Soil']
    useMask = (options is not None and options['useMask']) or True
    sensors = (options is not None and options['sensors']) or {'l4': True, 'l5': True, 'l7': True, 'l8': True}

    # Filter using new filtering functions
    collection4 = ee.ImageCollection('LANDSAT/LT04/C01/T1_SR') \
    .filterDate(start, end)
    collection5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR') \
    .filterDate(start, end)
    collection7 = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR') \
    .filterDate(start, end)
    collection8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
    .filterDate(start, end)
    if (useMask == 'No'):
        useMask = False

    if (useMask):
        collection8 = collection8.map(prepareL8)
        collection7 = collection7.map(prepareL7)
        collection5 = collection5.map(prepareL4L5)
        collection4 = collection4.map(prepareL4L5)



    col = collection4.merge(collection5) \
    .merge(collection7) \
    .merge(collection8)
    if (region):
        col = col.filterBounds(region)


    indices = doIndices(col).select(targetBands)

    if (not sensors.l5):
            indices = indices.filterMetadata('SATELLITE','not_equals','LANDSAT_5')

    if (not sensors.l4):
            indices = indices.filterMetadata('SATELLITE','not_equals','LANDSAT_4')

    if (not sensors.l7):
            indices = indices.filterMetadata('SATELLITE','not_equals','LANDSAT_7')

    if (not sensors.l8):
            indices = indices.filterMetadata('SATELLITE','not_equals','LANDSAT_8')

    indices = indices.filter(ee.Filter.dayOfYear(startDoy, endDoy))

    return ee.ImageCollection(indices)



def doIndices(collection):

    def func_ulk(image):
        NDVI =  calcNDVI(image)
        NBR = calcNBR(image)
        EVI = calcEVI(image)
        EVI2 = calcEVI2(image)
        TC = tcTrans(image)
        # NDFI function requires surface reflectance bands only
        BANDS = ['BLUE','GREEN','RED','NIR','SWIR1','SWIR2']
        NDFI = calcNDFI(image.select(BANDS))
        return image.addBands([NDVI, NBR, EVI, EVI2, TC, NDFI])

    return collection.map(func_ulk)













def getS2(roi):
    # Sentinel-2 Level 1C data.  Bands B7, B8, B8A and B10 from this
    # dataset are needed as input to CDI and the cloud mask function.
    s2 = ee.ImageCollection('COPERNICUS/S2')
    # Cloud probability dataset.  The probability band is used in
    # the cloud mask function.
    s2c = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
    # Sentinel-2 surface reflectance data for the composite.
    s2Sr = ee.ImageCollection('COPERNICUS/S2_SR')

    # Dates over which to create a median composite.
    start = ee.Date('2016-03-01')
    end = ee.Date('2021-09-01')

    # S2 L1C for Cloud Displacement Index (CDI) bands.
    s2 = s2.filterDate(start, end) \
    .select(['B7', 'B8', 'B8A', 'B10'])
    # S2Cloudless for the cloud probability band.
    s2c = s2c.filterDate(start, end)
    # S2 L2A for surface reflectance bands.
    s2Sr = s2Sr.filterDate(start, end) \
    .select(['B2', 'B3', 'B4', 'B5','B8','B11','B12'])
    if (roi):
            s2 = s2.filterBounds(roi)
            s2c = s2c.filterBounds(roi)
            s2Sr = s2Sr.filterBounds(roi)

    # Join two collections on their 'system:index' property.
    # The propertyName parameter is the name of the property
    # that references the joined image.
    def indexJoin(collectionA, collectionB, propertyName):
        joined = ee.ImageCollection(ee.Join.saveFirst(propertyName).apply(
        primary=collectionA,
        secondary=collectionB,
        condition=ee.Filter.equals(
        leftField='system:index',
        rightField='system:index')
        ))
        # Merge the bands of the joined image.

        def func_bkc(image):
            return image.addBands(ee.Image(image.get(propertyName)))

        return joined.map(func_bkc)




    # Aggressively mask clouds and shadows.
    def maskImage(image):
        # Compute the cloud displacement index from the L1C bands.
        cdi = ee.Algorithms.Sentinel2.CDI(image)
        s2c = image.select('probability')
        cirrus = image.select('B10').multiply(0.0001)

        # Assume low-to-mid atmospheric clouds to be pixels where probability
        # is greater than 65%, and CDI is less than -0.5. For higher atmosphere
        # cirrus clouds, assume the cirrus band is greater than 0.01.
        # The final cloud mask is one or both of these conditions.
        isCloud = s2c.gt(65).And(cdi.lt(-0.5)).Or(cirrus.gt(0.01))

        # Reproject is required to perform spatial operations at 20m scale.
        # 20m scale is for speed, and assumes clouds don't require 10m precision.
        isCloud = isCloud.focal_min(3).focal_max(16)
        isCloud = isCloud.reproject(crs=cdi.projection(), scale=20)

        # Project shadows from clouds we found in the last step. This assumes we're working in
        # a UTM projection.
        shadowAzimuth = ee.Number(90) \
        .subtract(ee.Number(image.get('MEAN_SOLAR_AZIMUTH_ANGLE')))

        # With the following reproject, the shadows are projected 5km.
        isCloud = isCloud.directionalDistanceTransform(shadowAzimuth, 50)
        isCloud = isCloud.reproject(crs=cdi.projection(), scale=100)

        isCloud = isCloud.select('distance').mask()
        return image.select('B2', 'B3', 'B4','B8','B11','B12') \
        .rename(['BLUE','GREEN','RED','NIR','SWIR1','SWIR2']) \
        .divide(10000).updateMask(isCloud.Not()) \
        .set('system:time_start',ee.Image(image.get('l1c')).get('system:time_start'))


    # Join the cloud probability dataset to surface reflectance.
    withCloudProbability = indexJoin(s2Sr, s2c, 'cloud_probability')
    # Join the L1C data to get the bands needed for CDI.
    withS2L1C = indexJoin(withCloudProbability, s2, 'l1c')

    # Map the cloud masking function over the joined collection.
    return doIndices(ee.ImageCollection(withS2L1C.map(maskImage)))



def calcNDVI(image):
    ndvi = ee.Image(image).normalizedDifference(['NIR', 'RED']).rename('NDVI')
    return ndvi



def calcNBR(image):
    nbr = ee.Image(image).normalizedDifference(['NIR', 'SWIR2']).rename('NBR')
    return nbr



def calcNDFI(image):
    # Do spectral unmixing #
    gv = [.0500, .0900, .0400, .6100, .3000, .1000]
    shade = [0, 0, 0, 0, 0, 0]
    npv = [.1400, .1700, .2200, .3000, .5500, .3000]
    soil = [.2000, .3000, .3400, .5800, .6000, .5800]
    cloud = [.9000, .9600, .8000, .7800, .7200, .6500]
    cf = .1 
    cfThreshold = ee.Image.constant(cf)
    unmixImage = ee.Image(image).unmix([gv, shade, npv, soil, cloud], True,True) \
    .rename(['band_0', 'band_1', 'band_2','band_3','band_4'])
    newImage = ee.Image(image).addBands(unmixImage)
    mask = newImage.select('band_4').lt(cfThreshold)
    ndfi = ee.Image(unmixImage).expression(
    '((GV / (1 - SHADE)) - (NPV + SOIL)) / ((GV / (1 - SHADE)) + NPV + SOIL)', {
        'GV':ee.Image(unmixImage).select('band_0'),
        'SHADE':ee.Image(unmixImage).select('band_1'),
        'NPV':ee.Image(unmixImage).select('band_2'),
        'SOIL':ee.Image(unmixImage).select('band_3')
    })

    return ee.Image(newImage) \
    .addBands(ee.Image(ndfi).rename(['NDFI'])) \
    .select(['band_0','band_1','band_2','band_3','NDFI']) \
    .rename(['GV','Shade','NPV','Soil','NDFI']) \
    .updateMask(mask)




def calcEVI(image):

    evi = ee.Image(image).expression(
    'float(2.5*(((B4) - (B3)) / ((B4) + (6 * (B3)) - (7.5 * (B1)) + 1)))',
    {
        'B4': ee.Image(image).select(['NIR']),
        'B3': ee.Image(image).select(['RED']),
        'B1': ee.Image(image).select(['BLUE'])
    }).rename('EVI')

    return evi



def calcEVI2(image):
    evi2 = ee.Image(image).expression(
    'float(2.5*(((B4) - (B3)) / ((B4) + (2.4 * (B3)) + 1)))',
    {
        'B4': image.select('NIR'),
        'B3': image.select('RED')
    })
    return evi2.rename('EVI2')



def tcTrans(image):

    # Calculate tasseled cap transformation
    brightness = image.expression(
    '(L1 * B1) + (L2 * B2) + (L3 * B3) + (L4 * B4) + (L5 * B5) + (L6 * B6)',
    {
        'L1': image.select('BLUE'),
        'B1': 0.2043,
        'L2': image.select('GREEN'),
        'B2': 0.4158,
        'L3': image.select('RED'),
        'B3': 0.5524,
        'L4': image.select('NIR'),
        'B4': 0.5741,
        'L5': image.select('SWIR1'),
        'B5': 0.3124,
        'L6': image.select('SWIR2'),
        'B6': 0.2303
    })
    greenness = image.expression(
    '(L1 * B1) + (L2 * B2) + (L3 * B3) + (L4 * B4) + (L5 * B5) + (L6 * B6)',
    {
        'L1': image.select('BLUE'),
        'B1': -0.1603,
        'L2': image.select('GREEN'),
        'B2': -0.2819,
        'L3': image.select('RED'),
        'B3': -0.4934,
        'L4': image.select('NIR'),
        'B4': 0.7940,
        'L5': image.select('SWIR1'),
        'B5': -0.0002,
        'L6': image.select('SWIR2'),
        'B6': -0.1446
    })
    wetness = image.expression(
    '(L1 * B1) + (L2 * B2) + (L3 * B3) + (L4 * B4) + (L5 * B5) + (L6 * B6)',
    {
        'L1': image.select('BLUE'),
        'B1': 0.0315,
        'L2': image.select('GREEN'),
        'B2': 0.2021,
        'L3': image.select('RED'),
        'B3': 0.3102,
        'L4': image.select('NIR'),
        'B4': 0.1594,
        'L5': image.select('SWIR1'),
        'B5': -0.6806,
        'L6': image.select('SWIR2'),
        'B6': -0.6109
    })

    bright =  ee.Image(brightness).rename('BRIGHTNESS')
    green = ee.Image(greenness).rename('GREENNESS')
    wet = ee.Image(wetness).rename('WETNESS')

    tasseledCap = ee.Image([bright, green, wet])
    return tasseledCap




def makeLatGrid(minY, maxY, minX, maxX, size):

    ySeq = ee.List.sequence(minY, maxY, size)
    numFeats = ySeq.length().subtract(2)

    def func_qfw(num):
        num = ee.Number(num)
        num2 = num.add(1)
        y1 = ee.Number(ySeq.get(num))
        y2 = ee.Number(ySeq.get(num2))
        feat = ee.Feature(ee.Geometry.Polygon([[maxX, y2], [minX, y2], [minX, y1], [maxX, y1]]))
        return feat

    feats = ee.List.sequence(0, numFeats).map(func_qfw)







    return ee.FeatureCollection(feats)





def makeLonGrid(minY, maxY, minX, maxX, size):

    ySeq = ee.List.sequence(minX, maxX, size)
    numFeats = ySeq.length().subtract(2)

    def func_vve(num):
        num = ee.Number(num)
        num2 = num.add(1)
        x1 = ee.Number(ySeq.get(num))
        x2 = ee.Number(ySeq.get(num2))
        feat = ee.Feature(ee.Geometry.Polygon([[x2, maxY], [x1, maxY], [x1, minY], [x2, minY]]))
        return feat

    feats = ee.List.sequence(0, numFeats).map(func_vve)







    return ee.FeatureCollection(feats)



def makeLonLatGrid(minY, maxY, minX, maxX, size):

    xSeq = ee.List.sequence(minX, maxX, size)
    ySeq = ee.List.sequence(minY, maxY, size)

    numFeatsY = ySeq.length().subtract(2)
    numFeatsX = xSeq.length().subtract(2)


    def func_edh(y):
        y = ee.Number(y)
        y2 = y.add(1)
        y1_val = ee.Number(ySeq.get(y))
        y2_val = ee.Number(ySeq.get(y2))

        def func_aeq(x):
                x = ee.Number(x)
                x2 = x.add(1)
                x1_val = ee.Number(xSeq.get(x))
                x2_val = ee.Number(xSeq.get(x2))
                return ee.Feature(ee.Geometry.Polygon([[x2_val, y2_val], [x1_val, y2_val], [x1_val, y1_val], [x2_val, y1_val]]))

        feat = ee.List.sequence(0, numFeatsX).map(func_aeq)






        return feat


    feats = ee.List.sequence(0, numFeatsY).map(func_edh)

    return ee.FeatureCollection(feats.flatten())




def makeAutoGrid(geo, size):
    coordList = ee.List(geo.coordinates().get(0))


    def func_cal (c):
        return ee.List(c).flatten().get(0)

    lonList = coordList.map(func_cal)




    def func_gph (c):
        return ee.List(c).flatten().get(1)

    latList = coordList.map(func_gph)




    minY = latList.reduce(ee.Reducer.min())
    maxY = latList.reduce(ee.Reducer.max())


    minX = lonList.reduce(ee.Reducer.min())
    maxX = lonList.reduce(ee.Reducer.max())

    xSeq = ee.List.sequence(minX, maxX, size)
    ySeq = ee.List.sequence(minY, maxY, size)

    numFeatsY = ySeq.length().subtract(2)
    numFeatsX = xSeq.length().subtract(2)


    def func_lok(y):
        y = ee.Number(y)
        y2 = y.add(1)
        y1_val = ee.Number(ySeq.get(y))
        y2_val = ee.Number(ySeq.get(y2))

        def func_pnc(x):
                x = ee.Number(x)
                x2 = x.add(1)
                x1_val = ee.Number(xSeq.get(x))
                x2_val = ee.Number(xSeq.get(x2))
                return ee.Feature(ee.Geometry.Polygon([[x2_val, y2_val], [x1_val, y2_val], [x1_val, y1_val], [x2_val, y1_val]]))

        feat = ee.List.sequence(0, numFeatsX).map(func_pnc)






        return feat


    feats = ee.List.sequence(0, numFeatsY).map(func_lok)


    return ee.FeatureCollection(feats.flatten())


def getAncillary():

    srtm = ee.Image('USGS/SRTMGL1_003').rename('ELEVATION')
    alos =  ee.Image("JAXA/ALOS/AW3D30/V2_2").select(0).rename('ELEVATION')
    demImage = ee.ImageCollection([alos,srtm]).mosaic()

    slope = ee.Terrain.slope(demImage).rename('DEM_SLOPE')
    aspect = ee.Terrain.aspect(demImage).rename('ASPECT')
    bio = ee.Image('WORLDCLIM/V1/BIO').select(['bio01','bio12']).rename(['TEMPERATURE','RAINFALL'])
    water = ee.Image('JRC/GSW1_1/GlobalSurfaceWater') \
    .select('occurrence') \
    .rename('WATER_OCCURRENCE')
    pop = ee.ImageCollection("WorldPop/GP/100m/pop") \
    .filterMetadata('year','equals',2000) \
    .mosaic() \
    .rename('POPULATION')

    hansen = ee.Image("UMD/hansen/global_forest_change_2018_v1_6") \
    .select('treecover2000') \
    .rename('TREE_COVER')

    nightLights = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG") \
    .filter(ee.Filter.date('2019-01-01', '2019-12-31')) \
    .select('avg_rad') \
    .mosaic() \
    .rename('NIGHT_LIGHTS')

    # I can't get this to work without memory errors
    # settlement = ee.Image("JRC/GHSL/P2016/SMOD_POP_GLOBE_V1/2000")
    # distance = ee.Image(1).cumulativeCost(
    #   settlement.gt(1),
    #   100000)
    # .divide(100)
    # .int32()
    # .rename('DISTANCE_SETTLEMENT')

    return ee.Image.cat([demImage, slope, aspect, bio, pop, water, hansen, nightLights]).unmask()







def prepare(orbit):
    # Load the Sentinel-1 ImageCollection.
    return ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .filter(ee.Filter.eq('orbitProperties_pass', orbit))



def getS1(focalSize, kernelType):
    focalSize = focalSize or 3
    kernelType = kernelType or 'circle'
    data = ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .select(['V.','angle'])

    def func_uqt(img):
        geom = img.geometry()
        angle = img.select('angle')
        edge = img.select('VV').lt(-30.0); 

        fmean = img.select('V.').add(30).focal_mean(focalSize, kernelType)
        ratio = fmean.select('VH').divide(fmean.select('VV')).rename('ratio').multiply(30)
        return img.select().addBands(fmean).addBands(ratio).addBands(angle) \
    .map(func_uqt)











    return data





def prepareL4L5(image):
    bandList = ['B1', 'B2','B3','B4','B5','B7','B6']
    nameList = ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'TEMP']
    scaling = [10000, 10000, 10000, 10000, 10000, 10000, 1000]
    scaled = ee.Image(image).select(bandList).rename(nameList).divide(ee.Image.constant(scaling))

    validQA = [66, 130, 68, 132]
    mask1 = ee.Image(image).select(['pixel_qa']).remap(validQA, ee.List.repeat(1, validQA.length), 0)
    # Gat valid data mask, for pixels without band saturation
    mask2 = image.select('radsat_qa').eq(0)
    mask3 = image.select(bandList).reduce(ee.Reducer.min()).gt(0)
    # Mask hazy pixels. Aggressively filters too many images in arid regions (e.g Egypt)
    # unless we force include 'nodata' values by unmasking
    mask4 = image.select("sr_atmos_opacity").unmask().lt(300)
    return ee.Image(image).addBands(scaled).updateMask(mask1.And(mask2).And(mask3).And(mask4))



def prepareL7(image):
    bandList = ['B1', 'B2','B3','B4','B5','B7','B6']
    nameList = ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'TEMP']
    scaling = [10000, 10000, 10000, 10000, 10000, 10000, 1000]
    scaled = ee.Image(image).select(bandList).rename(nameList).divide(ee.Image.constant(scaling))

    validQA = [66, 130, 68, 132]
    mask1 = ee.Image(image).select(['pixel_qa']).remap(validQA, ee.List.repeat(1, validQA.length), 0)
    # Gat valid data mask, for pixels without band saturation
    mask2 = image.select('radsat_qa').eq(0)
    mask3 = image.select(bandList).reduce(ee.Reducer.min()).gt(0)
    # Mask hazy pixels. Aggressively filters too many images in arid regions (e.g Egypt)
    # unless we force include 'nodata' values by unmasking
    mask4 = image.select("sr_atmos_opacity").unmask().lt(300)
    # Slightly erode bands to get rid of artifacts due to scan lines
    mask5 = ee.Image(image).mask().reduce(ee.Reducer.min()).focal_min(2.5)
    return ee.Image(image).addBands(scaled).updateMask(mask1.And(mask2).And(mask3).And(mask4).And(mask5))



def prepareL8(image):
    bandList = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B10']
    nameList = ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'TEMP']
    scaling = [10000, 10000, 10000, 10000, 10000, 10000, 1000]

    validTOA = [66, 68, 72, 80, 96, 100, 130, 132, 136, 144, 160, 164]
    validQA = [322, 386, 324, 388, 836, 900]

    scaled = ee.Image(image).select(bandList).rename(nameList).divide(ee.Image.constant(scaling))
    mask1 = ee.Image(image).select(['pixel_qa']).remap(validQA, ee.List.repeat(1, validQA.length), 0)
    mask2 = image.select('radsat_qa').eq(0)
    mask3 = image.select(bandList).reduce(ee.Reducer.min()).gt(0)
    mask4 = ee.Image(image).select(['sr_aerosol']).remap(validTOA, ee.List.repeat(1, validTOA.length), 0)
    return ee.Image(image).addBands(scaled).updateMask(mask1.And(mask2).And(mask3).And(mask4))


def generateCollection(geom, startDate, endDate):
    filteredL8 = (ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
    .filter("WRS_ROW < 122") \
    .filterBounds(geom) \
    .map(prepareL8))

    filteredL7 = (ee.ImageCollection('LANDSAT/LE07/C01/T1_SR') \
    .filter("WRS_ROW < 122") \
    .filterBounds(geom) \
    .map(prepareL7))

    # Originally not included in Noel's run
    filteredL4 = (ee.ImageCollection('LANDSAT/LT04/C01/T1_SR') \
    .filter("WRS_ROW < 122") \
    .filterBounds(geom) \
    .map(prepareL4L5))
    filteredL5 = (ee.ImageCollection('LANDSAT/LT05/C01/T1_SR') \
    .filter("WRS_ROW < 122") \
    .filterBounds(geom) \
    .map(prepareL4L5))

    mergedCollections = ee.ImageCollection(filteredL8).merge(filteredL7).merge(filteredL5).merge(filteredL4)
    return mergedCollections.filterDate(startDate, endDate)



def makeCcdImage(metadataFilter, segs, numberOfSegments,bandNames,inputFeatures, version):
    metadataFilter = metadataFilter or 'z'
    numberOfSegments = numberOfSegments or 6
    bandNames = bandNames or ["BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP"]
    segs = segs or ['S1','S2','S3','S4','S5','S6']
    bandNames = bandNames or ["BLUE","GREEN","RED","NIR","SWIR1","SWIR2","TEMP"]
    inputFeatures = inputFeatures or ["INTP", "SLP","PHASE","AMPLITUDE","RMSE"]
    version = version or 'v2'

    ccdcCollection = ee.ImageCollection("projects/CCDC/" + version)

    # Get CCDC coefficients
    ccdcCollectionFiltered = ccdcCollection \
    .filterMetadata('system:index', 'starts_with',metadataFilter)

    # CCDC mosaic image
    ccdc = ccdcCollectionFiltered.mosaic()

    # Turn array image into image
    return ee.Image(ccdcUtils.buildCcdImage(ccdc, numberOfSegments, bandNames))



m
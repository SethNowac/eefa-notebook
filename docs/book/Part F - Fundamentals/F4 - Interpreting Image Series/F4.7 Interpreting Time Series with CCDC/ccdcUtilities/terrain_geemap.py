import ee 
import math
import geemap

m = geemap.Map()

#*** Start of imports. If edited, may not auto-convert in the playground. ***#
geometry = ee.Geometry.Point([84.07618795831739, 29.54037010686166])

utils = require('projects/GLANCE:ccdcUtilities/inputs')

PARAMS,
TERRAIN,
FUNCS,
HELPER
RESULTS = {}

PARAMS = {
    'pi': 3.14159265359,
    'dem': ee.Image("USGS/SRTMGL1_003"),
    'products': ee.Terrain.products(ee.Image("USGS/SRTMGL1_003")),
    'landsat': utils.getLandsat(),
    'landsat': ee.ImageCollection("LANDSAT/LC08/C01/T2_SR"),
    'wrs2': ee.FeatureCollection('projects/google/wrs2_descending'),
}


def func_csf():


    def func_kbm(num):
            return num.multiply(180).divide(PARAMS.pi)

    this.degrees = func_kbm




    def func_xqj(num):
            return num.multiply(pi).divide(180)

    this.radians = func_xqj




    def func_bki():
            PARAMS.landsatImage = ee.Image(
            PARAMS.landsat \
            .filterBounds(PARAMS.geo) \
            .first()
            )

            # Get the hour and minute from image, date from parameter
            sensingTime= ee.Date(PARAMS.landsatImage.get('SENSING_TIME'))

            PARAMS.newDate = PARAMS.date.update(
            PARAMS.date.get('year'),
            PARAMS.date.get('month'),
            PARAMS.date.get('day'),
            sensingTime.get('hour'),
            sensingTime.get('minute'),
            sensingTime.get('second')
            )

            PARAMS.sensingTime = sensingTime

    this.filterLandsat = func_bki






















    def func_ivp(img):
            point = PARAMS.geo
            sze = FUNCS.degrees(
            img.select('sunZen')
            ).sample(
            ee.Feature(point).buffer(300).geometry(),
            30,
            None,
            None,
            1
            ).first()
            saz = FUNCS.degrees(
            img.select('sunAz')
            ).sample(
            ee.Feature(point).buffer(300).geometry(),
            30,
            None,
            None,
            1
            ).first()
            return img.set('SZE',sze.get('sunZen'),'SAZ',saz.get('sunAz'))

    this.getSZE = func_ivp

























FUNCS = func_csf













































































































def toImage(band, args):
if ((typeof band):
if (band.indexOf('.'):
            band = image.expression(format(band, args), {'i': image})
             else
            band = image.select(band)
        }
        return ee.Image(band)


    def format(s, args):
if (not args):
        allArgs = merge(constants, args)
        result = s.replace(/{([^{}]*)}/g,

        def func_izi (a, b):
            replacement = allArgs[b]
if (replacement == None):
                    print('Undeclared argument: ' + b, 's: ' + s, args.getInfo())
                    return None

            return allArgs[b]

        func_izi







        )
if (result.indexOf(''):
            return format(result, args)
            return result
        }

        def merge(o1, o2):
            def addAll(target, toAdd):
                for (key in toAdd) target[key] = toAdd[key]


            result = {}
            addAll(result, o1)
            addAll(result, o2)
            return result


        secondsInHour = 3600
        set('longDeg',
        ee.Image.pixelLonLat().select('longitude'))
        set('latRad',
        ee.Image.pixelLonLat().select('latitude') \
        .multiply(math.pi).divide(180))
        set('hourGMT',
        ee.Number(date.getRelative('second', 'day')).divide(secondsInHour))
        set('jdp', 
        date.getFraction('year'))
        set('jdpr', 
        'i.jdp * 2 * {pi}')
        set('meanSolarTime',
        'i.hourGMT + i.longDeg / 15')
        set('localSolarDiff',
        '(0.000075 + 0.001868 * cos(i.jdpr) - 0.032077 * sin(i.jdpr)' + \
        '- 0.014615 * cos(2 * i.jdpr) - 0.040849 * sin(2 * i.jdpr))' + \
        '* 12 * 60 / {pi}')
        set('TrueSolarTime',
        'i.meanSolarTime + i.localSolarDiff / 60 - 12')
        set('angleHour',
        'i.TrueSolarTime * 15 * {pi} / 180')
        set('delta',
        '0.006918 - 0.399912 * cos(i.jdpr) + 0.070257 * sin(i.jdpr) - 0.006758 * cos(2 * i.jdpr)' + \
        '+ 0.000907 * sin(2 * i.jdpr) - 0.002697 * cos(3 * i.jdpr) + 0.001480 * sin(3 * i.jdpr)')
        set('cosSunZen',
        'sin(i.latRad) * sin(i.delta) ' + \
        '+ cos(i.latRad) * cos(i.delta) * cos(i.angleHour)')
        set('sunZen',
        'acos(i.cosSunZen)')
        set('sinSunAzSW',
        toImage('cos(i.delta) * sin(i.angleHour) / sin(i.sunZen)') \
        .clamp(-1, 1))
        set('cosSunAzSW',
        '(-cos(i.latRad) * sin(i.delta)' + \
        '+ sin(i.latRad) * cos(i.delta) * cos(i.angleHour)) / sin(i.sunZen)')
        set('sunAzSW',
        'asin(i.sinSunAzSW)')
        setIf('sunAzSW',
        'i.cosSunAzSW <= 0',
        '{pi} - i.sunAzSW',
        'sunAzSW')
        setIf('sunAzSW',
        'i.cosSunAzSW > 0 and i.sinSunAzSW <= 0',
        '2 * {pi} + i.sunAzSW',
        'sunAzSW')
        set('sunAz',
        'i.sunAzSW + {pi}')
        setIf('sunAz',
        'i.sunAz > 2 * {pi}',
        'i.sunAz - 2 * {pi}',
        'sunAz')
        return image



    def func_xde(img):

        SZ_rad = img.select('sunZen')
        SA_rad = img.select('sunAz')

        # Creat terrain layers
        slp = ee.Terrain.slope(PARAMS.dem) \
        .clip(img.geometry().buffer(10000))

        slp_rad = ee.Terrain.slope(PARAMS.dem) \
        .multiply(3.14159265359) \
        .divide(180) \
        .clip(img.geometry().buffer(10000))

        asp_rad = ee.Terrain.aspect(PARAMS.dem) \
        .multiply(3.14159265359) \
        .divide(180) \
        .clip(img.geometry().buffer(10000))

        # Calculate the Illumination Condition (IC)
        # slope part of the illumination condition
        cosZ = SZ_rad.cos()
        cosS = slp_rad.cos()
        slope_illumination = cosS.expression("cosZ * cosS",
        {'cosZ': cosZ,
            'cosS': cosS.select('slope')})
        # aspect part of the illumination condition
        sinZ = SZ_rad.sin()
        sinS = slp_rad.sin()
        cosAziDiff = (SA_rad.subtract(asp_rad)).cos()
        aspect_illumination = sinZ.expression("sinZ * sinS * cosAziDiff",
        {'sinZ': sinZ,
                'sinS': sinS,
            'cosAziDiff': cosAziDiff})
        # full illumination condition (IC)
        ic = slope_illumination.add(aspect_illumination)

        # Add IC to original image
        img_plus_ic = ee.Image(
        img.addBands(ic.rename('IC')) \
        .addBands(cosZ.rename('cosZ')) \
        .addBands(cosS.rename('cosS')) \
        .addBands(slp.rename('slope')))
        return img_plus_ic

    this.illuminationCondition = func_xde














































    def func_ctw(img):
        props = img.toDictionary()
        st = img.get('system:time_start')

        img_plus_ic = img
        mask1 = img_plus_ic.select('NIR').gt(-0.1)
        mask2 = img_plus_ic.select('slope').gte(5) \
        .And(img_plus_ic.select('NIR').gt(-0.1))
        img_plus_ic_mask2 = ee.Image(img_plus_ic.updateMask(mask2))

        # Specify Bands to topographically correct
        bandList = ['BLUE','GREEN','RED','NIR','SWIR1','SWIR2']
        compositeBands = img.bandNames()
        nonCorrectBands = img.select(compositeBands.removeAll(bandList))

        geom = ee.Geometry(img.get('system:footprint')).bounds().buffer(10000)

        def apply_SCSccorr(band):
                method = 'SCSc'
                out = img_plus_ic_mask2.select('IC', band).reduceRegion(
                    reducer=ee.Reducer.linearFit(), 
                    geometry=ee.Geometry(img.geometry().buffer(-5000)), 
                    scale=300,
                    maxPixels=1000000000,
                    tileScale=8
                    )

if (out == None or out == undefined ):
                        return img_plus_ic_mask2.select(band)


                else{
                        out_a = ee.Number(out.get('scale'))
                        out_b = ee.Number(out.get('offset'))
                        out_c = out_b.divide(out_a)
                        # Apply the SCSc correction
                        SCSc_output = img_plus_ic_mask2.expression(
                        "((image * (cosB * cosZ + cvalue)) / (ic + cvalue))", {
                                    'image': img_plus_ic_mask2.select(band),
                                    'ic': img_plus_ic_mask2.select('IC'),
                                    'cosB': img_plus_ic_mask2.select('cosS'),
                                    'cosZ': img_plus_ic_mask2.select('cosZ'),
                                    'cvalue': out_c
                                })

                        return ee.Algorithms.If(out.get('offset'), SCSc_output, img_plus_ic_mask2.select(band))
                    }



        img_SCSccorr = ee.Image(bandList.map(apply_SCSccorr)) \
        .addBands(img_plus_ic.select('IC'))

        bandList_IC = ee.List([bandList, 'IC']).flatten()

        img_SCSccorr = img_SCSccorr.unmask(img_plus_ic.select(bandList_IC)).select(bandList)

        return img_SCSccorr.addBands(nonCorrectBands) \
        .setMulti(props) \
        .set('system:time_start',st)

    this.illuminationCorrection = func_ctw































































# main(geo, img.date(), None, img,threshold)

def func_ojj(geo, date, maskMode, landsatImage, maskType, icThreshold, slopeThreshold):

    PARAMS.geo = geo
    PARAMS.date = ee.Date(date)
    PARAMS.icThreshold = icThreshold or .7
    PARAMS.slopeThreshold = slopeThreshold or 10
    maskType = maskType or 'any'

if (maskMode):
            FUNCS.filterLandsat()
         else {
            PARAMS.landsatImage = landsatImage
            PARAMS.newDate = PARAMS.date
            PARAMS.sensingTime = ee.Date(PARAMS.landsatImage.get('SENSING_TIME'))

        }

    solarGeo = HELPER.solarPosition(
    PARAMS.landsatImage,
    PARAMS.newDate.millis()
    )
    PARAMS.solarGeo = solarGeo

    illuminationCondition = ee.Image(
    HELPER.illuminationCondition(
    PARAMS.solarGeo
    )
    )

    PARAMS.illuminationCondition = illuminationCondition


    terrainCorrected = ee.Image(
    HELPER.illuminationCorrection(
    illuminationCondition
    )
    )
    # In case i need it later....
    PARAMS.terrainCorrected = terrainCorrected

    illumMask = illuminationCondition.select('IC') \
    .lte(PARAMS.icThreshold) \
    .And(
    PARAMS.products.select('slope') \
    .gt(
    PARAMS.slopeThreshold
    )
    ).unmask()

    # Now get cast shadow
    imgWithSZE = ee.Image(
    FUNCS.getSZE(
    illuminationCondition
    )
    )

    hillShadow = ee.Image(
    HELPER.doHillShadow(
    imgWithSZE
    )).gt(0).And(
    PARAMS.products.select('slope').gt(PARAMS.slopeThreshold)) \
    .unmask()

if (maskType == 'any'):
            return illumMask.Or(hillShadow).rename('TerrainShadowMask')
if (maskType == 'type'):
            return hillShadow.multiply(2).add(illumMask).rename('TerrainShadowMask')
if (maskType == 'hillshadow'):
            return hillShadow.rename('ShadowMask')
if (maskType == 'IC'):
            return illuminationCondition.select('IC')
          else {
            return illumMask.rename('TerrainMask')
        }

main = func_ojj













































































def func_oph(feat):

    def func_efu(num):
            return ee.Image(
            main(
            feat.centroid().geometry(),
            ee.String('2012-').cat(ee.String(num)).cat('-01'),
            True
            )
            )

    imList = ee.List([2,5,8,11]).map(func_efu)









    return ee.ImageCollection(imList) \
    .reduce(
    ee.Reducer.sum()
    ).gt(0).selfMask()

mappingFunc = func_oph


























def func_gzu(img, date, mask, threshold):
if (date):
            img = img.set('system:time_start',ee.Date(date).millis())

    copyOfImage = img
    geo = img.geometry()

    img = HELPER.solarPosition(
    img,
    ee.Date(date).millis()
    )

    img = HELPER.illuminationCondition(img)
    img = HELPER.illuminationCorrection(img)

    img = ee.Image(img).clip(geo)

if (mask && mask == 'any'):
            tMask = makeMask(geo)
            img = img.updateMask(tMask)
if (mask && mask == 'image'):
            tMask = main(geo, img.date(), None, img,'image',threshold)
            spectralBands = img.select(['BLUE','GREEN','RED','NIR','SWIR1','SWIR2','TEMP'])
            allMasks = ee.Image.cat([tMask, tMask, tMask, tMask, tMask, tMask, tMask])
            spectralBands = spectralBands.where(tMask.Not(), copyOfImage)
            img = img.addBands(spectralBands, None, True)


    return img.copyProperties(copyOfImage)

terrainCorrection = func_gzu






























HELPER = HELPER()
FUNCS = FUNCS()


makeMask = makeMask
terrainCorrection = terrainCorrection
main = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = maimain = main
m
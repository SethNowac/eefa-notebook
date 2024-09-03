import ee 
import math
import geemap

Map = geemap.Map()

# Fusion Near Real-time (Lite).
# Near real-time monitoring of forest disturbance by fusion of
# multi-sensor data.  @author Xiaojing Tang (xjtang@bu.edu).

# Utility functions.

# Common utilities.

def func_jfz(col, period, band):

    def func_xyl(col, band):

            def func_boj(img):
                        return addDependents(img \
                        .select(band)) \
                        .select(['INTP', 'SLP', 'COS', 'SIN', 'COS2', 'SIN2', 'COS3', 'SIN3', band]) \
                        .updateMask(img.select(band).mask())

            return ee.ImageCollection(col.map(func_boj




            ))

        prepareData = func_xyl













        t.multiply(omega * 2).sin(),
        t.multiply(omega * 3).cos(),
        t.multiply(omega * 3).sin()]).float() \
        .rename(['INTP', 'SLP', 'COS', 'SIN', 'COS2', 'SIN2', 'COS3', 'SIN3'])
        return img.addBands(dependents)
        
    col2 = prepareData(col, band)
    ccd = col2 \
    .reduce(ee.Reducer.robustLinearRegression(8, 1), 4) \
    .rename([band + '_coefs', band + '_rmse'])
    return ccd.select(band + '_coefs') \
    .arrayTranspose() \
    .addBands(ccd.select(band + '_rmse'))

runCCD = func_jfz












































def func_dmg(region, params, sensor, endMembers):
if (sensor == 'Sentinel-2'):
            return(getSen2TS(region, params, endMembers))
if (sensor == 'Sentinel-1'):
            return(getSen1TS(region, params))
         else {
            return(getLandsatTS(region, params, endMembers))
        }

getData = func_dmg










def func_gyb(region, date, sensor):
if (sensor == 'Sentinel-2'):
            return(getSen2Img(region, date))
if (sensor == 'Sentinel-1'):
            return(getSen1Img(region, date))
         else {
            return(getLandsatImage(region, date))
        }

getImage = func_gyb










def func_euf(t, coef, dateFormat):
    PI2 = 2.0 * math.pi
    OMEGAS = [PI2 / 365.25, PI2,
    PI2 / (1000 * 60 * 60 * 24 * 365.25)]
    omega = OMEGAS[dateFormat]
    return coef.get([0]) \
    .add(coef.get([1]).multiply(t)) \
    .add(coef.get([2]).multiply(t.multiply(omega).cos())) \
    .add(coef.get([3]).multiply(t.multiply(omega).sin())) \
    .add(coef.get([4]).multiply(t.multiply(omega * 2).cos())) \
    .add(coef.get([5]).multiply(t.multiply(omega * 2).sin())) \
    .add(coef.get([6]).multiply(t.multiply(omega * 3).cos())) \
    .add(coef.get([7]).multiply(t.multiply(omega * 3).sin()))

harmonicFit = func_euf















def func_von(ccd, band):
    band = band + '_'

    def func_cbt(ccd, band, coef):
            zeros = ee.Array(0).repeat(0, 1)
            coefImg = ccd \
            .select(band + coef) \
            .arrayCat(zeros, 0) \
            .float() \
            .arraySlice(0, 0, 1)
            return ee.Image(coefImg \
            .arrayFlatten([[ee.String('S1_').cat(band).cat(coef)]]))

    genCoefImg = func_cbt








    

    def func_sxx(ccd, band):
            harms = ['INTP', 'SLP', 'COS', 'SIN', 'COS2', 'SIN2', 'COS3', 'SIN3']
            zeros = ee.Image(ee.Array([ee.List.repeat(0, harms.length)])) \
            .arrayRepeat(0, 1)
            coefImg = ccd \
            .select(band + 'coefs') \
            .arrayCat(zeros, 0) \
            .float() \
            .arraySlice(0, 0, 1)
            return ee.Image(coefImg \
            .arrayFlatten([[ee.String('S1_').cat(band).cat('coef')], harms]))

    genHarmImg = func_sxx










    
    rmse = genCoefImg(ccd, band, 'rmse')
    coef = genHarmImg(ccd, band)
    return ee.Image.cat(rmse, coef)

getCCDImage = func_von \
.rename(['synt', band]) \
.set({
'sensor': sensor,
'system:time_start': img.get('system:time_start'),
'dateString': dateString
})



def func_qjp(img):
    return genSyntImg(ccd, img, band, sensor)

return ee.ImageCollection(data.map(func_qjp

))



def func_efm(data, band):

    def func_ewz(img):
            return img \
            .select('synt') \
            .where(img.select('synt').gt(10000), 10000) \
            .subtract(img.select(band)) \
            .rename('residual') \
            .set({
                    'sensor': img.get('sensor'),
                    'system:time_start': img.get('system:time_start'),
                    'dateString': img.get('dateString')
                    })

    return ee.ImageCollection(data.map(func_ewz










    ))

getResiduals = func_efm

























'system:time_start': img.get('system:time_start')
)
return zStack.updateMask(strike.gt(0).Or(mask))
}))
}


def func_kal(zScores, nrtParam):
    zeros = ee.Image(0) \
    .addBands(ee.Image(0)) \
    .rename(['change', 'date'])
    shift = math.pow(2, nrtParam.m - 1) - 1

    def func_vfu(img, result):
            change = ee.Image(result).select('change')
            date = ee.Image(result).select('date')
            shiftImg = img \
            .select('z') \
            .mask() \
            .eq(0) \
            .multiply(shift + 1) \
            .add(shift)
            change = change \
            .bitwiseAnd(shiftImg) \
            .multiply(shiftImg.eq(shift).add(1)) \
            .add(img.select('strike').unmask().gt(0))
            date = date \
            .add(change.bitCount().gte(nrtParam.n) \
            .multiply(date.eq(0)) \
            .multiply(ee.Number(convertDateFormat(
            ee.Date(img.get('system:time_start')), 1))))
            return(change.addBands(date))

    monitor = func_vfu


















    
    return ee.Image(zScores.iterate(monitor, zeros)) \
    .select('date') \
    .rename('Alerts') \
    .selfMask()

monitorChange = func_kal



















































def func_ucv(region, params):
    collection7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
    .filterBounds(region) \
    .filterDate(params.get('start'), params.get('end'))
    collection8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .filterBounds(region) \
    .filterDate(params.get('start'), params.get('end'))
    col7NoClouds = collection7.map(maskL7)
    col8NoClouds = collection8.map(maskL8)
    colNoClouds = col7NoClouds.merge(col8NoClouds)
    return ee.ImageCollection(unmixing(colNoClouds))

getLandsatTS = func_ucv













def func_crc(img):
    return img \
    .addBands(
    img.multiply(0.0000275).add(-0.2).multiply(10000),
    img.bandNames(),
    True
    )

c2ToSR = func_crc









def func_olm(img):
    sr = c2ToSR(img \
    .select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'])) \
    .rename(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
    validQA = [5440, 5504]
    mask1 = img \
    .select('QA_PIXEL') \
    .remap(validQA, ee.List.repeat(1, validQA.length), 0)
    mask2 = sr.reduce(ee.Reducer.min()).gt(0)
    mask3 = sr.reduce(ee.Reducer.max()).lt(10000)
    return sr.updateMask(mask1.And(mask2).And(mask3))

maskL7 = func_olm













def func_dqt(img):
    sr = c2ToSR(img \
    .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'])) \
    .rename(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
    validQA = [21824, 21888]
    mask1 = img \
    .select(['QA_PIXEL']) \
    .remap(validQA, ee.List.repeat(1, validQA.length), 0)
    mask2 = sr.reduce(ee.Reducer.min()).gt(0)
    mask3 = sr.reduce(ee.Reducer.max()).lt(10000)
    return sr.updateMask(mask1.And(mask2).And(mask3))

maskL8 = func_dqt













def func_ssm(col):
    gv = [500, 900, 400, 6100, 3000, 1000]
    npv = [1400, 1700, 2200, 3000, 5500, 3000]
    soil = [2000, 3000, 3400, 5800, 6000, 5800]
    shade = [0, 0, 0, 0, 0, 0]
    cloud = [9000, 9600, 8000, 7800, 7200, 6500]
    cfThreshold = 0.05

    def func_bgz(img):
            unmixed = img \
            .select(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2']) \
            .unmix([gv, shade, npv, soil, cloud], True, True) \
            .rename(['GV', 'Shade', 'NPV', 'Soil', 'Cloud'])
            maskCloud = unmixed.select('Cloud').lt(cfThreshold)
            maskShade = unmixed.select('Shade').lt(1)
            NDFI = unmixed.expression(
            '10000 * ((GV / (1 - SHADE)) - (NPV + SOIL)) / ((GV / (1 - SHADE)) + (NPV + SOIL))',
            {
                        'GV': unmixed.select('GV'),
                        'SHADE': unmixed.select('Shade'),
                        'NPV': unmixed.select('NPV'),
                        'SOIL': unmixed.select('Soil')
                    }).rename('NDFI')
            maskNDFI = unmixed.expression(
            '(GV / (1 - SHADE)) + (NPV + SOIL)',
            {
                        'GV': unmixed.select('GV'),
                        'SHADE': unmixed.select('Shade'),
                        'NPV': unmixed.select('NPV'),
                        'SOIL': unmixed.select('Soil')
                    }).gt(0)
            return img \
            .addBands(unmixed.select(['GV','Shade','NPV','Soil']) \
            .multiply(10000)) \
            .addBands(NDFI) \
            .updateMask(maskCloud) \
            .updateMask(maskNDFI) \
            .updateMask(maskShade)

    return col.map(func_bgz)































unmixing = func_ssm






































































def func_qaz(region, date):
    imDate = ee.Date(date)
    befDate = imDate.advance(-1, 'day')
    aftDate = imDate.advance(1, 'day')
    S2 = ee.ImageCollection('COPERNICUS/S2') \
    .filterBounds(region) \
    .filterDate(befDate, aftDate)
    S2Cloud = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY') \
    .filterBounds(region) \
    .filterDate(befDate, aftDate)
    S2Joined = ee.ImageCollection(ee.Join.saveFirst('cloud_prob') \
    .apply(
        primary = S2,
        secondary = S2Cloud,
        condition = ee.Filter.equals(
            leftField = 'system =index',
            rightField = 'system =index'
            )
        ))
    return ee.Algorithms.If(
    S2Joined.size().gt(0),
    maskSen2Img(S2Joined.first()),
    None
    )

getSen2Img = func_qaz


























def func_bju(img):
    qa = img.select('QA60')
    cloud = ee.Image(img.get('cloud_prob')) \
    .select('probability')
    cloudProbMask = cloud.lt(65)
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0) \
    .And(qa.bitwiseAnd(cirrusBitMask).eq(0)) \
    .And(cloudProbMask)
    return img \
    .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']) \
    .rename(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2']) \
    .updateMask(mask)

maskSen2Img = func_bju















# Sentinel-1 utilities.

def func_ixa(region, params):

    def func_con(img):
            st = img.get('system:time_start')
            geom = img.geometry()
            angle = img.select('angle')
            edge = img.select('VV').lt(-30.0)
            fmean = img.select('V.').add(30)
            fmean = fmean.focal_mean(3, 'circle')
            ratio = fmean \
            .select('VH') \
            .divide(fmean.select('VV')) \
            .rename('ratio') \
            .multiply(30)
            return img \
            .select() \
            .addBands(fmean) \
            .addBands(ratio) \
            .addBands(angle) \
            .set('timeStamp', st)

    spatialSmoothing = func_con

















    


    def func_ewe(col):
            model = 'volume'
            elevation = ee.Image('USGS/SRTMGL1_003')
            buffer = 0
            ninetyRad = ee.Image.constant(90) \
            .multiply(math.pi/180)

            def _volume_model(theta_iRad, alpha_rRad):
                        nominator = (ninetyRad.subtract(theta_iRad) \
                        .add(alpha_rRad)) \
                        .tan()
                        denominator = (ninetyRad.subtract(theta_iRad)) \
                        .tan()
                        return nominator.divide(denominator)


            def _surface_model(theta_iRad, alpha_rRad, alpha_azRad):
                        nominator = (ninetyRad.subtract(theta_iRad)).cos()
                        denominator = alpha_azRad \
                        .cos() \
                        .multiply((ninetyRad.subtract(theta_iRad) \
                        .add(alpha_rRad)).cos())
                        return nominator.divide(denominator)


            def _erode(img, distance):
                        d = img \
                        .Not() \
                        .unmask(1) \
                        .fastDistanceTransform(30) \
                        .sqrt() \
                        .multiply(ee.Image.pixelArea() \
                        .sqrt())
                        return img.updateMask(d.gt(distance))


            def _masking(alpha_rRad, theta_iRad, proj, buffer):
                        layover = alpha_rRad.lt(theta_iRad).rename('layover')
                        shadow = alpha_rRad \
                        .gt(ee.Image.constant(-1).multiply(ninetyRad.subtract(theta_iRad))) \
                        .rename('shadow')
                        mask = layover.And(shadow)
if (buffer > 0):
                        return mask.rename('no_data_mask')


            def _correct(image):
                        geom = image.geometry()
                        proj = image.select(1).projection()
                        heading = ee.Terrain.aspect(image.select('angle')) \
                        .reduceRegion(ee.Reducer.mean(), geom, 1000) \
                        .get('aspect')
                        sigma0Pow = ee.Image.constant(10) \
                        .pow(image.divide(10.0))
                        theta_iRad = image.select('angle') \
                        .multiply(math.pi/180) \
                        .clip(geom)
                        phi_iRad = ee.Image.constant(heading) \
                        .multiply(math.pi/180)
                        alpha_sRad = ee.Terrain.slope(elevation) \
                        .select('slope') \
                        .multiply(math.pi/180) \
                        .setDefaultProjection(proj) \
                        .clip(geom)
                        phi_sRad = ee.Terrain.aspect(elevation) \
                        .select('aspect') \
                        .multiply(math.pi/180) \
                        .setDefaultProjection(proj) \
                        .clip(geom)
                        phi_rRad = phi_iRad.subtract(phi_sRad)
                        alpha_rRad = (alpha_sRad.tan().multiply(phi_rRad.cos())) \
                        .atan()
                        alpha_azRad = (alpha_sRad.tan().multiply(phi_rRad.sin())) \
                        .atan()
                        gamma0 = sigma0Pow.divide(theta_iRad.cos())
                        corrModel = _volume_model(theta_iRad, alpha_rRad)
                        gamma0_flat = gamma0.divide(corrModel)
                        gamma0_flatDB = ee.Image.constant(10) \
                        .multiply(gamma0_flat.log10()) \
                        .select(['VV', 'VH'])
                        mask = _masking(alpha_rRad, theta_iRad, proj, buffer)
                        return gamma0_flatDB \
                        .addBands(mask) \
                        .copyProperties(image)

            return col.map(_correct)

    slopeCorrection = func_ewe





















































































    

    S1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filterBounds(region) \
    .filterDate(params.get('start'), params.get('end')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
    .filter(ee.Filter.eq('instrumentMode', 'IW')) \
    .select(['V.','angle']) \
    .map(spatialSmoothing) \
    .select(['VH','VV','ratio','angle'])
    passCount = ee.Dictionary(S1.aggregate_histogram('orbitProperties_pass'))
    passValues = passCount.values().sort().reverse()
    higherCount = passValues.get(0)
    maxOrbitalPass = passCount \
    .keys() \
    .get(passCount.values().indexOf(higherCount))
    S1Filtered = S1.filter(ee.Filter.eq(
    'orbitProperties_pass',
    maxOrbitalPass
    ))
    S1Corrected = slopeCorrection(S1Filtered)

    def func_wpi(img):
            st = img.get('timeStamp')
            return img \
            .addBands(img.select('VH').divide(img.select('VV')) \
            .rename('ratio') \
            .multiply(10)) \
            .set('system:time_start', st)

    return ee.ImageCollection(S1Corrected.map(func_wpi






    ))

getSen1TS = func_ixa





























































































































































































































































'geometry': geometry,
'crs': proj
).getNumber(band)
fit = harmonicFit(time, ee.Array(coef), dateFormat)
residual = ee.Algorithms.If(
value,
fit.subtract(value),
value
)
return ee.Feature(geometry).set({
'monitor': value,
'fitTime': time,
'fit': fit,
'x': residual,
'rmse': rmse,
'dateString': img \
.date() \
.format('YYYY-MM-dd'),
'monitorFitTime': time,
})
)


return produceTrainSeries(train, geometry, band) \
.merge(produceMonitorSeries(monitor, geometry, band))



def func_ond(ccdTS, colNames):
    listLen = colNames.length
    return ccdTS \
    .reduceColumns(ee.Reducer.toList(listLen, listLen), colNames) \
    .get('list')

transformToTable = func_ond







def func_bxq(table, band, lat, lon):
    def formatTable(table):
            cols = [
            {'id': 'A', 'label': 'Date', 'type': 'date'},
            {'id': 'B', 'label': 'Training', 'type': 'number'},
            {'id': 'C', 'label': 'Monitoring', 'type': 'number'},
            {'id': 'D', 'label': 'Fit', 'type': 'number'}
            ]

            def func_ttn(list):

                    def func_bxe(item, index):
                                return {'v': 'index == 0 ? new Date(item)': item}
                            )
                    return {'c': list.map(func_bxe

                                

                        values = table.map(func_ttn







                        chart = ui.Chart(formatted, 'LineChart', {
                                    'title': 'Pixel located at ' + lat.toFixed(3) + ', ' + lon.toFixed(3),
                                    'pointSize': 0,
                                    'series': {
                                                '0': '{ pointSize': 1.8, 'lineWidth': 0},
                                                '1': '{ pointSize': 1.8, 'lineWidth': 0}
                                            },
                                    'vAxis': {
                                                'title': band,
                                            },
                                    'height': '90%',
                                    'stretch': 'both'
                                })
                        return chart

        createCCDChart = func_bxq







































        rmse = ee.Number(timeSeries.first().get('rmse')) \
        .max(minRMSE)

        def func_bzj(img):
                            x = img.get('x')
                            residual = img.get('residual')
                            train = img.get('trainFitTime')
                            return ee.Algorithms.If(
                            train,
                            img.set({'Z_train': ee.Number(
                                    ee.Algorithms.If(
                                    ee.Number(residual).divide(rmse).gt(maxZ),
                                    maxZ,
                                    ee.Number(residual).divide(rmse)
                                    )
                                    )}),
                            ee.Algorithms.If(
                            x,
                            img.set({'Z_monitor': ee.Number(
                                    ee.Algorithms.If(
                                    ee.Number(x).divide(rmse).gt(maxZ),
                                    maxZ,
                                    ee.Number(x).divide(rmse)
                                    )
                                    )}),
                            img
                            )
                            )

        return timeSeries.map(func_bzj)

























    }


    def func_qol(timeSeries, threshold):

                    def func_ife(img):
                            x = img.get('Z_monitor')
                            return ee.Algorithms.If(
                            x,
                            ee.Algorithms.If(
                            ee.Number(x).gt(threshold),
                            img.set({'Strike': x}),
                            img.set({'Ball': x})
                            ),
                            img)

                    return timeSeries.map(func_ife)











    checkPixelZScore = func_qol























    flags.slice(1).add(1).frequency(1).gte(nrtParam.n),
    flags.add(img.get('fitTime')),
    flags.slice(1).add(1)
    ),
    flags.slice(1).add(0)
    )
    )
    , ee.List.repeat(0, nrtParam.m))).get(-1))

flag = nrtDetect(zScoreSeries, nrtParam)
return ee.Algorithms.If(
flag.gt(0),

def func_swd(img):
                date = img.get('fitTime')
                z = img.get('Strike')
                return ee.Algorithms.If(
                flag.eq(date),
                img.set({'StrikeOut': z, 'Strike': None}),
                img
                )

zScoreSeries.map(func_swd







),
zScoreSeries
)



def func_gkf(table, lat, lon):
                def formatTable(table):
                        cols = [
                        {'id': 'A', 'label': 'Date', 'type': 'date'},
                        {'id': 'B', 'label': 'Training', 'type': 'number'},
                        {'id': 'C', 'label': 'Ball', 'type': 'number'},
                        {'id': 'D', 'label': 'Strike', 'type': 'number'},
                        {'id': 'E', 'label': 'StrikeOut', 'type': 'number'}
                        ]

                        def func_xsz(list):

                                def func_gbv(item, index):
                                            return {'v': 'index == 0 ? new Date(item)': item}
                                        )
                                return {'c': list.map(func_gbv

                                            

                                    values = table.map(func_xsz







                                    chart = ui.Chart(formatted, 'ScatterChart', {
                                                'title': 'Pixel located at ' + lat.toFixed(3) + ', ' + lon.toFixed(3),
                                                'pointSize': 1.8,
                                                'vAxis': {
                                                            'title': 'Z Score',
                                                            'viewWindowMode': 'explicit',
                                                        },
                                                'height': '90%',
                                                'stretch': 'both'
                                            })
                                    return chart

        createNRTChart = func_gkf





































        'getSen2Img': getSen2Img,
        'getSen1TS': getSen1TS,
        'getSen1Img': getSen1Img,
        'runCCD': runCCD,
        'transformToTable': transformToTable,
        'createCCDChart': createCCDChart,
        'getTimeSeries': getTimeSeries,
        'addPixelZScore': addPixelZScore,
        'checkPixelZScore': checkPixelZScore,
        'monitorPixelChange': monitorPixelChange,
        'createNRTChart': createNRTChart,
        'getCCDImage': getCCDImage,
        'addSynthetic': addSynthetic,
        'getResiduals': getResiduals,
        'getChangeScores': getChangeScores,
        'monitorChange': monitorChange,
        'spatialFilter': spatialFilter
    }

    # Comments (nclinton).  This is too much for me to reformat.
    # Please adhere to Google JavaScript stype guidelines as
    # described in:
    # https:#docs.google.com/document/d/19KQBEDA-hYQEg4EizWOXPRNLmeOyc77YqEkqtHH6770/edit?usp=sharing&resourcekey=0-SRpYwdFqCLHgB5rA145AAw

# LGTM (nclinton# LGTM (nclinton# LGTM (nclinton# LGTM (nclinton)
Map
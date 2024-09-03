import ee 
import math
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      A3.5 Deforestation Viewed from Multiple Sensors
#  Checkpoint:   A35e
#  Author:       Xiaojing Tang
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

testArea = ee.Geometry.Polygon(
[
[
[-66.73156878460787, -8.662236005089952],
[-66.73156878460787, -8.916025640576244],
[-66.44867083538912, -8.916025640576244],
[-66.44867083538912, -8.662236005089952]
]
])

Map.centerObject(testArea)

# Start and end of the training and monitoring period.
trainPeriod = ee.Dictionary({
'start': '2017-01-01',
'end': '2020-01-01'
})
monitorPeriod = ee.Dictionary({
'start': '2020-01-01',
'end': '2021-01-01'
})

# Near-real-time monitoring parameters.
nrtParam = {
    'z': 2,
    'm': 5,
    'n': 4
}

# Sensor specific parameters.
lstParam = {
    'band': 'NDFI',
    'minRMSE': 0.05,
    'strikeOnly': False
}
s2Param = {
    'band': 'NDFI',
    'minRMSE': 0.05,
    'strikeOnly': False
}
s1Param = {
    'band': 'VV',
    'minRMSE': 0.01,
    'strikeOnly': True
}

# ------------------------------------------------------------------------
# CHECKPOINT
# ------------------------------------------------------------------------


def func_mns(col):

    # Define endmembers and cloud fraction threshold.
    gv = [500, 900, 400, 6100, 3000, 1000]
    npv = [1400, 1700, 2200, 3000, 5500, 3000]
    soil = [2000, 3000, 3400, 5800, 6000, 5800]
    shade = [0, 0, 0, 0, 0, 0]
    cloud = [9000, 9600, 8000, 7800, 7200, 6500]
    cfThreshold = 0.05


    def func_uwq(img):
            # Select the spectral bands and perform unmixing
            unmixed = img.select(['Blue', 'Green', 'Red',
            'NIR',
            'SWIR1', 'SWIR2'
            ]) \
            .unmix([gv, shade, npv, soil, cloud], True,
            True) \
            .rename(['GV', 'Shade', 'NPV', 'Soil',
            'Cloud'
            ])

            # Calculate Normalized Difference Fraction Index.+ \
            NDFI = unmixed.expression(
            '10000 * ((GV / (1 - SHADE)) - (NPV + SOIL)) / ' + \
            '((GV / (1 - SHADE)) + (NPV + SOIL))', {
                        'GV': unmixed.select('GV'),
                        'SHADE': unmixed.select('Shade'),
                        'NPV': unmixed.select('NPV'),
                        'SOIL': unmixed.select('Soil')
                    }).rename('NDFI')

            # Mask cloudy pixel.
            maskCloud = unmixed.select('Cloud').lt(
            cfThreshold)
            # Mask all shade pixel.
            maskShade = unmixed.select('Shade').lt(1)
            # Mask pixel where NDFI cannot be calculated.
            maskNDFI = unmixed.expression(
            '(GV / (1 - SHADE)) + (NPV + SOIL)', {
                        'GV': unmixed.select('GV'),
                        'SHADE': unmixed.select('Shade'),
                        'NPV': unmixed.select('NPV'),
                        'SOIL': unmixed.select('Soil')
                    }).gt(0)

            # Scale fractions to 0-10000 and apply masks.
            return img \
            .addBands(unmixed.select(['GV', 'Shade',
            'NPV', 'Soil'
            ]) \
            .multiply(10000)) \
            .addBands(NDFI) \
            .updateMask(maskCloud) \
            .updateMask(maskNDFI) \
            .updateMask(maskShade)

    return col.map(func_uwq)















































unmixing = func_mns











































































































def func_ihc(col, band):
    # Function to add dependent variables to an image.

    def func_wuh(img):
            # Transform time variable to fractional year.
            t = ee.Number(toFracYear(
            ee.Date(img.get('system:time_start')), 1))
            omega = 2.0 * math.pi
            # Construct dependent variables image.
            dependents = ee.Image.constant([
            1, t,
            t.multiply(omega).cos(),
            t.multiply(omega).sin(),
            t.multiply(omega * 2).cos(),
            t.multiply(omega * 2).sin(),
            t.multiply(omega * 3).cos(),
            t.multiply(omega * 3).sin()
            ]) \
            .float() \
            .rename(['INTP', 'SLP', 'COS', 'SIN',
            'COS2', 'SIN2', 'COS3', 'SIN3'
            ])
            return img.addBands(dependents)

    addDependents = func_wuh



















    

    # Function to add dependent variable images to all images.

    def func_fuh(col, band):

            def func_zii(img):
                        return addDependents(img.select(band)) \
                        .select(['INTP', 'SLP', 'COS',
                        'SIN',
                        'COS2', 'SIN2', 'COS3',
                        'SIN3',
                        band
                        ]) \
                        .updateMask(img.select(band) \
                        .mask())

            return ee.ImageCollection(col.map(func_zii









            ))























fitHarmonicModel = func_ihc





























































































s2Model = models \
.filterMetadata('sensor', 'equals', 'Sentinel-2').first()
s1Model = models \
.filterMetadata('sensor', 'equals', 'Sentinel-1').first()


def func_jmp(model, band):
        band = band + '_'

        # Function to extract a non-harmonic coefficients.

        def func_ekt(model, band, coef):
                zeros = ee.Array(0).repeat(0, 1)
                coefImg = model.select(band + coef) \
                .arrayCat(zeros, 0).float() \
                .arraySlice(0, 0, 1)
                return ee.Image(coefImg \
                .arrayFlatten([
                [ee.String('S1_') \
                .cat(band).cat(coef)
                ]
                ]))

        genCoefImg = func_ekt










        

        # Function to extract harmonic coefficients.

        def func_etl(model, band):
                harms = ['INTP', 'SLP', 'COS', 'SIN',
                'COS2', 'SIN2', 'COS3', 'SIN3'
                ]
                zeros = ee.Image(ee.Array([
                ee.List.repeat(0, harms.length)
                ])) \
                .arrayRepeat(0, 1)
                coefImg = model.select(band + 'coefs') \
                .arrayCat(zeros, 0).float() \
                .arraySlice(0, 0, 1)
                return ee.Image(coefImg \
                .arrayFlatten([
                [ee.String(band).cat('coef')], harms
                ]))

        genHarmImg = func_etl














        

        # Extract harmonic coefficients and rmse.
        rmse = genCoefImg(model, band, 'rmse')
        coef = genHarmImg(model, band)
        return ee.Image.cat(rmse, coef)

dearrayModel = func_jmp \
.addBands(img, [band]).rename(['predicted', band]) \
.set({
'sensor': sensor,
'system:time_start': img.get('system:time_start'),
'dateString': dateString
})



def func_sye(data, modelImg, band, sensor):

        def func_vep(img):
                return createPredImg(modelImg, img, band,
                sensor)

        return ee.ImageCollection(data.map(func_vep


        ))

addPredicted = func_sye









s1ModelImg = dearrayModel(s1Model, s1Param.band)

# Add predicted image to each real image.
lstPredicted = addPredicted(lstMonitoring, lstModelImg,
lstParam.band, 'Landsat')
s2Predicted = addPredicted(s2Monitoring, s2ModelImg,
s2Param.band, 'Sentinel-2')
s1Predicted = addPredicted(s1Monitoring, s1ModelImg,
s1Param.band, 'Sentinel-1')

print('lstPredicted', lstPredicted.getInfo())

# ------------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------# -----------------------------------------------------------------------# -----------------------------------------------------------------------# -----------------------------------------------------------------------# -----------------------------------------------------------------------# -----------------------------------------------------------------------# -----------------------------------------------------------------------# ------------------------------------------------------------------------
Map
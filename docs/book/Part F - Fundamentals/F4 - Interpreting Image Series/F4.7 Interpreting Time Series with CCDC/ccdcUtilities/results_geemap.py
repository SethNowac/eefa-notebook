import ee 
import geemap

m = geemap.Map()

#*** Start of imports. If edited, may not auto-convert in the playground. ***#
geometry = \
ee.Geometry.MultiPolygon(
[[[[-117.14969968636422, 31.56495919215045],
[-117.14969968636422, 27.786113408408234],
[-102.51591062386422, 27.786113408408234],
[-102.51591062386422, 31.56495919215045]]],
[[[-100.73971565424944, 23.387552980701475],
[-100.73971565424944, 22.715302336002278],
[-99.55593879878069, 22.715302336002278],
[-99.55593879878069, 23.387552980701475]]],
[[[-84.33357618887231, 11.493999379203002],
[-84.33357618887231, 10.99833392197591],
[-83.86116407949731, 10.99833392197591],
[-83.86116407949731, 11.493999379203002]]],
[[[-84.641588696685, 10.324312563679818],
[-84.641588696685, 10.118885408298746],
[-84.32023859902876, 10.118885408298746],
[-84.32023859902876, 10.324312563679818]]],
[[[-78.37840592797431, 9.302506837414125],
[-78.37840592797431, 9.218472491382073],
[-78.25206315453681, 9.218472491382073],
[-78.25206315453681, 9.302506837414125]]]], None, False)


# Return collection with all the images that match a string in an asset folder

def func_gbs(folderPath, assetType, stringMatch):
    list = ee.data.getList({'id': folderPath})
    ims = []

    for i in range(0, list.length, ):
            id = list[i]['id']
if (id.indexOf(stringMatch):
if (assetType == 'featureCollection'):
                            im = ee.FeatureCollection(id)
if (assetType == 'Image'):
                            im = ee.Image(id)

                    ims.push(im)


    return ims

assetsToCollection = func_gbs



















ccdcUtils = require('projects/GLANCE:ccdcUtilities/ccdc')
classUtils = require('projects/GLANCE:ccdcUtilities/classification')

# Date to display in addition to 1999
date = '2018-01-01'


def func_nnx():
    # Gather all the results finished as of now and create list.
    folder = 'projects/GLANCE/RESULTS/CLASSIFICATION/V1'

    list = ee.data.getList({'id': folder})
    ims = []

    for i in range(0, list.length, ):
            id = list[i]['id']
if (id.indexOf('Classified'):
                    im = ee.Image(id)
                    ims.push(im)



    # Turn that list into an image collection
    col = ee.ImageCollection(ims)

    # Get the mode for each segment.
    return col.reduce(ee.Reducer.mode())

getMode = func_nnx





















# Visualization parameters
palette = ['#5475a8','#ffffff','#b50000','#d2cdc0','#38814e','#dcca8f','#ca9146','#85c77e']
viz = {'min': 1, 'max': 8, 'palette': palette}


# Legend

# Make legends

def func_mcq(color, name):
    # Make a row of a legend

    colorBox = ui.Label(
        style={
                backgroundColor=color,
                padding='8px',
                margin='0 0 4px 0'
            }
        )

    description = ui.Label(
        value=name,
        style={margin='0 0 4px 6px'}
        )

    return ui.Panel(
        widgets=[colorBox, description],
        layout=ui.Panel.Layout.Flow('horizontal')
        )

makeRow = func_mcq





















legend = ui.Panel({'style': '{shown': True, 'width': '150px'}})
legend.style().set({'position': 'bottom-right'})

legend.add(makeRow(palette[0], 'Water'))
legend.add(makeRow(palette[1], 'Ice/Snow'))
legend.add(makeRow(palette[2], 'Built'))
legend.add(makeRow(palette[3], 'Bare'))
legend.add(makeRow(palette[4], 'Forest'))
legend.add(makeRow(palette[5], 'Shrub'))
legend.add(makeRow(palette[6], 'Herbaceous'))
legend.add(makeRow(palette[7], 'Woodland'))



viz = viz
legend = legend
getMode = getMode
assetsToCollection = assetsToCollection
m
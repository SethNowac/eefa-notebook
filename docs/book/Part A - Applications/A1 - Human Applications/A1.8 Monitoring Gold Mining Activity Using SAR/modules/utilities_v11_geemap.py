import ee 
import geemap

m = geemap.Map()

#*********************************************************************************
# Utilities for change detection
#*********************************************************************************
# References:
#
# Updated April 4, 2020 : Modified from 'users/mortcanty/changedetection:utilities'
#
#*********************************************************************************

def func_pjr(chi2,df):
    # Chi square cumulative distribution function '''
    return ee.Image(chi2.divide(2)).gammainc(ee.Number(df).divide(2))

chi2cdf = func_pjr




# def func_xqv(data):
#     # for exporting as CSV to Drive
#     return ee.Feature(None, {'data': data})
# makefeature = func_xqv



# def func_eze(vis):
#     lon = ee.Image.pixelLonLat().select('longitude')
#     gradient = lon.multiply((vis.max-vis.min)/100.0).add(vis.min)
#     legendImage = gradient.visualize(vis)
#     # Add legend to a panel
#     thumb = ui.Thumbnail(
#         image=legendImage,
#         params={bbox ='0,0,100,8', dimensions ='256x15'},
#         style={padding='1px', position='top-center'}
#         )
#     panel = ui.Panel(
#         widgets=[
#         ui.Label(str(vis['min'])),
#         ui.Label({'style':{'stretch':'horizontal'}}),
#         ui.Label(vis['max'])
#         ],
#         layout=ui.Panel.Layout.flow('horizontal'),
#         style={'stretch'='horizontal'}
#         )
#     return ui.Panel().add(panel).add(thumb)

# makeLegend = func_eze





















# def func_mco(image,geometry,k,title,max):
#     # generate time axis chart
#     bmap = image.select(ee.List.sequence(3,k+2))
#     zeroes = bmap.multiply(0)
#     ones = zeroes.add(1)
#     twos = zeroes.add(2)
#     threes = zeroes.add(3)
#     bmapall = zeroes.where(bmap.gt(0),ones)
#     bmappos = zeroes.where(bmap.eq(ones),ones)
#     bmapneg = zeroes.where(bmap.eq(twos),ones)
#     bmapind = zeroes.where(bmap.eq(threes),ones)

#     cutall = ee.Dictionary(bmapall.reduceRegion(ee.Reducer.mean(),geometry,None,None,None,False,1e11))

#     def func_qyw(x) return ee.String(x).slice(1,9)};:
#     keys = cutall.keys().map( function(x) {return ee.String(x).slice(1,9)}
#     keys = cutall.keys().map( func_qyw)
#     chartall = ui.Chart.array.values(cutall.toArray(),0,keys).setChartType('ColumnChart')

#     cutpos = ee.Dictionary(bmappos.reduceRegion(ee.Reducer.mean(),geometry,None,None,None,False,1e11))
#     chartpos = ui.Chart.array.values(cutpos.toArray(),0,keys).setChartType('ColumnChart')

#     cutneg = ee.Dictionary(bmapneg.reduceRegion(ee.Reducer.mean(),geometry,None,None,None,False,1e11))
#     chartneg = ui.Chart.array.values(cutneg.toArray(),0,keys).setChartType('ColumnChart')

#     cutind = ee.Dictionary(bmapind.reduceRegion(ee.Reducer.mean(),geometry,None,None,None,False,1e11))
#     chartind = ui.Chart.array.values(cutind.toArray(),0,keys).setChartType('ColumnChart')

#     chartall.setOptions(
#         title=title,
#         hAxis={
#                 title='End of Change Interval'
#             },
#         vAxis={
#                 title='Fraction of Changes',
#                 viewWindow={
#                             min=0.0,
#                             max=max
#                         },
#                 textStyle ={
#                             fontSize=16
#                         }
#             }})
#         chartpos.setOptions(
#             title=title,
#             hAxis={
#                     title='End of Change Interval'
#                 },
#             vAxis={
#                     title='Fraction of Positive Definite Changes',
#                     viewWindow={
#                                 min=0.0,
#                                 max=max
#                             },
#                     textStyle ={
#                                 fontSize=16
#                             }
#                 }})
#             chartneg.setOptions(
#                 title=title,
#                 hAxis={
#                         title='End of Change Interval'
#                     },
#                 vAxis={
#                         title='Fraction of Negative Definite Changes',
#                         viewWindow={
#                                     min=0.0,
#                                     max=max
#                                 },
#                         textStyle ={
#                                     fontSize=16
#                                 }
#                     }})
#                 chartind.setOptions(
#                     title=title,
#                     hAxis={
#                             title='End of Change Interval'
#                         },
#                     vAxis={
#                             title='Fraction of Indefinite Changes',
#                             viewWindow={
#                                         min=0.0,
#                                         max=max
#                                     },
#                             textStyle ={
#                                         fontSize=16
#                                     }
#                         }})
#                     return([chartall,chartpos,chartneg,chartind])

# rcut = func_mco
























































































# n = ee.Number(current)
# prev = ee.Dictionary(prev)
# bmap = ee.Image(prev.get('bmap'))
# bnames = bmap.bandNames()
# label = bnames.get(n)
# background = ee.Image(prev.get('background'))
# framelist = ee.List(prev.get('framelist'))
# bmapband = bmap.select(n)
# zeroes = bmapband.multiply(0)
# ones = zeroes.add(1)
# twos = zeroes.add(2)
# threes = zeroes.add(3)
# idxr = bmapband.eq(ones)
# idxg = bmapband.eq(twos)
# idxy = bmapband.eq(threes)
# imager = background.where(idxr,ones)
# imageg = background.where(idxr,zeroes)
# imageb = background.where(idxr,zeroes)
# imageg = imageg.where(idxg,ones)
# imager = imager.where(idxg,zeroes)
# imageb = imageb.where(idxg,zeroes)
# imageb = imageb.where(idxy,zeroes)
# imager = imager.where(idxy,ones)
# imageg = imageg.where(idxy,ones)
# frame = imager.addBands(imageg).addBands(imageb) \
# .multiply(256) \
# .uint8() \
# .rename(['r','g','b']) \
# .set({label =label})
# return ee.Dictionary({'bmap' =bmap,'background' =background,'framelist' =framelist.add(frame)})

# m
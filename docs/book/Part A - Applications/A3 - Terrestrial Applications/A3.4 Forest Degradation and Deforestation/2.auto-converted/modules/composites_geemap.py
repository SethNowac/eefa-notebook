import ee
import geemap

Map = geemap.Map()

def qaMask(img):
  good = img.select("QC_Day").eq(0)
  return img.select("LST_Day_1km").updateMask(good).multiply(0.02)

collection = ee.ImageCollection("MODIS/006/MOD11A1") \
  .map(qaMask) \
  .select("LST_Day_1km")
start = ee.Date('2016-01-01')
end = ee.Date('2020-01-01')

count = end.difference(start, 'month')
def func_jak(n):
  begin = start.advance(n, 'month')
  return collection.filterDate(begin, begin.advance(1, 'month')).mean()

result = ee.List.sequence(0, count).map(func_jak)

vis = {
  'min': 260.0,
  'max': 330.0,
  'palette': [
    '040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6',
    '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef',
    '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f',
    'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d',
    'ff0000', 'de0101', 'c21301', 'a71001', '911003'
  ],
}
Map.addLayer(ee.ImageCollection.fromImages(result), vis)
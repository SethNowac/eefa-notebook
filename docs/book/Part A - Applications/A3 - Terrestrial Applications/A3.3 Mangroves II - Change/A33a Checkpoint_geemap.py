import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      A3.3 Mangroves II - Change Mapping
#  Checkpoint:   A33a
#  Authors:      Celio de Sousa, David Lagomasino, and Lola Fatoyinbo
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# STEP 1 - ADD THE MAPS
areaOfstudy = ee.FeatureCollection(
'projects/gee-book/assets/A3-3/Border5km')
mangrove2000 = ee.Image(
'projects/gee-book/assets/A3-3/MangroveGuinea2000_v2')
mangrove2020 = ee.Image(
'projects/gee-book/assets/A3-3/MangroveGuinea2020_v2')

Map.setCenter(-13.6007, 9.6295, 10)
# Sets the map center to Conakry, Guinea
Map.addLayer(areaOfstudy, {}, 'Area of Study')
Map.addLayer(mangrove2000, {
    'palette': '#16a596'
}, 'Mangrove Extent 2000')
Map.addLayer(mangrove2020, {
    'palette': '#9ad3bc'
}, 'Mangrove Extent 2020')

# STEP 2 -  MAP TO MAP CHANGE

mang2020 = mangrove2020.unmask(0)
mang2000 = mangrove2000.unmask(0)
change = mang2020.subtract(mang2000) \
.clip(areaOfstudy)

paletteCHANGE = [
'red', 
'white', 
'green', 
]

Map.addLayer(change, {
    'min': -1,
    'max': 1,
    'palette': paletteCHANGE
}, 'Changes 2000-2020')

# Calculate the area of each pixel
gain = change.eq(1)
loss = change.eq(-1)

gainArea = gain.multiply(ee.Image.pixelArea().divide(1000000))
lossArea = loss.multiply(ee.Image.pixelArea().divide(1000000))

# Sum all the areas
statsgain = gainArea.reduceRegion(
reducer = ee.Reducer.sum(),
scale = 30,
maxPixels = 1e14
)

statsloss = lossArea.reduceRegion(
reducer = ee.Reducer.sum(),
scale = 30,
maxPixels = 1e14
)

print(statsgain.get('classification'.getInfo())
'km² of new mangroves in 2020')
print(statsloss.get('classification'.getInfo())
'of mangrove was lost in 2020')

Map.addLayer(gain.selfMask(), {
    'palette': 'green'
}, 'Gains')
Map.addLayer(loss.selfMask(), {
    'palette': 'red'
}, 'Loss')

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------
Map
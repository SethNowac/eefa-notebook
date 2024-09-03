import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F1.1 Exploring images
#  Checkpoint:   F11a
#  Author:       Jeff Howarth
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Load an image from its Earth Engine ID.
first_image = ee.Image(
'LANDSAT/LT05/C02/T1_L2/LT05_118038_20000606')

# Inspect the image object in the Console.
print(first_image.getInfo())

# Display band 1 of the image as the first map layer.
Map.addLayer(
first_image, 
{
    'bands': ['SR_B1'], 
    'min': 8000, 
    'max': 17000
},
'Layer 1' 
)

# Display band 2 as the second map layer.
Map.addLayer(
first_image,
{
    'bands': ['SR_B2'],
    'min': 8000,
    'max': 17000
},
'Layer 2',
0, 
1 
)

# Display band 3 as the third map layer.
Map.addLayer(
first_image,
{
    'bands': ['SR_B3'],
    'min': 8000,
    'max': 17000
},
'Layer 3',
1, 
0 
)

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------


Map
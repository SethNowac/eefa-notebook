import ee 
import geemap

Map = geemap.Map()

#*** Start of imports. If edited, may not auto-convert in the playground. ***#
geometry = \
\
[
{
    "type": "rectangle"
}
] 
ee.Geometry.Polygon(
[[[-112.1088347655006, 38.522463862329126],
[-112.1088347655006, 38.22315763773188],
[-111.91520073229748, 38.22315763773188],
[-111.91520073229748, 38.522463862329126]]], None, False)
#**** End of imports. If edited, may not auto-convert in the playground. ****#
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      A3.6 Working With GPS and Weather Data
#  Checkpoint:   A36b
#  Authors:      Peder Engelstad, Daniel Carver, Nicholas E. Young
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Import the data and add it to the map and print.
cougarF53 = ee.FeatureCollection(
'projects/gee-book/assets/A3-6/cougarF53')

Map.centerObject(cougarF53, 10)

Map.addLayer(cougarF53, {}, 'cougar presence data')

print(cougarF53, 'cougar data'.getInfo())

# Call in image collection and filter.
Daymet = ee.ImageCollection('NASA/ORNL/DAYMET_V4') \
.filterDate('2014-02-11', '2014-11-02') \
.filterBounds(geometry)

def func_zah(image):
    return image.clip(geometry) \
.map(func_zah)



print(Daymet, 'Daymet'.getInfo())

# Convert to a multiband image.
DaymetImage = Daymet.toBands()

print(DaymetImage, 'DaymetImage'.getInfo())

# Call the sample regions function.
samples = DaymetImage.sampleRegions(
collection = cougarF53,
properties = ['id'],
scale = 1000
)

print(samples, 'samples'.getInfo())

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------

# Export value added data to your Google Drive.
geemap.ee_export_vector_to_drive(
collection = samples,
description = 'cougarDaymetToDriveExample',
fileFormat = 'csv'
)

# Apply a median reducer to the dataset.
daymet1 = Daymet \
.median() \
.clip(geometry)

print(daymet1.getInfo())

# Export the image to drive.
Export.image.toDrive(
image = daymet1,
description = 'MedianValueForStudyArea',
scale = 1000,
region = geometry,
maxPixels = 1e9
)

# -----------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------
Map
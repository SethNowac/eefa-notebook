import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F4.8 Data Fusion: Merging Classification Streams
#  Checkpoint:   F48a
#  Authors:      Jeff Cardille, Rylan Boothman, Mary Villamor, Elijah Perez,
#                Eidan Willis, Flavie Pelletier
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

events = ee.ImageCollection(
'projects/gee-book/assets/F4-8/cleanEvents')
print(events, 'List of Events'.getInfo())
print('Number of events:', events.size().getInfo())

print(ui.Thumbnail(events, {
    'min': 0,
    'max': 3,
    'palette': ['black', 'green', 'blue', 'yellow'],
    'framesPerSecond': 1,
    'dimensions': 1000
}).getInfo())

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------
Map
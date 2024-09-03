import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F1.0 Exploring images
#  Checkpoint:   F10b
#  Author:       Ujaval Gandhi
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a = 1
b = 2

result = ee.Number(a).add(b)
print(result.getInfo())

yearList = ee.List.sequence(1980, 2020, 5)
print(yearList.getInfo())

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------

Map
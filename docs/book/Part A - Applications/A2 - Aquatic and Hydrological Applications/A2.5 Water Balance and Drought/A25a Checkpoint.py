import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      A2.5 Water Balance and Drought
#  Checkpoint:   A25a
#  Authors:      Ate Poortinga, Quyen Nguyen, Nyein Soe Thwal, Andréa Puzzi Nicolau
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Import the Lower Mekong boundary.
mekongBasin = ee.FeatureCollection(
    'projects/gee-book/assets/A2-5/lowerMekongBasin')

# Center the map.
Map.centerObject(mekongBasin, 5)

# Add the Lower Mekong Basin boundary to the map.
Map.addLayer(mekongBasin, {}, 'Lower Mekong basin')

# Set start and end years.
startYear = 2010
endYear = 2020

# Create two date objects for start and end years.
startDate = ee.Date.fromYMD(startYear, 1, 1)
endDate = ee.Date.fromYMD(endYear + 1, 1, 1)

# Make a list with years.
years = ee.List.sequence(startYear, endYear)

# Make a list with months.
months = ee.List.sequence(1, 12)

# Import the CHIRPS dataset.
CHIRPS = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')

# Filter for the relevant time period.
CHIRPS = CHIRPS.filterDate(startDate, endDate)

# We apply a nested loop where we first map over
# the relevant years and then map over the relevant
# months. The function returns an image with the total (sum)
# rainfall for each month. A flatten is applied to convert a
# feature collection of features into a single feature collection.
monthlyPrecip = ee.ImageCollection.fromImages(

def func_bgd(y):
        return months.map(function(m) {
            w = CHIRPS.filter(ee.Filter \
                    .calendarRange(y, y, 'year')) \
                .filter(ee.Filter.calendarRange(m, m,
                    'month')) \
                .sum()
            return w.set('year', y) \
                .set('month', m) \
                .set('system:time_start', ee.Date \
                    .fromYMD(y, m, 1))

        })

    years.map(func_bgd
).flatten()












).flatten()
)

# Add the layer with monthly mean. Note that we clip for the Mekong river basin.
precipVis = {
    'min': 0,
    'max': 250,
    'palette': 'white, blue, darkblue, red, purple'
}

Map.addLayer(monthlyPrecip.mean().clip(mekongBasin),
    precipVis,
    '2015 precipitation')

# Set the title and axis labels for the chart.
title = {
    'title': 'Monthly precipitation',
    'hAxis': {
        'title': 'Time'
    },
    'vAxis': {
        'title': 'Precipitation (mm)'
    },
}

# Plot the chart using the Mekong boundary.
chartMonthly = ui.Chart.image.seriesByRegion({
        'imageCollection': monthlyPrecip,
        'regions': mekongBasin.geometry(),
        'reducer': ee.Reducer.mean(),
        'band': 'precipitation',
        'scale': 5000,
        'xProperty': 'system:time_start'
    }).setSeriesNames(['P']) \
    .setOptions(title) \
    .setChartType('ColumnChart')

# Print the chart.
print(chartMonthly)

# -----------------------------------------------------------------------------------
# CHECKPOINT
# -----------------------------------------------------------------------------------
Map
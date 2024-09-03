import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F1.0 Exploring images
#  Checkpoint:   F10a
#  Author:       Ujaval Gandhi
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

print('Hello World'.getInfo())

city = 'San Francisco'
print(city.getInfo())

population = 873965
print(population.getInfo())

cities = ['San Francisco', 'Los Angeles', 'New York', 'Atlanta']
print(cities.getInfo())

cityData = {
    'city': 'San Francisco',
    'coordinates': [-122.4194, 37.7749],
    'population': 873965
}
print(cityData.getInfo())


def func_rwk(name):
    return 'Hello ' + name

greet = func_rwk


print(greet('World').getInfo())
print(greet('Readers').getInfo())

# This is a comment!

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------


Map
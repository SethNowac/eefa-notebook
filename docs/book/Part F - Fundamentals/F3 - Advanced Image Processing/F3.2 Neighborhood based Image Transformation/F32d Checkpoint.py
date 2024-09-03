import ee 
import math
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F3.2 Neighborhood-Based Image Transformation
#  Checkpoint:   F32d
#  Authors:      Karen, Andrea, David, Nick
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Create and print a uniform kernel to see its weights.
print('A uniform kernel:', ee.Kernel.square(2))

# Define a point of interest in Odessa, Washington, USA.
point = ee.Geometry.Point([-118.71845096212049,
    47.15743083101999])
Map.centerObject(point)

# Load NAIP data.
imageNAIP = ee.ImageCollection('USDA/NAIP/DOQQ') \
    .filterBounds(point) \
    .filter(ee.Filter.date('2017-01-01', '2018-12-31')) \
    .first()

Map.centerObject(point, 17)

TrueColor = {
    'bands': ['R', 'G', 'B'],
    'min': 0,
    'max': 255
}
Map.addLayer(imageNAIP, TrueColor, 'True color')

# Begin smoothing example.
# Define a square, uniform kernel.
uniformKernel = ee.Kernel.square({
    'radius': 2,
    'units': 'meters',
})

# Convolve the image by convolving with the smoothing kernel.
smoothed = imageNAIP.convolve(uniformKernel)
Map.addLayer(smoothed, {
    'min': 0,
    'max': 255
}, 'smoothed image')

# Begin Gaussian smoothing example.
# Print a Gaussian kernel to see its weights.
print('A Gaussian kernel:', ee.Kernel.gaussian(2))

# Define a square Gaussian kernel:
gaussianKernel = ee.Kernel.gaussian({
    'radius': 2,
    'units': 'meters',
})

# Convolve the image with the Gaussian kernel.
gaussian = imageNAIP.convolve(gaussianKernel)
Map.addLayer(gaussian, {
    'min': 0,
    'max': 255
}, 'Gaussian smoothed image')

# Begin edge detection example.
# For edge detection, define a Laplacian kernel.
laplacianKernel = ee.Kernel.laplacian8()

# Print the kernel to see its weights.
print('Edge detection Laplacian kernel:', laplacianKernel)

# Convolve the image with the Laplacian kernel.
edges = imageNAIP.convolve(laplacianKernel)
Map.addLayer(edges, {
    'min': 0,
    'max': 255
}, 'Laplacian convolution image')

# Begin image sharpening example.
# Define a "fat" Gaussian kernel.
fat = ee.Kernel.gaussian({
    'radius': 3,
    'sigma': 3,
    'magnitude': -1,
    'units': 'meters'
})

# Define a "skinny" Gaussian kernel.
skinny = ee.Kernel.gaussian({
    'radius': 3,
    'sigma': 0.5,
    'units': 'meters'
})

# Compute a difference-of-Gaussians (DOG) kernel.
dog = fat.add(skinny)

# Print the kernel to see its weights.
print('DoG kernel for image sharpening', dog)

# Add the DoG convolved image to the original image.
sharpened = imageNAIP.add(imageNAIP.convolve(dog))
Map.addLayer(sharpened, {
    'min': 0,
    'max': 255
}, 'DoG edge enhancement')

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------

# Begin median example.
# Pass a median neighborhood filter using our uniformKernel.
median = imageNAIP.reduceNeighborhood({
    'reducer': ee.Reducer.median(),
    'kernel': uniformKernel
})

Map.addLayer(median, {
    'min': 0,
    'max': 255
}, 'Median Neighborhood Filter')

# Mode example
# Create and display a simple two-class image.
veg = imageNAIP.select('N').gt(200)

# Display the two-class (binary) result.
binaryVis = {
    'min': 0,
    'max': 1,
    'palette': ['black', 'green']
}
Map.addLayer(veg, binaryVis, 'Vegetation categorical image')

# Compute the mode in each 5x5 neighborhood and display the result.
mode = veg.reduceNeighborhood({
    'reducer': ee.Reducer.mode(),
    'kernel': uniformKernel
})

Map.addLayer(mode, binaryVis, 'Mode Neighborhood Filter on Vegetation categorical image')

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------

# Begin Dilation example.
# Dilate by taking the max in each 5x5 neighborhood.
max = veg.reduceNeighborhood({
    'reducer': ee.Reducer.max(),
    'kernel': uniformKernel
})

Map.addLayer(max, binaryVis, 'Dilation using max')

# Begin Erosion example.
# Erode by taking the min in each 5x5 neighborhood.
min = veg.reduceNeighborhood({
    'reducer': ee.Reducer.min(),
    'kernel': uniformKernel
})

Map.addLayer(min, binaryVis, 'Erosion using min')

# Begin Opening example.
# Perform an opening by dilating the eroded image.
openedVeg = min.reduceNeighborhood({
    'reducer': ee.Reducer.max(),
    'kernel': uniformKernel
})

Map.addLayer(openedVeg, binaryVis, 'Opened image')

# Begin Closing example.
# Perform a closing by eroding the dilated image.
closedVeg = max.reduceNeighborhood({
    'reducer': ee.Reducer.min(),
    'kernel': uniformKernel
})

Map.addLayer(closedVeg, binaryVis, 'Closed image')

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------

# Begin Standard Deviation example.
# Define a big neighborhood with a 7-meter radius kernel.
bigKernel = ee.Kernel.square({
    'radius': 7,
    'units': 'meters'
})

# Compute SD in a neighborhood.
sd = imageNAIP.reduceNeighborhood({
    'reducer': ee.Reducer.stdDev(),
    'kernel': bigKernel
})

Map.addLayer(sd, {
    'min': 0,
    'max': 70
}, 'SD')

# Begin entropy example.
# Create an integer version of the NAIP image.
intNAIP = imageNAIP.int()

# Compute entropy in a neighborhood.
entropy = intNAIP.select('N').entropy(bigKernel)

Map.addLayer(entropy, {
    'min': 1,
    'max': 3
}, 'entropy')

# Begin GLCM example.
# Use the GLCM to compute a large number of texture measures.
glcmTexture = intNAIP.glcmTexture(7)
print('view the glcmTexture output', glcmTexture)

# Display the 'contrast' results for the red, green and blue bands.
contrastVis = {
    'bands': ['R_contrast', 'G_contrast', 'B_contrast'],
    'min': 40,
    'max': 1000
}

Map.addLayer(glcmTexture, contrastVis, 'contrast')

# Begin spatial statistics example using Geary's C.

# Create a list of weights for a 9x9 kernel.
list = [1, 1, 1, 1, 1, 1, 1, 1, 1]
# The center of the kernel is zero.
centerList = [1, 1, 1, 1, 0, 1, 1, 1, 1]
# Assemble a list of lists: the 9x9 kernel weights as a 2-D matrix.
lists = [list, list, list, list, centerList, list, list, list,
    list
]
# Create the kernel from the weights.
# Non-zero weights represent the spatial neighborhood.
kernel = ee.Kernel.fixed(9, 9, lists, -4, -4, False)

# Use the max among bands as the input.
maxBands = imageNAIP.reduce(ee.Reducer.max())

# Convert the neighborhood into multiple bands.
neighBands = maxBands.neighborhoodToBands(kernel)

# Compute local Geary's C, a measure of spatial association.
gearys = maxBands.subtract(neighBands).pow(2).reduce(ee.Reducer \
        .sum()) \
    .divide(math.pow(9, 2))

Map.addLayer(gearys, {
    'min': 20,
    'max': 2500
}, "Geary's C")

#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------



Map
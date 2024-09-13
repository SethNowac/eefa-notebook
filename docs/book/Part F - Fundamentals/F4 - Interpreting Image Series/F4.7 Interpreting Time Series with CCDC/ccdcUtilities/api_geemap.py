import ee 
import geemap

m = geemap.Map()

Classification = \
require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/classification.js')

CCDC = \
require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/ccdc.js')

Inputs = \
require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/inputs.js')

Dates = \
require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/dates.js')

Change = \
require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/change.js')


Classification = Classification
CCDC = CCDC
Inputs = Inputs
Dates = Dates
Change = Change
m
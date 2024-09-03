import ee 
import geemap

Map = geemap.Map()

'To access the latest version of GEEDiT (and legacy versions), use the following link':
'https':#liverpoolgee.wordpress.com/geedit-geedit-reviewer/

This tutorial was built using GEEDiT v2.02, and should also be valid for any later versions of version 2 that become available in the future. On this page you will see that there are actually two different GEEDiTs for each version. The first accesses Landsat Tier 1 imagery, and the second Landsat Tier 2. The former represent the highest quality imagery with respect to both spectral properties and geolocation accuracy, whereas the latter contains imagery that does not meet Tier 1 criteria. For some regions (e.g., Antarctica and some smaller islands) Tier 2 does provide a greater volume of imagery compared to Tier 1 that may be usable for particular research questions. However, in most cases, you will find that Tier 1 imagery is available.
Map
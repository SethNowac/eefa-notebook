import ee

# high-level image functions
 
def AssignDefault(x, dv):
    return x if x is not None else dv

def CalculateWidth_waterMask(imgIn):
  
    from . import functions_centerline_width as clWidthFun
    
    crs = imgIn.get('crs')
    scale = imgIn.get('scale')
    imgId = imgIn.get('image_id')
    bound = imgIn.select('riverMask').geometry()
    angle = imgIn.select('orthDegree')
    dem = ee.Image("MERIT/DEM/v1_0_3")
    infoEnds = imgIn.select('riverMask')
    infoExport = (imgIn.select('channelMask')
    # .addBands(imgIn.select('^flag.*'))
    .addBands(dem.rename('flag_elevation')))
    dm = imgIn.select('distanceMap')
    
    widths = clWidthFun.GetWidth(angle, infoExport, infoEnds, dm, crs, bound, scale, imgId, None) \
    .map(clWidthFun.prepExport)
    return(widths)


def rwGen_waterMask(MAXDISTANCE, FILL_SIZE, MAXDISTANCE_BRANCH_REMOVAL, AOI, RIVERDATA):
    
    # assign default values
    # WATER_METHOD = AssignDefault(WATER_METHOD, 'Jones2019')
    MAXDISTANCE = AssignDefault(MAXDISTANCE, 4000)
    FILL_SIZE = AssignDefault(FILL_SIZE, 333)
    MAXDISTANCE_BRANCH_REMOVAL = AssignDefault(MAXDISTANCE_BRANCH_REMOVAL, 500)
    AOI = AssignDefault(AOI, None)
    
    RIVERDATA = AssignDefault(RIVERDATA, ee.FeatureCollection("users/eeProject/grwl"))
    
    # grwl = ee.FeatureCollection("users/eeProject/grwl")
    from . import functions_landsat as lsFun
    from . import functions_river as riverFun
    from . import functions_centerline_width as clWidthFun
    
    # generate function based on user choice
    def tempFUN(img):
        tempAoi = ee.Algorithms.If(AOI, AOI, img.geometry())
        img = img.clip(tempAoi)
        
        # derive water mask and masks for flags
        # imgOut = lsFun.CalculateWaterAddFlagsSR(image, WATER_METHOD)
        # calculate river mask
        imgOut = riverFun.ExtractRiver(img, RIVERDATA, MAXDISTANCE, FILL_SIZE)
        # calculate centerline
        imgOut = clWidthFun.CalculateCenterline(imgOut)
        # calculate orthogonal direction of the centerline
        imgOut = clWidthFun.CalculateOrthAngle(imgOut)
        # export widths
        widthOut = CalculateWidth_waterMask(imgOut)
        
        return(ee.FeatureCollection(widthOut))
    
    return(tempFUN)
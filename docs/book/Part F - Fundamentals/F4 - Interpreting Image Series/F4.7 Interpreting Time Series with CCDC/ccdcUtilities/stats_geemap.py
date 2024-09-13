import ee 
import geemap

m = geemap.Map()


UNIT = ee.Number(1)

# Beta function
def betaNum(x, y):
    x = ee.Number(x)
    y = ee.Number(y)
    num = x.gamma().multiply(y.gamma())
    den = x.add(y).gamma()
    return ee.Number(num.divide(den))


# Image version of beta function
def beta(x, y):
    x = ee.Image(x)
    y = ee.Image(y)
    num = x.gamma().multiply(y.gamma())
    den = x.add(y).gamma()
    return ee.Image(num.divide(den))


def incbetaNum(x, a, b):
    a = ee.Number(a)
    b = ee.Number(b)
    x = ee.Number(x)
    #Higher yields more precise numbers but add computation time
    count = 100
    v = ee.List.sequence(0, x, None, count)
    # Calculate midpoint of intervals
    s1 = ee.Array(v.slice(0, count-1))
    s2 = ee.Array(v.slice(1, count))
    v = s1.add(s2).divide(2)
    # Get interval width
    dx = v.get([1]).subtract(v.get([0]))
    unitArray = ee.Array(ee.List.repeat(1, count-1))
    _incbeta = v.pow(a.subtract(UNIT)).multiply(unitArray.subtract(v).pow(b.subtract(UNIT)))
    incbeta = _incbeta.reduce(ee.Reducer.sum(), [0]).multiply(dx).get([0])
    return incbeta


# RE-implement to work for images
def incbeta(x, a, b):
    a = ee.Image(a)
    b = ee.Image(b)
    x = ee.Image(x)
    nInt = ee.Number(100)
    dx = x.divide(nInt)
    seq = ee.Image.constant(ee.List.sequence(0, nInt))
    # m.addLayer(seq)
    iv = dx.multiply(seq)
    # m.addLayer(iv)
    # Calculate midpoint of intervals
    s1 = iv.select(ee.List.sequence(0, nInt.subtract(1)))
    s2 = iv.select(ee.List.sequence(1, nInt))
    iv = s1.add(s2).divide(2)
    # m.addLayer(iv)

    unitImg = ee.Image(1)
    _incbeta = iv.pow(a.subtract(unitImg)).multiply(unitImg.subtract(iv).pow(b.subtract(unitImg)))
    incbetaOut = _incbeta.reduce(ee.Reducer.sum()).multiply(dx)
    return incbetaOut



# Regularized incomplete beta function
def regincbetaNum(x, a, b):
    return ee.Number(incbetaNum(x,a,b)).divide(ee.Number(incbetaNum(1,a,b)))


# image version
def regincbeta(x, a, b):
    return ee.Image(incbeta(x,a,b)).divide(ee.Image(incbeta(1,a,b)))



# CDF of F distribution
def F_cdfNum(x, v1, v2):
    x = ee.Number(x)
    v1 = ee.Number(v1)
    v2 = ee.Number(v2)
    k = v2.divide(v2.add(v1.multiply(x)))
    cdf = UNIT.subtract(regincbetaNum(k, v2.divide(2), v1.divide(2)))
    return cdf


# CDF of F distribution, image version
def F_cdf(x, v1, v2):
    x = ee.Image(x)
    v1 = ee.Image(v1)
    v2 = ee.Image(v2)
    k = v2.divide(v2.add(v1.multiply(x)))
    cdf = ee.Image(1).subtract(regincbeta(k, v2.divide(2), v1.divide(2)))
    return cdf


# Using implementation of F-pdf from scipy.stats.f
def F_pdf(x, df1, df2):
    x = ee.Number(x)
    df1 = ee.Number(df1)
    df2 = ee.Number(df2)
    num = df2.pow(df2.divide(2)).multiply(df1.pow(df1.divide(2))).multiply(x.pow(df1.divide(2).subtract(1)))
    den = df2.add(df1.multiply(x)).pow(df1.add(df2).divide(2)).multiply(beta(df1.divide(2), df2.divide(2)))
    return ee.Number(num.divide(den))




exports = {
    'F_cdf': F_cdf,
}
m
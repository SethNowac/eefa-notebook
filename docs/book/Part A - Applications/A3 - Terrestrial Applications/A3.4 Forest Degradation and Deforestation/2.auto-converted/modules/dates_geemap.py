import ee 
import geemap

m = geemap.Map()



# Julian date of date 01-01-0001
ORIGIN = 1721423
# Conversion factor from ms to days
MS_TO_DAYS = 86400000
# Number of days between 01-01-0001 (inclusive) and 01-01-1970 (non-inclusive)
EPOCH_DAYS = ee.Number(719163)



def msToDays(ms):
    return ee.Number(ms).divide(MS_TO_DAYS)



def dateToJdays(str_date):
    if (not str_date):
        return('Required parameter [str_date] missing')

    date = ee.Date(str_date)

    # Convert unix time to days
    return msToDays(date.millis()).add(EPOCH_DAYS)




def jdaysToms(jdays):
    daysSinceEpoch = ee.Number(jdays).subtract(EPOCH_DAYS)
    return daysSinceEpoch.multiply(MS_TO_DAYS)



def jdaysToDate(jdays):
    return ee.Date(jdaysToms(jdays))


def msToJdays(ms):
    return ee.Number(msToDays(ms)).add(EPOCH_DAYS)


def msToFrac(ms):
    year = (ee.Date(ms).get('year')) 
    frac = (ee.Date(ms).getFraction('year'))  
    return year.add(frac)


def fracToms(frac):
    fyear = ee.Number(frac)
    year = fyear.floor()
    d = fyear.subtract(year).multiply(365)
    day_one = ee.Date.fromYMD(year, 1, 1)
    return day_one.advance(d, 'day').millis()



def fracToDate(frac):
    ms = fracToms(frac)
    return msToDate(ms)


def msToDate(ms): return jdaysToDate(msToJdays(ms))



def convertDate(options):
    inputFormat = (options is not None and options["inputFormat"]) or 0
    inputDate = (options is not None and options["inputDate"]) or None
    outputFormat = (options is not None and options["outputFormat"]) or 0

    if (not inputDate):
        return('Required parameter [inputDate] missing')
    
    # First convert to millis
    if (inputFormat == 0):
        milli = jdaysToms(inputDate)
    elif (inputFormat == 1):
        milli = fracToms(inputDate)
    elif (inputFormat == 2):
        milli = inputDate
    elif (inputFormat == 3):
        milli = jdaysToms(dateToJdays(inputDate))

    # Now convert to output format
    if (outputFormat == 0):
        output = msToJdays(milli)
    elif (outputFormat == 1):
        output = msToFrac(milli)
    elif (outputFormat == 2):
        output = milli
    elif (outputFormat == 4):
        output = jdaysToDate(msToJdays(milli))
    
    return output
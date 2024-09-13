import ee 
import geemap

m = geemap.Map()



# Julian date of date 01-01-0001
ORIGIN = 1721423
# Conversion factor from ms to days
MS_TO_DAYS = 86400000
# Number of days between 01-01-0001 (inclusive) and 01-01-1970 (non-inclusive)
EPOCH_DAYS = ee.Number(719163)




def func_dcy(ms):
    return ee.Number(ms).divide(MS_TO_DAYS)

msToDays = func_dcy






def func_xtx(str_date):
if (not str_date):
            return('Required parameter [str_date] missing')

    date = ee.Date(str_date)

    # Convert unix time to days
    return msToDays(date.millis()).add(EPOCH_DAYS)

dateToJdays = func_xtx












def func_oac(jdays):
    daysSinceEpoch = ee.Number(jdays).subtract(EPOCH_DAYS)
    return daysSinceEpoch.multiply(MS_TO_DAYS)

jdaysToms = func_oac






def func_cky(jdays):
    return ee.Date(jdaysToms(jdays))

jdaysToDate = func_cky





def func_ted(ms):
    return ee.Number(msToDays(ms)).add(EPOCH_DAYS)

msToJdays = func_ted





def func_ram(ms):
    year = (ee.Date(ms).get('year'))
    frac = (ee.Date(ms).getFraction('year'))
    return year.add(frac)

msToFrac = func_ram







def func_cwb(frac):
    fyear = ee.Number(frac)
    year = fyear.floor()
    d = fyear.subtract(year).multiply(365)
    day_one = ee.Date.fromYMD(year, 1, 1)
    return day_one.advance(d, 'day').millis()


fracToms = func_cwb











def func_kyt(frac):
    ms = fracToms(frac)
    return msToDate(ms)

fracToDate = func_kyt






def func_ris(ms)return jdaysToDate(msToJdays(ms))}:
def msToDate(ms)return jdaysToDate(msToJdays(ms))}:
msToDate = func_ris




def func_bmo(options):
    inputFormat = (options && options.inputFormat) or 0
    inputDate = (options && options.inputDate) or None
    outputFormat = (options && options.outputFormat) or 0

if (not inputDate):
            return('Required parameter [inputDate] missing')


    # First convert to millis
if (inputFormat == 0):
            milli = jdaysToms(inputDate)
if (inputFormat == 1):
            milli = fracToms(inputDate)
if (inputFormat == 2):
            milli = inputDate
if (inputFormat == 3):
            milli = jdaysToms(dateToJdays(inputDate))


    # Now convert to output format
if (outputFormat == 0):
            output = msToJdays(milli)
if (outputFormat == 1):
            output = msToFrac(milli)
if (outputFormat == 2):
            output = milli
if (outputFormat == 4):
            output = jdaysToDate(msToJdays(milli))


    return output

convertDate = func_bmo



































exports = {
    'msToDays': msToDays,
    'dateToJdays': dateToJdays,
    'jdaysToms': jdaysToms,
    'jdaysToDate': jdaysToDate,
    'msToJdays': msToJdays,
    'msToFrac': msToFrac,
    'msToDate': msToDate,
    'fracToms': fracToms,
    'convertDate': convertDate
}
m
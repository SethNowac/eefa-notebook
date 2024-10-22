

// Julian date of date 01-01-0001
var ORIGIN = 1721423
// Conversion factor from ms to days
var MS_TO_DAYS = 86400000
// Number of days between 01-01-0001 (inclusive) and 01-01-1970 (non-inclusive)
var EPOCH_DAYS = ee.Number(719163)



var msToDays = function(ms){
  return ee.Number(ms).divide(MS_TO_DAYS)
}



var dateToJdays = function(str_date){
   if (!str_date) {
    return('Required parameter [str_date] missing')
  }
  var date = ee.Date(str_date)

  // Convert unix time to days
  return msToDays(date.millis()).add(EPOCH_DAYS)
}



var jdaysToms = function(jdays){
  var daysSinceEpoch = ee.Number(jdays).subtract(EPOCH_DAYS)
  return daysSinceEpoch.multiply(MS_TO_DAYS)
}


var jdaysToDate = function(jdays){
  return ee.Date(jdaysToms(jdays))
}


var msToJdays = function(ms){
  return ee.Number(msToDays(ms)).add(EPOCH_DAYS)
}


var msToFrac = function(ms){
  var year = (ee.Date(ms).get('year')) 
  var frac = (ee.Date(ms).getFraction('year'))  
  return year.add(frac)
}


var fracToms = function(frac){
  var fyear = ee.Number(frac)
  var year = fyear.floor()
  var d = fyear.subtract(year).multiply(365)
  var day_one = ee.Date.fromYMD(year, 1, 1)
  return day_one.advance(d, 'day').millis()
  
}



var fracToDate = function(frac){
  var ms = fracToms(frac)
  return msToDate(ms)
}


var msToDate = function(ms){return jdaysToDate(msToJdays(ms))}



var convertDate = function(options) {
  var inputFormat = (options && options.inputFormat) || 0
  var inputDate = (options && options.inputDate) || null
  var outputFormat = (options && options.outputFormat) || 0

  if (!inputDate) {
    return('Required parameter [inputDate] missing')
  }
  
  // First convert to millis
  if (inputFormat === 0) {
    var milli = jdaysToms(inputDate)
  } else if (inputFormat == 1) {
    var milli = fracToms(inputDate)
  } else if (inputFormat == 2) {
    var milli = inputDate
  } else if (inputFormat == 3) {
    var milli = jdaysToms(dateToJdays(inputDate))
  }

  // Now convert to output format
  if (outputFormat === 0) {
    var output = msToJdays(milli)
  } else if (outputFormat == 1) {
    var output = msToFrac(milli)
  } else if (outputFormat == 2) {
    var output = milli
  } else if (outputFormat == 4) {
    var output = jdaysToDate(msToJdays(milli))
  }
  
  return output
}



exports = {
  msToDays: msToDays,
  dateToJdays: dateToJdays,
  jdaysToms: jdaysToms,
  jdaysToDate: jdaysToDate,
  msToJdays: msToJdays,
  msToFrac: msToFrac,
  msToDate: msToDate,
  fracToms: fracToms,
  convertDate: convertDate
}

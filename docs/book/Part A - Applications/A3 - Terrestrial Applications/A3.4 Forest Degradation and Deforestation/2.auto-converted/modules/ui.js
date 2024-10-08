
// Global variables 
var horizontalStyle = {stretch: 'horizontal', width: '100%'}
var miscUtils = require('projects/AREA2/public:utilities/misc') 
var inputUtils = require('users/parevalo_bu/gee-ccdc-tools:ccdcUtilities/inputs.js') 

// Set default ccd params
var BANDS = ['BLUE','GREEN','RED', 'NIR', 'SWIR1', 'SWIR2'] 
var BPBANDS = ['GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']
var TMBANDS = ['GREEN', 'SWIR2']
var proj = ee.Projection("EPSG:4326").atScale(30)
var dateFormat = 1
var lambda = 20/10000
var maxIter = 10000
var defaultCcdParams = {   
    breakpointBands: BPBANDS,
    tmaskBands: TMBANDS,
    dateFormat: dateFormat,
    lambda: lambda,
    maxIterations: maxIter
  }


var getImageRegion = function(mapObj, geometry, date, vizParams) {
  var imDate = ee.Date(date)
  var befDate = imDate.advance(-1, 'day')
  var aftDate = imDate.advance(1, 'day')
  
  var col = inputUtils.generateCollection(geometry, befDate, aftDate).select(BANDS)
  var selectedImage =  inputUtils.doIndices(col).first()

  selectedImage.get('system:index').evaluate(function(obj) {
    var bandList = [vizParams['red'], vizParams['green'], vizParams['blue']]
    var minList = [vizParams['redMin'], vizParams['greenMin'], vizParams['blueMin']]
    var maxList = [vizParams['redMax'], vizParams['greenMax'], vizParams['blueMax']]
    // Get current number of layers to add images just below the outline of the clicked pixel, which
    // should be always on top, but on top of other existing images
    var numLayers = mapObj.layers().length()
    var insertIndex = numLayers - 1
    // Use insert to preserve clicked box on top and shift any other existing bands
    mapObj.layers().insert(insertIndex, ui.Map.Layer(ee.Image(selectedImage), {bands: bandList, min: minList, max: maxList}, obj))
  })
}


function getBounds(point, projection){
  var toProj = ee.Projection(projection).atScale(30)
  var c1 = point.transform(toProj, 1).coordinates()
    .map(function(p) {
      return ee.Number(p).floor()
    })
  var c2 = c1.map(function(p) { return ee.Number(p).add(1) })
  var p2 =  ee.Geometry.LineString([c1, c2], toProj)
  return p2.bounds()
}

function ccdcTimeseries(collection, dateFormat, ccdc, geometry, band, padding) {
  function harmonicFit(t, coef) {
    var PI2 = 2.0 * Math.PI
    var OMEGAS = [PI2 / 365.25, PI2, PI2 / (1000 * 60 * 60 * 24 * 365.25)]
    var omega = OMEGAS[dateFormat];
    return coef.get([0])
      .add(coef.get([1]).multiply(t))
      .add(coef.get([2]).multiply(t.multiply(omega).cos()))
      .add(coef.get([3]).multiply(t.multiply(omega).sin()))
      .add(coef.get([4]).multiply(t.multiply(omega * 2).cos()))
      .add(coef.get([5]).multiply(t.multiply(omega * 2).sin()))
      .add(coef.get([6]).multiply(t.multiply(omega * 3).cos()))
      .add(coef.get([7]).multiply(t.multiply(omega * 3).sin()));
  };

  function convertDateFormat(date, format) {
    if (format == 0) { 
      var epoch = 719529;
      var days = date.difference(ee.Date('1970-01-01'), 'day')
      return days.add(epoch)
    } else if (format == 1) {
      var year = date.get('year')
      var fYear = date.difference(ee.Date.fromYMD(year, 1, 1), 'year')
      return year.add(fYear)
    } else {
      return date.millis()
    }
  }

  function date_to_segment(t, fit) {
    var tStart = ee.Array(fit.get('tStart'));
    var tEnd = ee.Array(fit.get('tEnd'));
    return tStart.lte(t).and(tEnd.gte(t)).toList().indexOf(1);
  };

  function produceTimeSeries(collection, ccdc, geometry, band) {

    var ccdcFits = ccdc.reduceRegion({
      reducer: ee.Reducer.first(), 
      geometry: geometry, 
      crs: proj
    })
    
    
    if (padding) {
      collection = collection.sort('system:time_start')

      var first = collection.first()
      var last = collection.sort('system:time_start', false).first()
      var fakeDates = ee.List.sequence(first.date().get('year'), last.date().get('year'), padding).map(function(t) {
        var fYear = ee.Number(t);
        var year = fYear.floor()
        return  ee.Date.fromYMD(year, 1, 1).advance(fYear.subtract(year), 'year')
      })
      fakeDates = fakeDates.map(function(d) { 
        return ee.Image().rename(band).set('system:time_start', ee.Date(d).millis())
      })
      collection = collection.merge(fakeDates)
    }    
    
    collection = collection.sort('system:time_start')

    /** Augment images with the model fit. */
    var timeSeries = collection.map(function(img) {
      var time = convertDateFormat(img.date(), dateFormat)
      var segment = date_to_segment(time, ccdcFits)
      var value = img.select(band).reduceRegion({
        reducer: ee.Reducer.first(), 
        geometry: geometry,
        crs: proj
      }).getNumber(band)
      
      var coef = ee.Algorithms.If(segment.add(1), 
        ccdcFits.getArray(band + '_coefs')
          .slice(0, segment, segment.add(1))
          .project([1]),
        ee.Array([0,0,0,0,0,0,0,0,0]))
      
      var fit = harmonicFit(time, ee.Array(coef))
      return img.set({
        value: value,
        fitTime: time,
        fit: fit,
        coef: coef,
        segment: segment,
        dateString: img.date().format("YYYY-MM-dd")
      }).set(segment.format("h%d"), fit)
    })
    return timeSeries
  }
  
  return produceTimeSeries(collection, ccdc, geometry, band)
  
}

function chartTimeseries(table, band, lat, lon, nSegs) {
  nSegs = nSegs || 6
  
  // Get alphabet letter using index
  function getLetter(x){
    var alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    var charCode = alphabet.charCodeAt(x)
    return String.fromCharCode(charCode)
  }
  
  // Build dictionary required to create custom segment chart 
  function buildDict(letter, index){
    var fitName = 'fit '.concat(index.toString())
    return {id: letter, label: fitName, type: 'number'}
  }
  
  // Everything in here is client-side javascript.
  function formatAsDataTable(table) {
    
    // Generate dictionaries for n segments and append to list
    var cols = [{id: 'A', label: 'Date', type: 'date'},
            {id: 'B', label: 'Observation', type: 'number'}]
    for (var i = 1; i < nSegs+1; i++) {
      var dict = buildDict(getLetter(i+1), i)
      cols.push(dict)
    }
    
    var values = table.map(function(list) {
      return {c: list.map(function(item, index) {
          return {"v": index == 0 ? new Date(item) : item }
        })
      }
    })
    return {cols: cols, rows: values}
  }

  /** Compute the limits of the given column */
  function getLimits(table, column) {
    var col = table.map(function(l) { return l[column]; }).filter(function(i) { return i != null })
    return [Math.min.apply(Math, col), Math.max.apply(Math, col)]
  }

  var limits = getLimits(table, 8)
  var formatted = formatAsDataTable(table)
  return ui.Chart(formatted, 'LineChart', {
      title: 'CCDC TS, Latitude, Longitude: ' + lat.toFixed(3) + ', ' + lon.toFixed(3),
      pointSize: 0,
      series: {
        0: { pointSize: 1.8, lineWidth: 0},
      },
      vAxis: {
        title: 'Surface reflectance (' + band + ')',
        viewWindowMode: 'explicit', //'pretty', 
        viewWindow: {
          min: limits[0] * 0.9,
          max: limits[1] * 1.1
        }
      },
      height: '90%', //If 100%, chart starts growing if split panel is resized
      stretch: 'both'
  })
}


var defaultRunParams = {sDate: '2000-01-01', eDate:'2020-01-01', nSegs: 6}
var defaultVizParams = {red: 'SWIR1', green: 'NIR', blue: 'RED', 
                        redMin: 0, redMax: 0.6, 
                        greenMin: 0, greenMax: 0.6, 
                        blueMin: 0, blueMax: 0.6}

// TODO: doctstring
function chartCcdc(ccdParams, runParams, vizParams, 
                    geometry, panel, latitude, longitude, mapObj){
  
  ccdParams = ccdParams || defaultCcdParams
  runParams = runParams || defaultRunParams
  vizParams = vizParams || defaultVizParams
  
  // Set up and run CCDC
  // Need to filter bands because indices code does not currently work if TEMP is included
  var collection = inputUtils.generateCollection(geometry, runParams['sDate'], runParams['eDate']).select(BANDS)
  ccdParams['collection'] =  inputUtils.doIndices(collection)
  var ccdc_tile = ee.Algorithms.TemporalSegmentation.Ccdc(ccdParams)
  
  // mapObj.addLayer(ccdc_tile, {}, "ccdc", false)

  var series = ccdcTimeseries(ccdParams['collection'], ccdParams['dateFormat'], ccdc_tile, geometry, runParams['bandSelect'], 0.1)

  // Snap click box to image
  var ref_image =ee.Image(ccdParams['collection'].first()) 
  var proj = ref_image.projection().atScale(30)
  
  var c1 = geometry.transform(proj, 1).coordinates()
    .map(function(p) {
      return ee.Number(p).floor()
    })
  var c2 = c1.map(function(p) { return ee.Number(p).add(1) })
  var p2 =  ee.Geometry.LineString([c1, c2], proj)
  mapObj.addLayer(p2.bounds(), {}, 'clicked')
  
  // mapObj.addLayer(series, {}, "series", false)

  // Get required list programatically for n segments
  var templist = ["dateString", "value" ]
  for (var i = 0; i < runParams['nSegs']; i++) {
    templist.push("h".concat(i.toString()))
  }
  templist.push("fit")
  var listLength = templist.length
  
  var table = series.reduceColumns(ee.Reducer.toList(listLength, listLength), templist)
                    .get('list')

  // Use evaluate so we don't lock up the browser.
  table.evaluate(function(t, e) {
    var chart = chartTimeseries(t, runParams['bandSelect'], latitude, longitude, runParams['nSegs'])
    // panel.widgets().reset([chart])
    // This is the original code working
    panel.widgets().set(0, chart) 
    // This is the new code for testing that simplifies integration with landtrendr, but breaks resizing figure
    // panel.add(chart) 
    chart.onClick(function(x) {
      if (x) {
        // getImageRegion(mapObj, geometry, x)
        getImageRegion(mapObj, geometry, x, vizParams)
      }
    })
  })
}  

function chartDOY(runParams, mapObj, geometry, panel, lat, lon){
  
  runParams = runParams || defaultRunParams
  
  var col = inputUtils.getLandsat(runParams['sDate'], runParams['eDate'], 1, 366, geometry)
  var ref_image =ee.Image(col.first()) 
  var bounds = getBounds(geometry, ref_image.projection())

  // High number 'ensures' this layer is added on top unless there's that many layers loaded already
  mapObj.layers().insert(20, ui.Map.Layer(bounds, {}, 'clicked'))
  
  var chart = ui.Chart.image.doySeries({
    imageCollection: col.select([runParams['bandSelect']]), 
    region: geometry, 
    scale: 30,
    regionReducer: ee.Reducer.first()
    })
    .setChartType("ScatterChart")
    .setOptions({
      title: 'DOY Plot, Latitude, Longitude: ' + lat.toFixed(4) + ', ' + lon.toFixed(4),
      pointSize: 0,
      series: {
        0: { pointSize: 2},
      },
      vAxis: {
        title: 'Surface reflectance (' + runParams['bandSelect'] + ')',
      },
      hAxis: {
        title: "Day of year",
        viewWindowMode: 'explicit', 
        viewWindow: {
          min: 0,
          max: 366
        }
      },
      height: '90%', //If 100%, chart starts growing if split panel is resized
      stretch: 'both',
      explorer: {} ,
    })

  panel.widgets().set(0, chart) 
  
}


function initializeTSViewer(mapObj, ccdParams, runParams, vizParams) {
  ccdParams = ccdParams || defaultCcdParams
  runParams = runParams || defaultRunParams
  vizParams = vizParams || defaultVizParams
  
  var locationButton = ui.Button({
  label:'User location',
  style:{stretch: 'horizontal', backgroundColor: 'rgba(255, 255, 255, 0.0)'}
  })
  
  locationButton.onClick(function() {
  var geoSuccess = function(position) {
    var lat = position.coords.latitude;
    var lon = position.coords.longitude;
     if (navigator.geolocation) {
      var point = ee.Geometry.Point([lon, lat])
      mapObj.centerObject(point)
      mapObj.addLayer(point, {color:'#0099ff'}, "Current location")
    }
    else {
      console.log('Geolocation is not supported for this Browser/OS.');
    }
  };
  navigator.geolocation.getCurrentPosition(geoSuccess);

  });
  
  var waitMsg = ui.Label({
    value: 'Processing, please wait',
    style: {
      position: 'bottom-left',
      stretch: 'horizontal',
      textAlign: 'center',
      fontWeight: 'bold',
      backgroundColor: 'rgba(255, 255, 255, 0.0)'
    }
  });
  
  var sDate = ui.Textbox({
    placeholder: "Start date in 'yyyy-mm-dd' format",
    value: '1997-01-01',
    style:{stretch: 'horizontal', backgroundColor: 'rgba(255, 255, 255, 0.0)'}
  })

  var eDate = ui.Textbox({
    placeholder: "End date in 'yyyy-mm-dd' format",
    value: '2020-01-01',
    style:{stretch: 'horizontal', backgroundColor: 'rgba(255, 255, 255, 0.0)'}
  })
  
  var chartPanel = ui.Panel({
  style: {
    height: '30%',
    width: '100%',
    position: 'bottom-center',
    padding: '0px',
    margin: '0px',
    border: '0px',
    // whiteSpace:'nowrap',
    stretch: 'both',
    backgroundColor: 'rgba(255, 255, 255, 0.5)'
    } 
  });
  
  
  var bandSelect = ui.Select({items:BANDS, value:'SWIR1', 
    style:{stretch: 'horizontal', backgroundColor: 'rgba(255, 255, 255, 0.0)'
  }});
  
  
  // Map callback function, set the first time and after map is cleared
  var mapCallback = function(coords) {
    // Re-set runParams
    runParams['sDate'] = sDate.getValue()
    runParams['eDate'] = eDate.getValue()
    runParams['bandSelect'] = bandSelect.getValue()
    
    if(dirtyMap === false){
      //mapObj.widgets().set(1, chartPanel)
      dirtyMap = true;
    }
    chartPanel.clear();
    chartPanel.add(waitMsg);
    
    var geometry = ee.Geometry.Point([coords.lon, coords.lat]);
    // Run ccdc and get time series
    chartCcdc(ccdParams, runParams, vizParams, geometry, chartPanel, 
              coords.lat, coords.lon, mapObj) 
  }

  var clearMap = ui.Button({label: 'Clear map', 
                            onClick:function(){
                                      mapObj.clear()
                                      mapObj.widgets().set(0, controlPanel);
                                      // Need to restablish callback after map.clear
                                      dirtyMap = false
                                      mapObj.setControlVisibility({zoomControl:false, layerList:true})
                                      mapObj.onClick(mapCallback)
                            },
                            style:{stretch: 'horizontal'}
  })
  
  // Floating widget with map controls
  var controlPanel = ui.Panel({
    widgets: [bandSelect, sDate, eDate, locationButton, clearMap], //label,
    style: {
      height: '230px',
      width: '120px',
      position: 'top-left',
      backgroundColor: 'rgba(255, 255, 255, 0)'
      
    }
  });
  
  // Set initial map options
  var dirtyMap = false
  mapObj.onClick(mapCallback) 
  mapObj.setOptions('SATELLITE');
  mapObj.widgets().set(0, controlPanel);
  mapObj.setControlVisibility({zoomControl:false, layerList:true})
  mapObj.style().set({cursor:'crosshair'});
  return ui.SplitPanel(mapObj, chartPanel, 'vertical')
  
}




function getTSChart(mapObj, ccdParams, runParams, vizParams) {
  ccdParams = ccdParams || defaultCcdParams
  runParams = runParams || defaultRunParams
  vizParams = vizParams || defaultVizParams
  
  var waitMsg = ui.Label({
    value: 'Processing, please wait',
    style: {
      position: 'bottom-left',
      stretch: 'horizontal',
      textAlign: 'center',
      fontWeight: 'bold',
      backgroundColor: 'rgba(255, 255, 255, 0.0)'
    }
  });
  
  var chartPanel = ui.Panel({
  style: {
    height: '30%',
    width: '100%',
    position: 'bottom-center',
    padding: '0px',
    margin: '0px',
    border: '0px',
    // whiteSpace:'nowrap',
    stretch: 'both',
    backgroundColor: 'rgba(255, 255, 255, 0.5)'
    } 
  });
  
  // Map callback function, set the first time and after map is cleared
  var mapCallback = function(coords) {
    if(dirtyMap === false){
      //mapObj.widgets().set(1, chartPanel)
      dirtyMap = true;
    }
    chartPanel.clear();
    chartPanel.add(waitMsg);
    
    var geometry = ee.Geometry.Point([coords.lon, coords.lat]);
    // Retrieve time series of DOY plot
    if (vizParams.tsType == "Time series"){
      chartCcdc(ccdParams, runParams, vizParams, geometry, chartPanel, 
              coords.lat, coords.lon, mapObj)
    
    } else if (vizParams.tsType == "DOY") {
      chartDOY(runParams, mapObj, geometry, chartPanel,
                coords.lat, coords.lon)
    }
  }

  // Set initial map options and link map and chart
  var dirtyMap = false
  mapObj.onClick(mapCallback) 
  
  return chartPanel
  
}



function generateSelectorPanel(name, items){
  var selectorPanel = ui.Panel(
    [
      ui.Label({value: name, style:{stretch: 'horizontal', color:'black'}}),
      ui.Select({items: items, style:{stretch: 'horizontal'}}) 
    ],
    ui.Panel.Layout.Flow('horizontal'),
    horizontalStyle
  )
  return selectorPanel
}



function generateColorbarLegend(min, max, palette, orientation, title){
   var viz = {min:min, max:max, palette:palette};
   
   if (orientation == 'vertical'){
     
     var layout = ui.Panel.Layout.flow('vertical', false)
     var coordinate = 'latitude'
     var params = {bbox:'0,0,10,100', dimensions:'10x200'}
     var width = '50px'
     
   } else if (orientation == 'horizontal'){
     
     var layout = ui.Panel.Layout.flow('horizontal', false)
     var coordinate = 'longitude'
     var params = {bbox:'0,0,100,10', dimensions:'200x10'}
     var width = '330px'
     var labwidth = '40px'
     
   } else {
     
     print("Orientation must be 'vertical' or 'horizontal'")
     
   }
   
    // set position of panel
    var legend = ui.Panel({
      style: {
        position: 'middle-left',
      },
      layout: layout
    });
     
    // create the legend image
    var lon = ee.Image.pixelLonLat().select(coordinate)
    var gradient = lon.multiply((viz.max-viz.min)/100.0).add(viz.min);
    var legendImage = gradient.visualize(viz);
     
    // create text for max value
    var maxPanel = ui.Panel({
      widgets: [
        ui.Label(viz['max'])
      ],
      style: {width: labwidth}
    })

    // create thumbnail from the image
    var thumbnail = ui.Thumbnail({
      image: legendImage,
      params: params,
      style: {padding: '1px', position: 'bottom-center'}
    });

    // create text for min value
    var minPanel = ui.Panel({
      widgets: [
        ui.Label(viz['min'])
      ],
      style: {width: labwidth}
    });
     
    // Organize panel and return
    if (orientation == 'vertical'){
      
      legend.add(maxPanel)
      legend.add(thumbnail)
      return legend.add(minPanel)
      
    } else if (orientation == 'horizontal'){
      
      legend.add(minPanel)
      legend.add(thumbnail)
      var outpanel = legend.add(maxPanel)
      
      return ui.Panel({widgets: [
        ui.Label({
          value: title,
          style: {
            padding: '1px', 
            position: 'top-center',
            
          }
        }),
        outpanel
        ], 
        style: {
          position: 'middle-left',
          width: width
        }})
    }  
}


var makeTextPanel = function(label, value, stretch) {
  return ui.Panel(
  [
    ui.Label({value:label, style:{stretch: stretch, color:'black'}}),
    ui.Textbox({value:value, style:{stretch: stretch}}),

  ],
  ui.Panel.Layout.Flow(stretch),
  horizontalStyle
);
}

var arrayRemove = function(arr, value) {
   return arr.filter(function(ele){
       return ele != value;
   });
}

var makeCheckbox = function(label, inputs) {
  return ui.Checkbox({
    label: label, 
    value: true,
    onChange: function(b) {
      if (!b) {
        inputs = arrayRemove(inputs, label)
      } else {
        inputs.push(label)
      }
      // return inputs
    }  
  })
}

var makePanel = function(stretch, widgets) {
 return ui.Panel(
    widgets,
    ui.Panel.Layout.Flow(stretch)); 
}




var training = function(theMap, visLabels, helperFuncs) {
  var self = this
  this.widgs = {}
  // this.outGeo = outGeo

  this.trainingOptions = ['Use All','Within Output Extent']
  this.trainingStrategy = ''
  this.yearOptions = ['Attribute','Specify Year','Predictors in Attributes']
  this.yearStrategy = ''
  this.widgs.panels = makePanel('vertical',
    [
      makeTextPanel('Training Data','projects/GLANCE/TRAINING/MASTER/NA_training_master_Feb_7_data','horizontal'),
      makeTextPanel('Attribute','landcover', 'horizontal'),

    ]
  )
  
  /**
   * List of functions for the selector widget
   */
  this.funcs = [
    this.useAllTraining, 
    this.useRegionTraining,
  ]
  
  this.widgs.dropdown = makePanel('horizontal',
    [
      ui.Label('Define training data strategy'),
      ui.Select({
        items: self.trainingOptions,
        onChange: function(i) {
          self.trainingStrategy = i
          self.fc = ee.FeatureCollection(
            self.widgs.panels.widgets().get(0).widgets().get(1).getValue())
        helperFuncs.checkParams()

        }
      })
    ])
  
  this.widgs.yearPanel = makePanel('vertical',[])
  
  this.widgs.dropdown2 = makePanel('horizontal',
    [
      ui.Label('Define strategy for training date'),
      ui.Select({
        items: self.yearOptions,
        onChange: function(i) {
          self.yearStrategy = i
          self.widgs.yearPanel.clear()
          if (i == 'Attribute') {
            self.widgs.yearPanel.add(makeTextPanel('Year attribute','year', 'horizontal'))
          } else if (i == 'Specify Year') {
            self.widgs.yearPanel.add(makeTextPanel('Training year','year', 'horizontal'))
          } 
          helperFuncs.checkParams()
        }
      })
    ])
  
  this.widgs.all = makePanel('vertical',
    [
      ui.Label('Training data procedure',visLabels),
      self.widgs.dropdown,
      self.widgs.panels,
      self.widgs.dropdown2,
      self.widgs.yearPanel
    ]
  )
}



var DrawAreaTool = function(map) {
  var drawingToolLayer = ui.Map.Layer({name: 'Area Selection Tool', visParams: {palette:'#4A8BF4', color:'#4A8BF4' }});

  this.map = map;
  this.selection = null;
  this.active = false;
  this.points = [];
  this.area = null;
  
  this.listeners = [];

  var tool = this;
  
  this.initialize = function() {
    this.map.onClick(this.onMouseClick);
    map.layers().reset()
    map.layers().set(0, drawingToolLayer);
  };
  
  this.startDrawing = function() {
    this.active = true;
    this.points = [];

    this.map.style().set('cursor', 'crosshair');
    drawingToolLayer.setShown(true);
  };
  
  this.stopDrawing = function() {
    tool.active = false;
    tool.map.style().set('cursor', 'hand');

    if(tool.points.length < 2) {
      return;
    }

    var closedPoints = tool.points.slice(0,-1);
    tool.area = ee.Geometry.Polygon(closedPoints)///.bounds();
    
    var empty = ee.Image().byte();
    var test = empty.paint({
      featureCollection: ee.FeatureCollection(tool.area),
      color: 1,
      width: 4
    });
  
    drawingToolLayer.setEeObject(test);

    tool.listeners.map(function(listener) {
      listener(tool.area);
    });
  };
  
  this.onMouseClick = function(coords) {
    if(!tool.active) {
      return;
    }
    
    tool.points.push([coords.lon, coords.lat]);

    var geom = tool.points.length > 1 ? ee.Geometry.LineString(tool.points) : ee.Geometry.Point(tool.points[0]);
    drawingToolLayer.setEeObject(geom);

    if(tool.points.length > 4) {
      tool.stopDrawing();
    }
  };
  
  this.onFinished = function(listener) {
    tool.listeners.push(listener);
  };
  
  this.initialize();
};

var region = function(theMap, grids,regions, visLabels, helperFuncs) {
  var self = this
  this.widgs = {}
  this.widgs.geoPanel = ui.Panel()
  this.regions = regions
  this.theMap = theMap
  this.regionTypes = ['Select Method','Draw on Map','Single Tile','Tile Intersecting Point','Multiple Tiles','Draw Multiple Tiles on Map','Country Boundary']
  this.countryTable = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
  this.countries = self.countryTable.aggregate_histogram('country_na').keys()
  
  this.widgs.singleTilePanel = makePanel('horizontal',
    [
      ui.Label({value:'Vertical #:', style:{color:'red'}}),
      ui.Textbox({value:32, style:{stretch: 'horizontal'}}),
      ui.Label({value:'Horizontal #:', style:{color:'red'}}),
      ui.Textbox({value:61, style:{stretch: 'horizontal'}}) ,
      ui.Label({value:'Region', style:{color:'red'}}),
      ui.Select({items:self.regions,value: self.regions[5], style:{stretch: 'horizontal'}}) 
    ]
  )
  
  
  this.widgs.multiplePanelStart = makePanel('horizontal',
    [
      ui.Label({value:'Vertical # Min:', style:{color:'red'}}),
      ui.Textbox({value:30, style:{stretch: 'horizontal'}}),
      ui.Label({value:'Horizontal # Min:', style:{color:'red'}}),
      ui.Textbox({value:60, style:{stretch: 'horizontal'}}),
      ui.Label({value:'Region', style:{color:'red'}}),
      ui.Select({items:self.regions,value: self.regions[0], style:{stretch: 'horizontal'}}) 
    ]
  )
  
  
  this.widgs.multiplePanelEnd = makePanel('vertical',
    [
      ui.Label({value:'Vertical # Max:', style:{color:'red'}}),
      ui.Textbox({value:35, style:{stretch: 'horizontal'}}),
      ui.Label({value:'Horizontal # End:', style:{color:'red'}}),
      ui.Textbox({value:65, style:{stretch: 'horizontal'}}),
    ]
  )

  this.doAreaTool = function() {
    self.widgs.geoPanel.add(ui.Label('Slowly click five points on the map and the application will generate a rectangle for the output extent geometry.'))
    var tool = new DrawAreaTool(self.theMap);
    tool.startDrawing();
    tool.onFinished(function(geometry) {
      self.outGeo = ee.Feature(geometry);
    });
    
  }


   this.drawMultipleTiles = function() {
    self.widgs.geoPanel.add(ui.Label('Slowly click five points on the map and the application will generate a rectangle for the output extent geometry.'))
    var tool = new DrawAreaTool(self.theMap);
    tool.startDrawing();
    tool.onFinished(function(geometry) {
      var tempGeo = grids.filterBounds(geometry);
  
      tempGeo.size().evaluate(function(val) {
        if (val > 0) {
          self.outGeos = ee.FeatureCollection(tempGeo)
          theMap.addLayer(self.outGeos, {},'Output Geometry')
          theMap.centerObject(self.outGeos)
          self.outGeosSize = val
        } else {
          print('No overlapping tiles found!')
        }
      })
    })
    
  }
  


  this.doSingleTile = function() {
    self.widgs.geoPanel.add(self.widgs.singleTilePanel)
  
    var tempGeo
    var validateTile = ui.Button('Load Tile', function(){
      h = Number(self.widgs.singleTilePanel.widgets().get(3).getValue())
      v = Number(self.widgs.singleTilePanel.widgets().get(1).getValue())
      r = String(self.widgs.singleTilePanel.widgets().get(5).getValue())
      tempGeo = grids.filterMetadata('horizontal','equals',h)
        .filterMetadata('vertical','equals',v)
        .filterMetadata('zone','equals',r)
  
      tempGeo.size().evaluate(function(val) { 
        if (val > 0) {
          self.outGeo = ee.Feature(tempGeo.first())
          theMap.addLayer(self.outGeo, {},'Output Geometry')
          theMap.centerObject(self.outGeo)
        }
        else {
          print('No Tile Found!')
        }
      })
    })
    self.widgs.geoPanel.add(validateTile)
  }
  

  this.doPoint = function() {
    self.hasClicked = false
    theMap.style().set('cursor', 'crosshair');
    self.widgs.geoPanel.add(ui.Label('Click a location on the map to load the intersecting tile'))
    theMap.onClick(function(coords) {
      theMap.layers().reset()
      var latitude = coords.lat
      var longitude = coords.lon
      var point = ee.Geometry.Point([longitude, latitude])
      var tempGeo = grids.filterBounds(point)
      
      theMap.layers().set(0, point)
      tempGeo.size().evaluate(function(val) { 
        if (val > 0) {
          self.outGeo = ee.Feature(tempGeo.first())
          theMap.addLayer(self.outGeo, {},'Output Geometry')
          theMap.centerObject(self.outGeo)
        }
     })
     theMap.unlisten()
    })
  }
  

  this.doMultipleTiles = function() {
    
    self.widgs.geoPanel.add(self.widgs.multiplePanelStart)
    self.widgs.geoPanel.add(self.widgs.multiplePanelEnd)
  
    var tempGeo
    var validateTile = ui.Button('Load Tiles', function(){
      var h1 = Number(self.widgs.multiplePanelStart.widgets().get(3).getValue())
      var v1 = Number(self.widgs.multiplePanelStart.widgets().get(1).getValue())
      
      var h2 = Number(self.widgs.multiplePanelEnd.widgets().get(3).getValue())
      var v2 = Number(self.widgs.multiplePanelEnd.widgets().get(1).getValue())
  
      var r = String(self.widgs.multiplePanelStart.widgets().get(5).getValue())
      tempGeo = grids.filterMetadata('horizontal','greater_than',h1)
        .filterMetadata('horizontal','less_than',h2)
        .filterMetadata('vertical','greater_than',v1)
        .filterMetadata('vertical','less_than',v2)
        .filterMetadata('zone','equals',r)
  
      tempGeo.size().evaluate(function(val) {
        if (val > 0) {
          self.outGeo = ee.FeatureCollection(tempGeo)
          theMap.addLayer(self.outGeo, {},'Output Geometry')
          theMap.centerObject(self.outGeo)
          self.outGeosSize = val
        } else if (val === 0) {
          print('No Tile Found!')
        }
      })
    })
    self.widgs.geoPanel.add(validateTile)
  }
  
  this.widgs.all = makePanel('vertical',
    [
      ui.Label('Define Output Region',visLabels),
  
   // this.widgs.selectRegion,
  //    self.widgs.geoPanel
    ]
  )
  // Evaluate country list to make dropdown
  var countryList = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    .aggregate_histogram('country_na')
    .keys()
    .getInfo()

  this.widgs.countryPanel = makePanel('horizontal',
    [
      ui.Label({value:'Country:', style:{color:'black'}}),
      ui.Select({
        value: countryList[0],
        items: countryList,
        onChange: function(reg) {
          self.outGeo = ee.Feature(
            ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
            .filterMetadata('country_na','equals',reg)
            .union()
          )
        }
      })
    ]
  )


  this.countryFunc = function() {
    self.widgs.geoPanel.add(self.widgs.countryPanel)
  }
  
  this.widgs.selectRegion = makePanel('horizontal',
    [
      ui.Label({value:'Define Study Region:', style:{color:'black'}}),
      ui.Select({
        value: 'Select Method',
        items: self.regionTypes,
        onChange: function(reg) {
          self.widgs.geoPanel.clear()
          Map.unlisten()
          theMap.layers().reset()
          var index = self.regionTypes.indexOf(reg) - 1
          self.geoType = index
          
          var regionFuncs = [
            self.doAreaTool, 
            self.doSingleTile, 
            self.doPoint, 
            self.doMultipleTiles, 
            self.drawMultipleTiles,
            self.countryFunc
          ]
          var regionFunc = regionFuncs[index]
          regionFunc(reg)
          helperFuncs.checkParams()
        }
      })
    ]
  );
  self.widgs.all.add(self.widgs.selectRegion)
  self.widgs.all.add(self.widgs.geoPanel)
}


var classifier = function(classifierList, eeClassifiers, visLabels, helperFuncs) {
  var self = this
  this.widgs = {}
  this.classifierList = classifierList
  this.eeClassifiers = eeClassifiers
  this.visLabels = visLabels
  this.widgs.classifierParams = makePanel('vertical', [])

  this.randomForestOptions = function() {
    self.widgs.classifierParams.add(makeTextPanel('numTrees',100,'horizontal'))
    self.widgs.classifierParams.add(makeTextPanel('variablesPerSplit',null, 'horizontal'))
  }
    
  this.changeClassifier = function(i) {
    var index = self.classifierList.indexOf(i)
    self.classifier = self.eeClassifiers[index]
    self.widgs.classifierParams.clear()
    if (i == 'RandomForest') {
      self.randomForestOptions()
    }
    helperFuncs.checkParams()
  }
  
  this.dateList = '2001-01-01'
  this.widgs.dateBox = makeTextPanel('Dates (YYYY-MM-DD); Comma separated',self.dateList,'horizontal')
  this.widgs.dateBox.widgets().get(1).onChange(function(str) {
    self.dateList = str
  })

  this.widgs.classifierSelector = ui.Panel(
    [
      ui.Label({value:'Classifier', style:{stretch: 'horizontal', color:'black'}}),
      ui.Select({
        items: self.classifierList, 
        onChange: self.changeClassifier,
        style:{stretch: 'horizontal',
        }}),
  
    ],
    ui.Panel.Layout.Flow('horizontal')
  );
  
  this.widgs.all = makePanel('vertical',
    [
      ui.Label('Classification Parameters',self.visLabels),
      self.widgs.dateBox,  
      self.widgs.classifierSelector,
      self.widgs.classifierParams
    ]
  )
}

// PREDICTORS 
var predictors = function(visLabels, coefs, props, helperFuncs) {
  var self = this
  this.widgs = []
  this.widgs.bandChecks = makePanel('vertical', [])
  this.widgs.coefChecks = makePanel('vertical', [])
  this.widgs.ancChecks = makePanel('vertical', [])
  this.widgs.climChecks = makePanel('vertical', [])

    
  this.widgs.inputCheckboxes = []
  this.inputBands = []
  this.inputCoefs = []
  this.ancillary = []
  this.possibleInputs = []
  
  this.fillInputPanels = function(i) {
    self.bands = i

    for (var b = 0; b < i.length; b++) {
      this.possibleInputs.push(i[b])
      var newCheck = makeCheckbox(i[b], self.inputBands)
      newCheck.onChange(function(check, widg) {
        
        var widgIndex = self.widgs.inputCheckboxes.indexOf(widg)
        if (!check) {
          self.inputBands = arrayRemove(self.inputBands, self.possibleInputs[widgIndex])
        } else {
          self.inputBands.push(self.possibleInputs[widgIndex])
        }
      helperFuncs.checkParams()
      })
      self.widgs.inputCheckboxes.push(newCheck)
      self.widgs.bandChecks.add(newCheck)
      self.inputBands.push(i[b])
    }

    for (var c = 0; c < coefs.length; c++) {
    this.possibleInputs.push(coefs[c])

      var newCheck = makeCheckbox(coefs[c], self.inputCoefs)
      newCheck.onChange(function(check, widg) {
        var widgIndex = self.widgs.inputCheckboxes.indexOf(widg)
        if (!check) {
          self.inputCoefs = arrayRemove(self.inputCoefs, self.possibleInputs[widgIndex])
        } else {
          self.inputCoefs.push(self.possibleInputs[widgIndex])
        }
      })
      self.widgs.inputCheckboxes.push(newCheck)
      self.widgs.coefChecks.add(newCheck)
      self.inputCoefs.push(coefs[c])
    }
  }
  
  var ancillaryList = ['ELEVATION','ASPECT','DEM_SLOPE']
  var climateList = ['RAINFALL','TEMPERATURE']

  for (var c = 0; c < ancillaryList.length; c++) {
    this.possibleInputs.push(ancillaryList[c])

      var newCheck = makeCheckbox(ancillaryList[c], self.ancillary)
      newCheck.onChange(function(check, widg) {
        var widgIndex = self.widgs.inputCheckboxes.indexOf(widg)
        if (!check) {
          self.ancillary = arrayRemove(self.ancillary, self.possibleInputs[widgIndex])
        } else {
          self.ancillary.push(self.possibleInputs[widgIndex])
        }
      })
      self.widgs.inputCheckboxes.push(newCheck)
      self.widgs.ancChecks.add(newCheck)
      self.ancillary.push(ancillaryList[c])
  }
   for (var c = 0; c < climateList.length; c++) {
    this.possibleInputs.push(climateList[c])

      var newCheck = makeCheckbox(climateList[c], self.ancillary)
      newCheck.onChange(function(check, widg) {
        var widgIndex = self.widgs.inputCheckboxes.indexOf(widg)
        if (!check) {
          self.ancillary = arrayRemove(self.ancillary, self.possibleInputs[widgIndex])
        } else {
          self.ancillary.push(self.possibleInputs[widgIndex])
        }
      })
      self.widgs.inputCheckboxes.push(newCheck)
      self.widgs.climChecks.add(newCheck)
      self.ancillary.push(climateList[c])
  }
  
  this.widgs.checks = makePanel(
    'horizontal', 
    [self.widgs.bandChecks, self.widgs.coefChecks])
  this.widgs.ancillaryChecks = makePanel(
    'horizontal',
    [self.widgs.ancChecks, self.widgs.climChecks])
  this.widgs.all = makePanel('vertical', 
    [
      ui.Label('Predictor Variables',visLabels),
      ui.Label('CCDC Model Parameters'),
      self.widgs.checks,
      ui.Label({value:'Ancillary inputs: ', style: {stretch: 'both'}}),
      self.widgs.ancillaryChecks,
    ]
  )
}





exports = {
  getImageRegion: getImageRegion,
  getBounds: getBounds,
  chartCcdc: chartCcdc,
  getTSChart: getTSChart,
  initializeTSViewer: initializeTSViewer,
  generateSelectorPanel: generateSelectorPanel,
  generateColorbarLegend: generateColorbarLegend,
  makePanel: makePanel,
  makeCheckbox: makeCheckbox,
  makeTextPanel: makeTextPanel,
  arrayRemove: arrayRemove,
  predictors: predictors,
  region: region,
  classifier: classifier,
  training: training
}





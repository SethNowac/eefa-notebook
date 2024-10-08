#
# Copyright (c) 2018 Gennadii Donchyts. All rights reserved.

# This work is licensed under the terms of the MIT license.  
# For a copy, see <https://opensource.org/licenses/MIT>.
#
import ee
import geemap

Map = geemap.Map(center=[40, -100], zoom=4)

def draw(text, pos, scale, props):
  text = ee.String(text)
  
  ascii = {}
  for i in range(32, 128):
      ascii[''.join(map(chr, i))] = i
  ascii = ee.Dictionary(ascii)
  
  fontSize = '16'

  if(props and props['fontSize']):
    fontSize = props['fontSize']
  
  fontType = "Arial"
  if(props and props['fontType']):
    fontType = props['fontType']
  
  glyphs = ee.Image('users/gena/fonts/' + fontType + fontSize)

  if(props and props.resample):
    glyphs = glyphs.resample(props.resample)
  
  proj = glyphs.projection()
  s = ee.Number(1).divide(proj.nominalScale())
  
  # HACK: ee.Projection does not provide a way to query xscale, yscale, determing north direction manually
  north = ee.Algorithms.If(proj.transform().index("-1.0").gt(0), 1, -1)

  glyphs = glyphs.changeProj(proj, proj.scale(s, s.multiply(north)))
  
  # get font info
  def func_chw(n): return ee.Number.parse(n, 10)

  font = {
    'height': ee.Number(glyphs.get('height')),
    'width': ee.Number(glyphs.get('width')),
    'cellHeight': ee.Number(glyphs.get('cell_height')),
    'cellWidth': ee.Number(glyphs.get('cell_width')),
    'charWidths': ee.String(glyphs.get('char_widths')).split(',').map(func_chw),
  }
  
  font['columns'] = font['width'].divide(font['cellWidth']).floor()
  font['rows'] = font['height'].divide(font['cellHeight']).floor()
 
  def toAscii(text):
    def func_cpe(char, prev): return ee.List(prev).add(ascii.get(char))
    return ee.List(text.split('') \
      .iterate(func_cpe, ee.List([])))
  
  def moveChar(image, xmin, xmax, ymin, ymax, x, y):
    ll = ee.Image.pixelLonLat()
    nxy = ll.floor().round().changeProj(ll.projection(), image.projection())
    nx = nxy.select(0)
    ny = nxy.select(1)
    mask = nx.gte(xmin).And(nx.lt(xmax)).And(ny.gte(ymin)).And(ny.lt(ymax))
    
    return image.mask(mask).translate(ee.Number(xmin).multiply(-1).add(x), ee.Number(ymin).multiply(-1).subtract(y))

  # TODO: workaround for missing chars
  text = text.replace('á', 'a')
  text = text.replace('é', 'e')
  text = text.replace('ó', 'o')

  codes = toAscii(text)
  
  # compute width for every char
  def func_cod(code): return ee.Number(font['charWidths'].get(ee.Number(code)))

  charWidths = codes.map(func_cod)

  alignX = 0
  alignY = 0
   
  if(props and props.alignX):
    if(props.alignX == 'center'):
      alignX = ee.Number(charWidths.reduce(ee.Reducer.sum())).divide(2) 
    elif(props.alignX == 'left'):
      alignX = 0 
    elif(props.alignX == 'right'):
      alignX = ee.Number(charWidths.reduce(ee.Reducer.sum())) 
    

  if(props and props.alignY):
    if(props.alignY == 'center'):
      alignY = ee.Number(font['cellHeight']).divide(ee.Number(2).multiply(north)) 
    elif(props.alignY == 'top'):
      alignY = 0 
    elif(props.alignY == 'bottom'):
      alignY = ee.Number(font['cellHeight']) 

  # compute xpos for every char
  def func_ite(w, list):
    list = ee.List(list)
    lastX = ee.Number(list.get(-1))
    x = lastX.add(w)
    
    return list.add(x)

  charX = ee.List(charWidths.iterate(func_ite, ee.List([0]))).slice(0, -1)
  
  charPositions = charX.zip(ee.List.sequence(0, charX.size()))
  
  # compute char glyph positions
  def func_gly(code):
    code = ee.Number(code).subtract(32) # subtract start star (32)
    y = code.divide(font.columns).floor().multiply(font['cellHeight'])
    x = code.mod(font.columns).multiply(font['cellWidth'])
    
    return [x, y]

  charGlyphPositions = codes.map(func_gly)
  
  charGlyphInfo = charGlyphPositions.zip(charWidths).zip(charPositions)
  
  pos = ee.Geometry(pos).transform(proj, scale).coordinates()
  xpos = ee.Number(pos.get(0)).subtract(ee.Number(alignX).multiply(scale))
  ypos = ee.Number(pos.get(1)).subtract(ee.Number(alignY).multiply(scale))

  # 'look-up' and draw char glyphs
  # textImage = ee.ImageCollection(charGlyphInfo.map(function(o) {
  #   o = ee.List(o)
    
  #   glyphInfo = ee.List(o.get(0))
  #   gw = ee.Number(glyphInfo.get(1))
  #   glyphPosition = ee.List(glyphInfo.get(0))
  #   gx = ee.Number(glyphPosition.get(0))
  #   gy = ee.Number(glyphPosition.get(1))
    
  #   charPositions = ee.List(o.get(1))
  #   x = ee.Number(charPositions.get(0))
  #   i = ee.Number(charPositions.get(1))
    
  #   glyph = moveChar(glyphs, gx, gx.add(gw), gy, gy.add(font['cellHeight']), x, 0, proj)
  
  #   return glyph.changeProj(proj, proj.translate(xpos, ypos).scale(scale, scale))
  # })).mosaic()

  # textImage = textImage.mask(textImage)

  # >>>>>>>>>>> START WORKAROUND, 29.08.2020
  # EE backend DAG parsing logic has changed, some of map() nesting broke, 
  # ee.Geometry objects can't be used within the map() below, pass them using zip()  
  positions = ee.List.repeat(xpos, charGlyphPositions.size()).zip(ee.List.repeat(ypos, charGlyphPositions.size()))
  charGlyphInfo = charGlyphInfo.zip(positions)

  # 'look-up' and draw char glyphs
  def func_lgo(o1):
    o1 = ee.List(o1)
    
    o = ee.List(o1.get(0))
    
    xy = ee.List(o1.get(1))
    xpos = ee.Number(xy.get(0))
    ypos = ee.Number(xy.get(1))

    glyphInfo = ee.List(o.get(0))
    gw = ee.Number(glyphInfo.get(1))
    glyphPosition = ee.List(glyphInfo.get(0))
    gx = ee.Number(glyphPosition.get(0))
    gy = ee.Number(glyphPosition.get(1))
    
    charPositions = ee.List(o.get(1))
    x = ee.Number(charPositions.get(0))
    i = ee.Number(charPositions.get(1))
    
    glyph = moveChar(glyphs, gx, gx.add(gw), gy, gy.add(font['cellHeight']), x, 0, proj)
  
    return ee.Image(glyph).changeProj(proj, proj.translate(xpos, ypos).scale(scale, scale))

  charImages = ee.List(charGlyphInfo).map(func_lgo)
  
  textImage = ee.ImageCollection(charImages).mosaic()

  textImage = textImage.mask(textImage)
  # <<<<<<<< END WORKAROUND

  if(props):
    props = { 
      'textColor': props['textColor'] or 'ffffff', 
      'outlineColor': props['outlineColor'] or '000000', 
      'outlineWidth': props['outlineWidth'] or 0, 
      'textOpacity': props['textOpacity'] or 0.9,
      'textWidth': props['textWidth'] or 1, 
      'outlineOpacity': props['outlineOpacity'] or 0.4 
    }

    textLine = textImage \
      .visualize({'opacity':props['textOpacity'], 'palette': [props['textColor']], 'forceRgbOutput':True})
      
    if(props['textWidth'] > 1):
      textLine.focal_max(props['textWidth'])

    if(not props or (props and not props['outlineWidth'])):
      return textLine

    textOutline = textImage.focal_max(props['outlineWidth']) \
      .visualize({'opacity':props['outlineOpacity'], 'palette': [props['outlineColor']], 'forceRgbOutput':True})

      
    return ee.ImageCollection.fromImages(ee.List([textOutline, textLine])).mosaic()
  else:
    return textImage


###
 # Annotates image, annotation info should be an array of:
 # 
 # { 
 #    position: 'left' | 'top' | 'right' | 'bottom',
 #    offset: <number>%,
 #    margin: <number>%,
 #    property: <image property name>
 #    format: <property format callback function>
 # }
 #  
 # offset is measured from left (for 'top' | 'bottom') or from top (for 'left' | 'right')
 # 
 # Example:
 # 
 # annotations = [
 #  { 
 #    position: 'left', offset: '10%', margin: '5%',
 #    property: 'system:time_start', 
 #    format: function(o) { return ee.Date(o).format('YYYY-MM-dd') }
 #  },
 #  {
 #    position: 'top', offset: '50%', margin: '5%',
 #    property: 'SUN_AZIMUTH',
 #    format: function(o) { return ee.Number(o).format('%.1f degree') }
 #  }
 # ]
 # 
 # annotate(image, region, annotations)
 # 
 #
def annotateImage(image, vis, bounds, annotations):
  # generate an image for every annotation
  def func_anno(annotation):
    def func_loc(o): return ee.String(o)

    annotation.format = annotation.format or func_loc

    scale = annotation['scale'] or Map.getScale()

    pt = getLocation(bounds, annotation['position'], annotation['offset'], annotation['margin'], scale)
    
    if(annotation['property']):
      str_p = annotation.format(image.get(annotation['property']))
      
      textProperties = { 'fontSize': 14, 'fontType': 'Arial', 'textColor': 'ffffff', 'outlineColor': '000000', 'outlineWidth': 2, 'outlineOpacity': 0.6 }

      # set custom text properties, if any
      textProperties['fontSize'] = annotation['fontSize'] or textProperties['fontSize']
      textProperties['fontType'] = annotation['fontType'] or textProperties['fontType']
      textProperties['textColor'] = annotation['textColor'] or textProperties['textColor']
      textProperties['outlineColor'] = annotation['outlineColor'] or textProperties['outlineColor']
      textProperties['outlineWidth'] = annotation['outlineWidth'] or textProperties['outlineWidth']
      textProperties['outlineOpacity'] = annotation['outlineOpacity'] or textProperties['outlineOpacity']

      return draw(str_p, pt, annotation['scale'] or scale, textProperties)
    
  

  imagesText = annotations.map(func_anno)
  
  images = [image].concat(imagesText)

  if(vis):
      images = [image.visualize(vis)].concat(imagesText)
  
  return ee.ImageCollection.fromImages(images).mosaic()

###
 # Returns size of the geometry bounds
 #
def getSize(g):
  p = g.projection()
  coords = ee.List(ee.Geometry(g).bounds(1).transform(p, p.nominalScale()).coordinates().get(0))
  ll = ee.List(coords.get(0))
  ur = ee.List(coords.get(2))
  ul = ee.List(coords.get(3))
  
  height = ee.Number(ul.get(1)).subtract(ll.get(1))
  width = ee.Number(ur.get(0)).subtract(ul.get(0))

  return { 'width': width, 'height': height }

###
 # Computes a coordinate given positon as a text (left | right | top | bottom) and an offset in px or %
 #
def getLocation(bounds, position, offset, margin, scale):
  coords = ee.List(ee.Geometry(bounds).bounds(scale).coordinates().get(0))
  ll = ee.List(coords.get(0))
  ur = ee.List(coords.get(2))
  ul = ee.List(coords.get(3))
  
  height = ee.Number(ul.get(1)).subtract(ll.get(1))
  width = ee.Number(ur.get(0)).subtract(ul.get(0))

  offsetX = 0
  offsetY = 0
  pt = None

  match(position):
    case 'left':
      pt = ee.Geometry.Point(ul)
      offsetX = offsetToValue(margin, width)
      offsetY = offsetToValue(offset, height).multiply(-1)
    case 'right':
      pt = ee.Geometry.Point(ur)
      offsetX = offsetToValue(margin, width).multiply(-1)
      offsetY = offsetToValue(offset, height).multiply(-1)
    case 'top':
      pt = ee.Geometry.Point(ul)
      offsetX = offsetToValue(offset, width)
      offsetY = offsetToValue(margin, height).multiply(-1)
    case 'bottom':
      pt = ee.Geometry.Point(ll)
      offsetX = offsetToValue(offset, width)
      offsetY = offsetToValue(margin, height)#.multiply(-1)
  

  return translatePoint(pt, offsetX, offsetY)


###
 # Converts <number>px | <number>% to a number value. 
 #
def offsetToValue(offset, range):
  if(offset.match('px$')) :
    return ee.Number.parse(offset[0: offset.length - 2])
  elif(offset.match('%$')):
    offsetPercent = float(offset[0: offset.length - 1])
    return ee.Number.parse(range).multiply(ee.Number(offsetPercent).divide(100))
  else:
    raise 'Unknown value format: ' + offset


def translatePoint(pt, x, y):
  return ee.Geometry.Point(ee.Array(pt.coordinates()).add([x,y]).toList())
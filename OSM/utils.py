import math


def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def topleft2bottomleft(box):
    top_left, bottom_right = box
    bottom_left = bottom_right[0], top_left[1]
    top_right = top_left[0], bottom_right[1]
    return (bottom_left ,top_right)
  
def topleft2orientation(box):
    top_left, bottom_right = box
    south = bottom_right[0]
    west = top_left[1]
    north = top_left[0]
    east = bottom_right[1]
    return south, west, north, east
from shapely.geometry import Polygon
import os
import rasterio
from rasterio.merge import merge

def create_polygon(box):
    """create box polygon for clipping the geopands df
    """
    (max_lat, min_lon), (min_lat, max_lon) = box
    return Polygon([(min_lon, max_lat), 
                    (min_lon, min_lat), 
                    (max_lon, min_lat), 
                    (max_lon, max_lat), 
                    (min_lon, max_lat)])

def rasters_to_mosaic(var, city):
    mosaic_list = []
    num = 1
    path = os.path.join( 'data', var, city+str(num)+'.tif')
    while os.path.exists( path ):
        raster =  rasterio.open( path )
        mosaic_list.append( raster )
        num += 1
        path = os.path.join( 'data', var, city+str(num)+'.tif')
    if num == 1:
        return
    mosaic, output = merge(mosaic_list)
    output_meta = raster.meta.copy()
    output_meta.update(
        {"driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": output,
        }
    )   
    output_path = os.path.join( 'data', var, city+'.tif')
    with rasterio.open(output_path, 'w', **output_meta) as f:
        f.write(mosaic)
    return
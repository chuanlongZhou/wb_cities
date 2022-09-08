import os
import json
import rasterio
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from rasterio.features import shapes
from region_new import Region, vector


def add_polygons(data, city):
    inner_bounds = data.total_bounds
    minx_, miny_, maxx_, maxy_ = inner_bounds
    outer_path = os.path.join("data","microsoft_buildings", city+".json")
    outer_data = gpd.read_file(outer_path)
    outer_bounds = outer_data.total_bounds
    minx, miny, maxx, maxy = outer_bounds
    # We use shapely difference tool to find the ROI
    p_inner = box(minx_, miny_, maxx_, maxy_)
    p_outer = box(minx, miny, maxx, maxy)
    difference = p_outer.difference(p_inner)
    additional_polygons = outer_data[outer_data.geometry.within(difference, align=False)]
    data = pd.concat([data, additional_polygons])
    return data


def add_density(data):
    data['density'] = 1
    return data


def add_area(data):
    data = data.to_crs("EPSG:3395")
    data['area']= data["geometry"].area
    data = data.to_crs("EPSG:4326")
    return data


def raster_to_vector(raster, variable, city, mask=None):
    output_path = os.path.join('data', 'output', 'v3', '')
    to_tif = getattr(raster, variable)
    path = output_path+city+"_"+variable+".tif"
    raster = to_tif.rio.to_raster(path)

    with rasterio.Env():
        with rasterio.open(path) as src:
            image = src.read(1)
            results = (
            {'properties': {variable: v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image.astype('float32'), mask=mask, transform=src.transform)))
    
    vector = gpd.GeoDataFrame.from_features(list(results), crs='EPSG:3395')
    vector = vector.to_crs('epsg:4326')

    return vector

def rasters_to_vectors(city, rasters, resolution):
    bounding_box = json.load(open('bounding_box.json'))
    house = os.path.join("data","microsoft_buildings", city+".json")
  
    box = bounding_box[city]['box']
    name = city
    house = house
   
    lcz_path = os.path.join ('data','lcz','lcz_filter_v1.tif')
    ntl_path = os.path.join ('data','ntl','ntl.tif')
    wsf_path = os.path.join ('data','wsf','')

    region = Region(box)
    house = gpd.read_file(house)
    house['density']=1
    house = house.to_crs("EPSG:3395")
    house['area']= house["geometry"].area
    house = house.to_crs("EPSG:4326")

    region.add_layer(layer_name="MS", 
                geo_data=house, 
                layer_type="vector", 
                meta="MS buildings")

    # add lcz raster layer
    region.add_layer(layer_name="lcz", 
                    geo_data=lcz_path, 
                    layer_type="raster", 
                    box=box, 
                    var_name="lcz", 
                    meta="LCZ categorey label")
    
    # add ntl raster layer
    region.add_layer(layer_name="ntl", 
                geo_data=ntl_path, 
                layer_type="raster", 
                box=box, 
                var_name="ntl", 
                meta="Nighttime Light")

    # add wsf raster layer
    region.add_layer(layer_name="wsf", 
                geo_data=wsf_path+city+'.tif', 
                layer_type="raster", 
                box=box, 
                var_name="wsf", 
                meta="WSF Mask")

    region.add_raster_from_vector(layer_name="MS",
                                    measurements=["area","density"], 
                                    resolution=resolution, 
                                    new_name = "MS_raster",
                                    res_type="meter")
        
    # unify the projection
    region.unify_proj(crs_type="meter")
    
    # merge raster as output xarray
    region.merge_data(base_raster="MS_raster", 
                    raster_list={
                        "lcz":(["lcz"],"nearest"),
                        "ntl":(["ntl"],"linear"),
                        "wsf":(["wsf"],"nearest")
                        }
                    )
    # we compute one vector dataset per raster variable
    raster_vectors = []
    for raster in rasters:
        raster_vectors.append( raster_to_vector(region.output, raster, city) )
    return raster_vectors

def add_feature_from_raster(vector, feature_vector, city):
    if 'index_right' in vector.columns:
        vector.drop('index_right', axis=1, inplace=True)
    vector = vector.sjoin(feature_vector, how='left', predicate='intersects')
    vector = vector[~vector.index.duplicated(keep='first')]
    return vector

def add_rasters(data, rasters, city, resolution=100):
    resolution = (-resolution, resolution)
    raster_vector_list = rasters_to_vectors(city, rasters, resolution)
    for vector in raster_vector_list:
        data = add_feature_from_raster(data, vector, city)
    return data


def add_all_features(data, city, rasters=['ntl', 'lcz', 'wsf']):
    print('adding polygons... ')
    data = add_polygons(data, city)
    print('adding denstity... ')
    data = add_density(data)
    print('adding area... ')
    data = add_area(data)
    print('adding rasters... ')
    data = add_rasters(data, rasters, city)
    data['city'] = city
    return data
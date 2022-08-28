# IMPORTS

from region_new import Region
import geopandas as gpd
import pandas as pd
import numpy as np
import pickle
import os 
import json
import rasterio
from rasterio.features import shapes

''' 
This library contains all necessary functions to fetch 
and add raster data as feature in a dataframe for 
a given city.
Functions are ranked from highest to lowest level.

'''


def prepare_raster_features(cities, variables):
    '''
    Add every variables as features to each city dataframe
    '''
    for city in cities:
        vector = get_vector(city)
        raster = get_raster(city)
        for var in variables:
            vector = add_feature_from_raster(vector, raster, var, city)
        dump_path = os.path.join('data', 'ml', city+'.pkl')
        with open(dump_path,"wb") as f:
            pickle.dump(vector, f, protocol=pickle.HIGHEST_PROTOCOL)

    return


def add_feature_from_raster(vector, raster, variable, city):

    feature_vector = raster_to_vector(raster, variable, city)
    try:
        vector.drop('index_right', inplace=True, axis=1)
        vector.drop(variable, inplace=True, axis=1)
    except:
        print('')
    vector = vector.sjoin(feature_vector, how='left', predicate='within')
    return vector

def get_vector(city):

    city = city+".pkl"
    ml_path = os.path.join('data', 'ml', city)
    with open(ml_path, 'rb') as pickle_file:
        vector = pickle.load(pickle_file)

    return vector


def get_raster(city, resolution=500):

    Cities = dict()
    dump_path = os.path.join("data","Cities_v3_raster.pickle")
    with open(dump_path, 'rb') as f:     
        Cities = pickle.load(f)
    try:
        raster = Cities[city].output
    except KeyError:
        print('City not found, creating rasters...')
        Cities = create_raster(resolution)
        raster = Cities[city].output

    return raster


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


def create_raster(resolution=500):

    # Bounding Box
    bounding_box = json.load(open('../bounding_box.json'))
    # MS Buildings
    johannesburg_house = os.path.join("data","microsoft_buildings","Johannesburg.json")
    cairo_house = os.path.join("data","microsoft_buildings","Cairo.json")
    adana_house = os.path.join("data","microsoft_buildings","Adana.json")
    ordu_house = os.path.join('data', 'microsoft_buildings', 'Ordu.json')
    trabzon_house = os.path.join('data', 'microsoft_buildings', 'Trabzon.json')
    manisa_house = os.path.join('data', 'microsoft_buildings', 'Manisa.json')
    # Raster Dict
    cities = dict(
        Cario = dict(
            bounding_box= bounding_box["Cairo"]["box"],
            name = "Cairo",
            house = cairo_house
        ),
        Johannesburg = dict(
            bounding_box= bounding_box["Johannesburg"]["box"],
            name = "Johannesburg",
            house = johannesburg_house
        ),
        Adana = dict(
            bounding_box= bounding_box["Adana"]["box"],
            name = "Adana",
            house = adana_house
        ),
        Ordu = dict(
            bounding_box= bounding_box["Ordu"]["box"],
            name = "Ordu",
            house = ordu_house,
        ),
        Manisa = dict(
            bounding_box= bounding_box["Manisa"]["box"],
            name = "Manisa",
            house = manisa_house
        ),
        Trabzon = dict(
            bounding_box= bounding_box["Trabzon"]["box"],
            name = "Trabzon",
            house = trabzon_house
        ),
    )

    return  create_regions(cities, resolution)


def create_regions(cities, resolution):

    Cities = dict()
    res = (resolution, 0-resolution)
    lcz_path = os.path.join ('data','lcz','lcz_filter_v1.tif')
    ntl_path = os.path.join ('data','ntl','ntl.tif')

    for index, (key, val) in enumerate(cities.items()):
        print(key)
        box, name, house = val["box"], val["name"],val["house"]
        city = Region(val["box"])
    
        #add MS building
        house = gpd.read_file(house)
        house['density']=1
        house = house.to_crs("EPSG:3395")
        house['area']= house["geometry"].area
        house = house.to_crs("EPSG:4326")

        city.add_layer(layer_name="MS", 
                    geo_data=house, 
                    layer_type="vector", 
                    meta="MS buildings")

        # add lcz raster layer
        city.add_layer(layer_name="lcz", 
                       geo_data=lcz_path, 
                       layer_type="raster", 
                       box=box, 
                       var_name="lcz", 
                       meta="LCZ categorey label")
        
        # add ntl raster layer
        city.add_layer(layer_name="ntl", 
                    geo_data=ntl_path, 
                    layer_type="raster", 
                    box=box, 
                    var_name="ntl", 
                    meta="Nighttime Light")
        
        
        # convert vector to raster
        city.add_raster_from_vector(layer_name="MS", 
                                    measurements=["area","density"], 
                                    resolution=resolution, 
                                    new_name = "MS_raster",
                                    res_type="meter")
        
        # unify the projection
        city.unify_proj(crs_type="meter")
        
        # merge raster as output xarray
        city.merge_data(base_raster="MS_raster", 
                        raster_list={
                            "lcz":(["lcz"],"nearest"),
                            "ntl":(["ntl"],"linear")
                            }
                        )
        Cities[key] = city       

    return Cities               



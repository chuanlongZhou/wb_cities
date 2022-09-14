import os
import json
import rasterio
import geopandas as gpd
import pandas as pd
from shapely.geometry import *
from rasterio.features import shapes
from region_new import Region
import rioxarray
from utils import *

def add_polygons(data, city):
    '''
    Ensures bounding box homogeneity (eg. FUA bounding box)

    :param DataFrame data: Building dataset
    :param string city: city name 
    :return DataFrame: Updated Building dataset
    '''
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
    data['source'] = data['source'].fillna('MS')
    return data


def add_density(data):
    '''
    Ensures density=1 for newly added polygons -- see add_polygons

    :param DataFrame data: Building dataset
    :return DataFrame: Updated Building dataset
    '''
    data['density'] = 1
    return data


def add_area(data):
    '''
    Computes polygon area for newly added polygons

    :param DataFrame data: Building dataset
    :return DataFrame: Updated Building dataset
    '''
    data_to_update = data[data['area'].isna()]
    data_to_update = data_to_update.to_crs("EPSG:3395")
    data_to_update['area']= data_to_update["geometry"].area
    data_to_update = data_to_update.to_crs("EPSG:4326")
    data[data['area'].isna()] = data_to_update
    return data


def raster_to_vector(raster, variable, city):
    '''
    Returns vectorized raster variable 

    :param Xarray Dataset raster: Raster variable
    :param string variable: Variable name
    :param string city: City name
    :return DataFrame: Vectorized raster
    '''
    output_path = os.path.join('data', 'output', 'v3', '')
    # to_tif = getattr(raster, variable)
    path = output_path+city+"_"+variable+".tif"
    raster = raster.rio.to_raster(path)

    with rasterio.Env():
        with rasterio.open(path) as src:
            image = src.read(1)
            results = (
            {'properties': {variable: v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image.astype('float32'), transform=src.transform)))
    
    vector = gpd.GeoDataFrame.from_features(list(results), crs='EPSG:4326')
    # vector = vector.to_crs('epsg:4326')

    return vector



def rasters_to_vectors(city, variables):
    '''
    Returns a list of vectorized rasters 

    :param string city: City name
    :param string list rasters: List of raster variablesm already includes LCZ & VIIRS NTL
    :return DataFrame list: Vectorized rasters
    '''
    vector_list = []
    box = json.load(open('bounding_box.json'))[city]['box']
    [maxy, minx], [miny, maxx] = box

    for variable in variables:
        path_to_raster = os.path.join('data', variable, city+'.tif')
        if variable=="lcz" or variable=="ntl":
            path_to_raster = os.path.join('data', variable, variable+'.tif')
        raster = rioxarray.open_rasterio(path_to_raster).rio.clip_box(minx, miny, maxx, maxy)
        vector_list.append(raster_to_vector(raster, variable, city))
    

    return vector_list,variables

def add_features_from_rasters(arg_tuple):
    '''
    Compute the intersection between building polygons and vectorized rasters to assign 
    the given raster value to each polygon.

    :param DataFrame vector: Building dataset
    :param DataFrame arg_tuple: Raster dataset, raster name
    :return DataFrame: Updated building dataset
    '''
    vector, rvector, name = arg_tuple
    print(name, 'sjoin...')
    vector = vector.sjoin(rvector, how='left', predicate='intersects')
    vector = vector[~vector.index.duplicated(keep='first')]
    col_filter = [col for col in vector if col.startswith('index_right')]
    vector = vector.drop(col_filter, axis=1)
    return vector[[name]]


def add_rasters(data, rasters, city):
    '''
    Assign raster values to each building polygon.

    :param DataFrame data: Building dataset
    :param string List rasters: Raster variables names
    :param string city: City name
    :return DataFrame: Updated Building dataset
    '''

    vectors, names =  rasters_to_vectors( city, rasters )
    points = []
    for p in data.geometry:
        if p.geom_type =='MultiPolygon':
            points.append(Point(p.geoms[0].exterior.coords[0]))
        else:
            points.append(Point(p.exterior.coords[0]))
    data_p = data.set_geometry(points, crs='EPSG:4326')
    vn_list = list( zip( vectors, names ) )
    for v, n in vn_list:
        data = data.join( add_features_from_rasters((data_p, v, n)), how='left' )
        col_filter = [col for col in data if col.startswith('index_right')]
        data = data.drop(col_filter, axis=1)
    # data_list = [data_p for i in range(len(names))]
    # arg_list = list(zip(data_list, vectors, names))
    # results = run_mp(add_features_from_rasters, arg_list)
    # for result in results:
    #     data = data.join(result, how='left')
    #     col_filter = [col for col in data if col.startswith('index_right')]
    #     data = data.drop(col_filter, axis=1)
    for name in names:
        data = data.dropna(subset=[name])
    # Filter with WSF:
    data = data.drop( 
        data[ (data['source']!='OSM') & (data['wsf']==0.0) ].index
    )
    return data


def add_all_features(data, city, rasters=['lcz', 'ntl', 'wsf', 'height_ghsl']):
    '''
    Chain-calls all the updating functions of this package

    :param DataFrame data: Building dataset
    :param string city: city name
    :param list rasters: raster variables to add, defaults to ['wsf']
    :return DataFrame: Updated Building dataset
    '''
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
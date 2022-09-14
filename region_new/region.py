
import geopandas 
import pickle
import shapely
import os
import rasterio
import numpy as np
from region_new.equations import *
from functools import partial
from geocube.api.core import make_geocube
from geocube.rasterize import rasterize_image
from rasterio.enums import MergeAlg
from .vector import Vector
from .raster import Raster


class Region:
    # crs for meter based grid
    crs_meter = "EPSG:3395"
    # crs for degree based grid
    crs_degree = "EPSG:4326"

    def __init__(self, box):
        # set of vector polgon based on data
        # vals: Vector
        self.vector = {}

        # set of raster tiff based on data
        # vals: Raster
        self.raster = {}

        # we'll retrieve the total population 
        self.pop = 0
        # meta data
        self.meta = dict(vector={}, raster={})

        # bounding box for the region
        # (max_lat, min_lon), (min_lat, max_lon) = box
        self.box = box

        # the merged xarray, used as final output
        self.output = None
        self.output_normed = None

    def add_layer(self, layer_name,  geo_data, layer_type="vector", **args):
        if layer_type in ["vector", "v"]:
            self.vector[layer_name] = Vector(geo_data, **args)
            self.meta["vector"][layer_name] = self.vector[layer_name].meta

        elif layer_type in ["raster", "r"]:
            self.raster[layer_name] = Raster(geo_data, **args)
            self.meta["raster"][layer_name] = self.raster[layer_name].meta
            
    def add_raster_from_vector(self, layer_name, measurements, resolution, new_name=None, res_type="degree",**args):
        if res_type in ["meter", "m"]:
            temp_df = self.vector[layer_name].geo_df.to_crs(self.crs_meter)
        else:
            temp_df = self.vector[layer_name].geo_df.to_crs(self.crs_degree)
        
        if new_name is None:
            new_name=layer_name
        
        out_grid = Region.vector2raster(temp_df, measurements, resolution,**args)
        self.add_layer(new_name, layer_type="raster", 
                       geo_data=out_grid, 
                       box = self.vector[layer_name].box,
                       grid_data=True,
                       meta=f"transformed from vector {layer_name}")
    
    def unify_proj(self, crs_type="meter", crs=None):
        if crs is None:
            crs = self.crs_meter if crs_type in ["meter", "m"] else self.crs_degree
        
        for v in self.vector:
            self.vector[v].geo_df = self.vector[v].geo_df.to_crs(crs)
        for r in self.raster:
            self.raster[r].reproject(crs)
    
    def merge_data(self, base_raster, raster_list):
        output = self.raster[base_raster].tiff
        base = self.raster[base_raster].tiff
        var0 = list(base.data_vars)[0]
        base = base[var0] 
        for _, (key, val) in enumerate(raster_list.items()):
            vars, method = val
            for v in vars:
                grid = self.raster[key].interp(like_grid=base, 
                                                    var= v,
                                                    method=method)
                output = output.assign(temp=grid)
                output = output.rename({"temp":v})
        
        self.output = output

    @staticmethod
    def vector2raster(vector_data, measurements, resolution, all_touched=True, alg=MergeAlg.add):
        out_grid = make_geocube(
            vector_data = vector_data,
            measurements = measurements,
            resolution = resolution,
            fill = 0,
            rasterize_function = partial(rasterize_image, 
                                         all_touched=all_touched, 
                                         merge_alg=alg),
        )
        
        return out_grid
    
    

    def normalize_variable(self, variable, output=False, layer=None):
        '''
        Returns variable distribution so that all cell values sum to 1.
        :param string variable: variable to normalize
        :param string layer: layer name, default named as variable
        '''
        if output:
            min = self.output[variable].min()
            total = (self.output[variable] - min).sum()
            self.output[variable] = (self.output[variable] - min) / total
            return
        if layer is None:
            layer=variable
        min = self.raster[layer].tiff[variable].min()
        total = (self.raster[layer].tiff[variable] - min).sum()
        self.output[variable] = (self.raster[layer].tiff[variable] - min) / total


    def difference_map(self, var1, var2):        
        diff = self.output[var1] - self.output[var2]
        return diff.plot(cmap='PiYG', figsize=(10,5))


def get_total_pop(raster_path):
    with rasterio.Env():
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            data = np.where(data == np.nan, 0, data)
            data = np.where(data < 0, 0, data)
            region = np.unique(data)
            counts = [np.count_nonzero(data==region[i]) for i in range(len(region))]
            res = 0
            for i in range(len(region)):
                res += region[i]*counts[i]
            return int(res)


def regions_from_cities(cities, resolution):
    '''
    Generates a set of Regions for each city with a given final resolution for the output.

    :param dict cities: cities (name, box, fua, buildings)
    :param int resolution: meter length of raster cells for the output
    '''
    ntl_path = os.path.join( 'data', 'ntl', 'ntl.tif')
    gpw_path = os.path.join('data', 'gpw', '')
    height_path = os.path.join('data', 'ghsl', 'height', '')
    pop_path = os.path.join('data', 'ghsl', 'pop', '')
     
    resolution=(-resolution, resolution)
    Cities = {}

    for index, (key, val) in enumerate(cities.items()):
        box, fua, name, house = val["box"], val["fua"], val["name"], val["house"]
        city = Region(val["box"])


        # Parse FUA edges from JSON
        fua = shapely.geometry.Polygon(fua)
        fua = geopandas.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[fua])
        # FUA edges
        city.add_layer(layer_name="fua", 
                    geo_data=fua, 
                    layer_type="vector", 
                    box=box, 
                    meta="Functional Urban Area")
        # Census 
        
        
        # MS building|
        with open(house,"rb") as f:
            ms = pickle.load(f)
        city.add_layer(layer_name="MS", 
                    geo_data=ms, 
                    layer_type="vector", 
                    meta="MS buildings")
                    
        # Rasters
        city.add_layer(
                    layer_name="height",
                    geo_data=height_path+name+".tif",
                    layer_type='raster',
                    box=box, 
                    var_name="height", 
                    meta="GHSL BUILT-H")

        city.add_layer(
                    layer_name="ghsl_pop",
                    geo_data=pop_path+name+".tif",
                    layer_type='raster',
                    box=box, 
                    var_name="ghsl_pop", 
                    meta="GHSL POP")
        
        city.add_layer(
            layer_name='ntl',
            geo_data=ntl_path,
            layer_type='raster',
            box=box,
            var_name='ntl',
            meta='VIIRS annual ntl'
        )

        city.pop = get_total_pop(gpw_path+name+'.tif')
        

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
                            "height":(["height"], "linear"),
                            "ntl":(["ntl"], "linear"),
                            "ghsl_pop":(["ghsl_pop"], "linear")
                            }
                        )
        # Compute side variables : population disaggregation, volume, surface
        city.output = city.output.assign(surface= building_surface) 
        city.normalize_variable('surface',output=True)
        city.output = city.output.assign(volume = building_volume)
        city.normalize_variable('volume',output=True)
        city.output = city.output.assign(pop_v = pop_desaggregation_v(city.output, city.pop))
        city.output = city.output.assign(pop_s = pop_desaggregation_s(city.output, city.pop))
        Cities[key] = city      
    return Cities      
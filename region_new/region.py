
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
    def vector2raster(vector_data, measurements, resolution, all_touched=True):
        out_grid = make_geocube(
            vector_data = vector_data,
            measurements = measurements,
            resolution = resolution,
            fill = 0,
            rasterize_function = partial(rasterize_image, 
                                         all_touched=all_touched, 
                                         merge_alg=MergeAlg.add),
        )
        
        return out_grid
    
    
    def normalize_output(self):
        for var in self.output:
            if var == 'emission':
                continue
            maxd = self.output.max()
            mind = self.output.min()
            self.output[var] = (self.output[var] - mind[var]) / (maxd[var] - mind[var])
        
    
    def difference_map(self, var1, var2):        
        diff = self.output[var1] - self.output[var2]
        return diff.plot(cmap='PiYG', figsize=(15,10))
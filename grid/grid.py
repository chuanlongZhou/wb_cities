import geopandas
import contextily as cx
import numpy as np
import os
import pickle
import matplotlib.pyplot as plt
from utils import *
from region import Region
import shapely.geometry
import pandas as pd
import pyproj


class Grid:
    def __init__(self, region, resolution):
        self.region = region
        self.resolution = resolution
        self.cells_df = geopandas.GeoDataFrame()
          
    def create_cells_df(self):
        # Creates a dataframe where each row is a grid cell of the given grid resolution.
        xmax, ymax, xmin, ymin= self.region.box
        transformer = pyproj.Transformer.from_crs("epsg:4326","epsg:3857")
        xmax, ymax = transformer.transform(xmax, ymax)
        xmin, ymin = transformer.transform(xmin, ymin)
        array = []
        x = xmin
        y = ymin
        nb = (ymax-ymin)*(xmax-xmin)//self.resolution
        print('nb cells : ', nb)
        while y <= ymax:
            while x <= xmax:	
                poly = shapely.geometry.Polygon([
                    (x,y), 
                    (x, y+self.resolution), 
                    (x+self.resolution, y+self.resolution), 
                    (x+self.resolution, y)
                ])
                array.append([poly])
                x += self.resolution
            x = xmin
            y += self.resolution
            
        grid = geopandas.GeoDataFrame(array, columns=['geometry']).set_crs('EPSG:3857')
        self.cells_df = grid.to_crs('EPSG:4326')
        self.cells_df["ID"] = np.arange(len(self.cells_df))
        return

    def get_LCZ(self, cell):
        # Returns the mean class of lcz in the corresponding area.
        if self.region.lcz == None:
            raise ValueError("LCZ not defined for the region")
        xmax, ymax, xmin, ymin = cell['geometry'].bounds
        box = (ymin, xmax), (ymax, xmin)
        return self.region.lcz.fetch_LCZ(box)
    
    def set_LCZ(self):
        # Fetch LCZ for all cells in the dataframe
        self.cells_df['lcz'] = self.cells_df.apply(self.get_LCZ, axis=1)
        return
    
    def plot_grid(self):
        ax = self.cells_df.plot(column='lcz', figsize=(15, 10), cmap='OrRd', alpha=0.75)
        cx.add_basemap(ax, source=cx.providers.Stamen.TonerLite, crs=self.cells_df.crs)  


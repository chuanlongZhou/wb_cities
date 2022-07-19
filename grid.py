import geopandas
import contextily as cx
import numpy as np
import os
import pickle
from shapely import geometry, speedups
import matplotlib.pyplot as plt


class Grid:
    def __init__(self, city, total_bounds, resolution, population):
        self.city = city
        self.population = population
        self.building_list = []
        self.buildings = 0
        self.grid = geopandas.GeoDataFrame()
        self.length = resolution
        self.xmin, self.ymin, self.xmax, self.ymax = total_bounds
    
    def saveGrid(self, filename):
        with open(filename, 'wb') as output:
            pickle.dump(self, output)
        return
        
    def loadGrid(self, filename):
        with open(filename, 'rb') as loaded_file:
            loaded_class = pickle.load(loaded_file)
            self.city = loaded_class.city
            self.population = loaded_class.population
            self.grid = loaded_class.grid
            self.length = loaded_class.length
            self.xmin = loaded_class.xmin
            self.ymin = loaded_class.ymin
            self.xmax = loaded_class.xmax
            self.ymax = loaded_class.ymax
        return
        
          
    def createGrid(self):
        x, y = (self.xmin, self.ymin)
        array = []
        while y <= self.ymax:
            while x <= self.xmax:
                poly = geometry.Polygon([
                    (x,y), (x, y+self.length), 
                    (x+self.length, y+self.length), 
                    (x+self.length, y), (x, y)
                ])
                array.append([poly, 0])
                x += self.length
            x = self.xmin
            y += self.length
        grid = geopandas.GeoDataFrame(array, columns=['geometry', 'population']).set_crs('EPSG:3857')
        self.grid = grid.to_crs('EPSG:4326')
        self.grid["ID"] = np.arange(len(self.grid))
        return

            
    def fetchBuildings(self, path):
        return geopandas.read_file(path+self.city+'.json')

    
    def setBuildings(self, path):
        # Set number of building per grid cell
        speedups.enable()
        df = self.fetchBuildings(path)
        self.buildings += df.size
        buildings_in_cells = geopandas.sjoin(df, self.grid, how='inner', predicate='within')
        buildings_in_cells['n_buildings']=1
        buildings_in_cells = buildings_in_cells.groupby('ID').agg({'n_buildings':'sum'})
        self.grid = self.grid.merge(buildings_in_cells, on = 'ID', how = "left")
        self.grid['n_buildings'] = self.grid['n_buildings'].fillna(0)
        return
    
    
    def setPopulationV1(self):
        # Evenly distributes the population on the grid
        self.grid['population'] = self.population / self.grid.size
        return
    
    
    def setPopulationV2(self):
        # Distributes population given the building density
        self.grid['population'] = self.population * self.grid['n_buildings'] / self.buildings
        return
        
        
    def plotPopulation(self):
        # Plots population density for now 
        ax = self.grid.plot(column='population', figsize=(15, 10), cmap='terrain', alpha=0.5, legend=True)
        cx.add_basemap(ax, source=cx.providers.CartoDB.Positron, crs=self.grid.crs)
        

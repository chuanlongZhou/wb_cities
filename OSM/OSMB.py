import requests
import geopandas as gpd
from .utils import *
import numpy as np
from tqdm import tqdm

class OSMB:
    def __init__(self, box):
        # top left and bottom right 
        self.box = box
        # bottom left and top right 
        self.box2 = topleft2bottomleft(box)
        self.z = 15
        
        tile_1 = deg2num(self.box2[0][0],self.box2[0][1], self.z)
        tile_2 = deg2num(self.box2[1][0],self.box2[1][1], self.z)
        
        self.x = np.linspace(tile_1[0], tile_2[0], tile_2[0] - tile_1[0] + 1)
        self.y = np.linspace(tile_2[1], tile_1[1], tile_1[1] - tile_2[1] + 1)
        self.gdf = None
        self.errors = []
        
    
    def get_data(self):
        res =[]
        
        with tqdm(total=(len(self.x))*(len(self.y))) as pbar:
            for x in self.x:
                for y in self.y:
                    temp = OSMB.get_tile_OSMB(int(x), int(y), self.z)
                    if type(temp)==str:
                        self.errors.append((x, y, temp))
                    else:
                        res.extend(temp)
                    pbar.update(1)
        
        self.gdf =  gpd.GeoDataFrame.from_features(res)

    
    @ staticmethod
    def get_tile_OSMB(x, y, z):
        url = f"https://data.osmbuildings.org/0.2/anonymous/tile/{z}/{x}/{y}.json"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code==200:
            data = response.json()
            return data["features"]
        else:
            return f"error {response.status_code}"
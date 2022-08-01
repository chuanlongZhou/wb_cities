from .constant import CATEGORY
from .utils import *
import requests
import json
from tqdm import tqdm

from osmapi import OsmApi
from .constant import OVERPASS_URL
from shapely.geometry import Polygon, Point
import geopandas as gpd


class OSM:
    OMS_category = CATEGORY
    def __init__(self, box):
        # top left and bottom right 
        self.box = box
        # bottom left and top right 
        self.SWNE = topleft2orientation(box)
        self.gdf = None
        
    def get_builidngs(self):
        data = []
        Osm = OsmApi()
        for _, (key, val) in enumerate(self.OMS_category.items()):
            print(f"fetching {key} ...")
            buildings = OSM.query_building(self.SWNE, val)
            print("converting raw data...")
            for b in tqdm(buildings):
                if b["type"]=="way":
                    temp = {}
                    nodes = Osm.NodesGet(b["nodes"])
                    
                    lat_point_list = []
                    lon_point_list = []
                    for _,(_, val) in enumerate(nodes.items()):
                        lat_point_list.append(val["lat"])
                        lon_point_list.append(val["lon"])
                    polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
                    
                    temp["geometry"]=polygon_geom
                    temp["properties"]={
                    "id": b["id"],
                    "type": b["type"],
                    "tags": b["tags"],
                    "category": key
                    }
                    data.append(temp)
                elif b["type"]=="node":
                    temp = {}
                    temp["geometry"] = Point(b["lon"], b["lat"])
                    temp["properties"]={
                    "id": b["id"],
                    "type": b["type"],
                    "category": key
                    }
                    data.append(temp)
        
        self.gdf = gpd.GeoDataFrame.from_features(data, crs='epsg:4326')
             
    @staticmethod
    def query_building(SWNE, builiding_cate):
        overpass_query = f"""
[out:json];
way ["building"~"{builiding_cate}"] {SWNE};
(._;>;);
out;
        """
        return OSM.query_overpass(overpass_query)
    
    
    @staticmethod
    def query_overpass(query):
        response = requests.get(OVERPASS_URL, 
                            params={'data': query})
        try:
            data = response.json()
            data = data['elements']
            return data
        except Exception as e:
            print(e)
            return []
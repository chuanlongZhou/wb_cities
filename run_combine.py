from re import L
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from utils import *

import os
import pickle
import pandas as pd
import geopandas
import numpy as np
import matplotlib.pyplot as plt
import json


import time
from polygon_compare import *


def merge_OSM(tasks, cities):
    for c in cities:
        city_osm = os.path.join("data","OSM",f"{c}_labeled_repaired.pkl")
        df_osm = pickle.load(open(city_osm,"rb"))
        df_osm_b = df_osm[df_osm["type"]=="way"]
        df_osm_b = df_osm_b.to_crs('EPSG:4326')
        
        city_osmb = os.path.join("data","OSMB",f"{c}_labeled_repaired.pkl")
        df_osmb = pickle.load(open(city_osmb,"rb"))
        df_osmb = df_osmb.to_crs('EPSG:4326')
        
        df = geopandas.GeoDataFrame()
        add = []
        
        print(df_osmb.shape)
        
        df_lists = np.array_split(df_osmb, tasks)
        res = run_mp(searh_rows2, df_lists, df2=df_osm_b, added=[])

        for r in res:
            df_temp, add_temp = r
            df = df.append(df_temp)
            add.extend(add_temp)
        
        df_lists = np.array_split(df_osm_b, tasks)
        res = run_mp(searh_rows2, df_lists, df2=df_osmb, added=add)

        for r in res:
            df_temp, add_temp = r
            df = df.append(df_temp)
            add.extend(add_temp)
        
        print(df)
        df = geopandas.GeoDataFrame(df)
        df = df.set_crs('EPSG:4326', allow_override=True)
        
        df.to_pickle(os.path.join("data","OSM_combined",f'{c}_combined_osm.pkl'))
        # df.plot()
        # plt.show()


def merge_MS(tasks, cities, num_cores):

    for c in cities:
        print(c)
        city_osm_combined = os.path.join("data","OSM_combined",f"{c}_combined_osm.pkl")
        city_osm_combined = pickle.load(open(city_osm_combined,"rb"))
        
        city_house = os.path.join("data","clipped_house",f"{c}_labeled.pkl")
        df_ms = pickle.load(open(city_house,"rb"))
        df_ms = df_ms[df_ms["area"]>30]
        df_ms = df_ms.to_crs('EPSG:4326')

        print(city_osm_combined.shape)
        print(df_ms.shape)
        print()

        
        df = geopandas.GeoDataFrame()
        add = []
        
        
        df_lists = np.array_split(city_osm_combined, tasks)

        res = run_mp(searh_rows2, df_lists, df2=df_ms, added=[], num_cores=num_cores)
        
        with open("temp.pkl","wb") as f:
            pickle.dump(res, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        for r in res:
            df_temp, add_temp = r
            df = df.append(df_temp)
            add.extend(add_temp)
        
        df_lists = np.array_split(df_ms, tasks)
        res = run_mp(searh_rows2, df_lists, df2=city_osm_combined, added=add, num_cores=num_cores)

        for r in res:
            df_temp, add_temp = r
            df = df.append(df_temp)
            add.extend(add_temp)
        
        print(df)
        df = geopandas.GeoDataFrame(df)
        df = df.set_crs('EPSG:4326', allow_override=True)
        # df.plot()
        # plt.show()
        print(c)
        df.to_pickle(os.path.join("data","OSM_combined",f'{c}_combined_osm_ms.pkl'))

def cal_label(box, df):
    p, i = box
    index = df.clip(p.buffer(0)).index
    return (i, index)

def add_label(cities):
    bounding_box = json.load(open('bounding_box.json'))
    
    for c in cities:
        print(c)
        box= bounding_box[c]["box"]
        box = create_polygon(box[0],box[1])
        boxes = make_grid(box,0.05)
    
    
        box_list=[]
        for (i, b) in enumerate(boxes):
            box_list.append((b, i))
    
        paths = [
            os.path.join("data","OSM"),
            os.path.join("data","OSMB"),
            os.path.join("data","clipped_house"),
        ]
        for index, path in enumerate(paths):
            df = pickle.load(open(os.path.join(path,f"{c}.pkl"),"rb"))
            
            if index ==0:
                df = df[df["type"]=="way"]
            if index ==2:
                df = df[df["area"]>30]
                
            if df.crs is None:
                df = df.set_crs('EPSG:4326')
            else:
                df = df.to_crs('EPSG:4326')
            
            buffered = df.buffer(0)

            res = run_mp(cal_label, box_list, df=buffered, num_cores=6)

            for r in res:
                i, index = r
                df.loc[index,"box_index"] = i
            
            df = geopandas.GeoDataFrame(df)
            df = df.set_crs('EPSG:4326', allow_override=True)
            
            df.to_pickle(os.path.join(path,f"{c}_labeled.pkl"))




if __name__ == '__main__':
    cities = [
        # 'Ordu',
        # 'Manisa',
        # 'Trabzon',
        # 'Adana',
        # 'Cairo',
        
        'Johannesburg',
    ]
    num_cores=8
    for c in cities:
        # add_label(cities=[c])
        # merge_OSM(tasks=200, cities=[c])
        merge_MS(tasks=200, cities=[c], num_cores=num_cores)
        
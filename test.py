import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from utils import run_mp

import os
import pickle
import pandas as pd
import geopandas
import numpy as np
import matplotlib.pyplot as plt

from polygon_compare import *


def main(tasks):
    cities = [
        # 'Ordu',
        # 'Manisa',
        # 'Adana',
        # 'Cairo',
        # 'Trabzon',
        
        'Johannesburg',
    ]
    for c in cities:
        city_osm = os.path.join("data","OSM",f"{c}.pkl")
        df_osm = pickle.load(open(city_osm,"rb"))
        df_osm_b = df_osm[df_osm["type"]=="way"]
        
        city_osmb = os.path.join("data","OSMB",f"{c}.pkl")
        df_osmb = pickle.load(open(city_osmb,"rb"))
        df_osmb = df_osmb.set_crs('EPSG:4326')
        
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
        df.plot()
        
        df.to_pickle(f'{c}_combined_osm.pkl')
        plt.show()


def main2(tasks):
    cities = [
        # 'Ordu',
        # 'Manisa',
        
        'Trabzon',
        'Adana',
        'Cairo',
        # 'Johannesburg',
    ]
    for c in cities:
        print(c)
        city_osm_combined = os.path.join("data","OSM_combined",f"{c}_combined_osm.pkl")
        city_osm_combined = pickle.load(open(city_osm_combined,"rb"))
        
        city_house = os.path.join("data","clipped_house",f"{c}_house.pkl")
        df_ms = pickle.load(open(city_house,"rb"))
        df_ms = df_ms[df_ms["area"]>30]
        df_ms = df_ms.to_crs('EPSG:4326')

        print(city_osm_combined.shape)
        print(df_ms.shape)
        
        df = geopandas.GeoDataFrame()
        add = []
        
        
        df_lists = np.array_split(city_osm_combined, tasks)
        res = run_mp(searh_rows2, df_lists, df2=df_ms, added=[])

        for r in res:
            df_temp, add_temp = r
            df = df.append(df_temp)
            add.extend(add_temp)
        
        df_lists = np.array_split(df_ms, tasks)
        res = run_mp(searh_rows2, df_lists, df2=city_osm_combined, added=add)

        for r in res:
            df_temp, add_temp = r
            df = df.append(df_temp)
            add.extend(add_temp)
        
        print(df)
        df = geopandas.GeoDataFrame(df)
        df = df.set_crs('EPSG:4326', allow_override=True)
        # df.plot()
        # plt.show()
        
        df.to_pickle(f'{c}_combined_osm_ms.pkl')
    
if __name__ == '__main__':
    main2(tasks=200)
    main(tasks=1000)
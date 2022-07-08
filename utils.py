import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import concurrent.futures
import multiprocessing as mp
from tqdm import tqdm
import geopandas as gpd
from shapely.geometry import Polygon



def plot_map_annote(c, col):
    c['coords'] = c['geometry'].apply(lambda x: x.representative_point().coords[:])
    c['coords'] = [coords[0] for coords in c['coords']]

    c.plot()
    for idx, row in c.iterrows():
        plt.annotate(row[col], xy=row['coords'],
                    horizontalalignment='center')
        

def run_mp(map_func, arg_list, combine_func=None, num_cores=None):
    if num_cores is None:
        num_cores = mp.cpu_count()
        num_cores = len(arg_list) if len(arg_list)<num_cores else num_cores
    print(f"Using {num_cores} threads...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as pool:
        with tqdm(total=len(arg_list)) as progress:
            futures = []
            for args in arg_list:
                future = pool.submit(map_func, args)
                future.add_done_callback(lambda p: progress.update())
                futures.append(future)

            results = []
            
            for future in futures:
                result = future.result()
                results.append(result)
    
    if combine_func is not None:
        return combine_func(results)
    else:
        return results   
    

def create_polygon(top, bottom):
    top_lat, top_lon = top
    bottom_lat, bottom_lon = bottom
    return Polygon([(top_lon, top_lat), (top_lon, bottom_lat), (bottom_lon, bottom_lat), (bottom_lon, top_lat), (top_lon, top_lat)])
    

def clip_func(house, region):
    return house.buffer(0).clip(region)

def parallelize(df, func, args, cups=-1):
    if cups == -1:
        cpus = mp.cpu_count()
    
    intersection_chunks = np.array_split(df, 200)
    
    pool = mp.Pool(processes=cpus)
    
    chunk_processes = [pool.apply_async(func, args=(chunk, args)) for chunk in intersection_chunks]
    
    intersection_results = [chunk.get() for chunk in chunk_processes]
    
    intersections_dist = gpd.GeoDataFrame(pd.concat(intersection_results), crs=df.crs)

    return intersections_dist
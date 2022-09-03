import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import concurrent.futures
import multiprocessing as mp
import geopandas as gpd
from shapely.geometry import Polygon
from tqdm import tqdm

import numpy as np
import numpy.linalg as LA

from create_polygon import Create_random_polygon
    
# def select_group_value(df, group, ):
#     tk_cen.groupby(["region","city"], sort=False)['year'].max().reset_index().merge(tk_cen, on=["region","city","year"])


def make_grid(polygon, edge_size):
    """
    polygon : shapely.geometry
    edge_size : length of the grid cell
    """
    from itertools import product
    import numpy as np
    import geopandas as gpd
    
    bounds = polygon.bounds    
    x_coords = np.arange(bounds[0] + edge_size/2, bounds[2], edge_size)
    y_coords = np.arange(bounds[1] + edge_size/2, bounds[3], edge_size)
    combinations = np.array(list(product(x_coords, y_coords)))
    
    squares = gpd.points_from_xy(combinations[:, 0], combinations[:, 1]).buffer(edge_size / 2, cap_style=3)
    return gpd.GeoSeries(squares[squares.intersects(polygon)])



def plot_map_annote(df, col):
    df.plot(figsize=(20,18))
    df["center"]= df.centroid
    for idx, row in df.iterrows():
        plt.annotate(row[col], xy=(row['center'].x, row['center'].y),
                    horizontalalignment='center')
        

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        

def run_mp(map_func, arg_list, combine_func=None, num_cores=-1, split_arg=-1, **kwargs):
    if num_cores==-1:
        num_cores = mp.cpu_count()
        num_cores = len(arg_list) if len(arg_list)<num_cores else num_cores
   
    if split_arg!=-1:
       arg_list = list(chunks(arg_list, split_arg))
   
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as pool:
        with tqdm(total=len(arg_list)) as progress:
            futures = []
            
            for args in arg_list:
                # the arg list need to be created if there are more than one arguments
                future = pool.submit(map_func, args, **kwargs)
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

def create_polygon_from_bounds(bounds):
    """create box polygon for clipping the geopands df
    """
    left, bottom, right, top = bounds
    return Polygon([(left, top), 
                    (left, bottom), 
                    (right, bottom), 
                    (right, top), 
                    (left, top)])
    
    
def reorder_points(p):
    coords = list(p.exterior.coords)
    res = [coords[0]]
    added = [0]
    curr = coords[0]
    
    while len(added)<len(coords):
        minV, minI = np.inf, -1
        for i, c in enumerate(coords):
            if i not in added:
                d = (curr[0]-c[0])**2 + (curr[1]-c[1])**2
                if d<minV:
                    minV, minI = d, i
            
        res.append(coords[minI])
        added.append(minI)
        curr = coords[minI]

    if Polygon(res).is_valid:
        return Polygon(res)
    else:
        maxx, maxy = -np.inf, -np.inf    
        minx, miny = np.inf, np.inf
        
        
        for c in coords:
            if c[0]>maxx:
                maxx = c[0]
            if c[0]<minx:
                minx = c[0]
            if c[1]>maxy:
                maxy = c[1]
            if c[1]<miny:
                miny = c[1]
                
        return create_polygon_from_bounds([minx, miny, maxx, maxy])
    
def is_convex(coords):
    total = 0
    
    
    
    if total==360:
        return True
    else:
        return False


def cal_angle(a, b):
    inner = np.inner(a, b)
    norms = LA.norm(a) * LA.norm(b)
    cos = inner / norms
    rad = np.arccos(np.clip(cos, -1.0, 1.0))
    deg = np.rad2deg(rad)
    return deg

    
def reorder_points_90(p):
    coords = list(set(list(p.exterior.coords)))
    # coords = list(p.exterior.coords)
    # print(len(coords))
    
    best_angle= np.inf
    best_res =None
    for index in range(len(coords)):
        curr_angle = 0
        res = [coords[index]]
        added = [index]
        
        # find the closest point
        curr = coords[index]
        minV, minI = np.inf, -1
        for i, c in enumerate(coords):
            if i not in added:
                d = (curr[0]-c[0])**2 + (curr[1]-c[1])**2
                if d<minV and d!=0:
                    minV, minI = d, i
        res.append(coords[minI])
        added.append(minI)
        
        prve_p = coords[index]
        curr_p = coords[minI]
        curr_v = np.array([curr_p[0]-prve_p[0], curr_p[1]-prve_p[1]])
        
        while len(added)<len(coords):
            minV, minI, next_p = np.inf, -1, None
            for i, c in enumerate(coords):
                if i not in added:
                    next_p = c
                    next_v = np.array([next_p[0]-curr_p[0], next_p[1]-curr_p[1]])
                    
                    # print(curr_v, next_v)
                    angle = cal_angle(curr_v, next_v)
                    if np.isnan(angle):
                        angle=0
                    if abs(angle-90)<minV:
                        minV, minI = abs(angle-90), i
            res.append(coords[minI])
            added.append(minI)
            # print(minI, minV, len(added), len(coords))
            next_p = coords[minI]
            curr_v = np.array([next_p[0]-curr_p[0], next_p[1]-curr_p[1]])
            curr_p = coords[minI]
            curr_angle+=minV

        
        if curr_angle<best_angle:
            best_res = res
            best_angle = curr_angle

    # print(best_res)
    convert_type = "90_degree"
    if not Polygon(best_res).is_valid:
        # temp = Create_random_polygon(array=coords)
        # best_res = temp.main()
        best_res = p.exterior.convex_hull
        convert_type = "convex_hull"
        
    return Polygon(best_res), convert_type

        
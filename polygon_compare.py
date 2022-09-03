import pickle
import pandas as pd
import geopandas
from tqdm import tqdm
import os

from functools import wraps
import time

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


def union_rows(row, jrows):
    # union overlapped polygon rows
        
    df = pd.DataFrame()
    polgyon = None
    if row["geometry"] is not None:
        polgyon = row["geometry"]
        
    if "polygon_type" in row:
        polygon_type = row["polygon_type"]
        if  pd.isna(polygon_type):
            polygon_type = ""
    else:
        polygon_type=""
        
    for r in jrows:
        if r["geometry"] is not None:
            if polgyon is None:
                polgyon = row["geometry"].buffer(0).union(r["geometry"].buffer(0))
            else:
                polgyon = polgyon.buffer(0).union(r["geometry"].buffer(0))
            
        if "polygon_type" in r:
            if not pd.isna(r["polygon_type"]):
                polygon_type = polygon_type+","+r["polygon_type"]
        
        df = df.append(r)
        
    row["geometry"] = polgyon
    row["polygon_type"] = polygon_type
    df = df.append(row)
    df = df.fillna(method='ffill')
    df = df.iloc[-1:]
    df =  geopandas.GeoDataFrame(df)
    
    return df

def compare_geodf(df1, df2, match_one):
    df, added = searh_rows(df1, df2, [], match_one=match_one)
    df, _ = searh_rows(df2, df1, added, df=df, match_one=match_one)
    
    return df

def compare_geodf2(df1, df2, match_one):
    df, added = searh_rows2(df1, df2, [], match_one=match_one)
    df, _ = searh_rows2(df2, df1, added, df=df, match_one=match_one)
    
    return df

def check_bbox(p1, p2):    
    # check whether the bounding boxes are overlapped
    minx1,  miny1,  maxx1,  maxy1 = p1.bounds
    minx2,  miny2,  maxx2,  maxy2 = p2.bounds

    x_left = max(minx1, minx2)
    x_right = min(maxx1, maxx2)
    
    y_bottom = max(miny1, miny2)
    y_top = min(maxy1, maxy2)
    
    # print(x_left, x_right)
    # print(y_bottom, y_top)
    
    if x_right < x_left or y_top < y_bottom:
        return False
    else:
        return True

def cal_overlap(p1, p2):
    area = p1.buffer(0).intersection(p2.buffer(0)).area
    return area

def searh_rows(df1, df2, added, crs='EPSG:4326', overlap_threshold = 0.3, df=None, match_one=True):
    if df is None:
        df = geopandas.GeoDataFrame()
    
    with tqdm(total=len(df1)) as pbar:
        
        for index, row in tqdm(df1.iterrows()):
            if index not in added:
                over_row = []
                over_index = []
                for jindex, jrow in df2.iterrows():
                    # if the polgyon is not added

                    if jindex not in added:
                        if check_bbox(row["geometry"], jrow["geometry"]):
                            overlapped_area = cal_overlap(row["geometry"], jrow["geometry"])
                            if jrow["geometry"].area>0:
                                # if the overlapped ratio is larger than threshold
                                if overlapped_area/jrow["geometry"].area > overlap_threshold:
                                    over_row.append(jrow)
                                    over_index.append(jindex)
                                    
                                    # one polgyon can only overlaps one polgyon
                                    if match_one:
                                        break
                
                if len(over_row)==0:
                    df = df.append(row)
                else:
                    temp = union_rows(row, over_row)
                    df = df.append(temp)
                    if len(over_index)>1:
                        print(over_index)
                    added.extend(over_index)
                added.append(index)
                
            pbar.update(1)
            
            if index>200:
                break   
            # break   
            
    df = geopandas.GeoDataFrame(df)
    df.set_crs(crs, allow_override=True)
    
    return df, added


def searh_rows2(df1, df2, added, crs='EPSG:4326', overlap_threshold = 0.3, df=None, match_one=True):
    df2_buffer = df2.buffer(0)
    
    path = os.path.join("data", "temp", f"{df1.index[0]}_{df1.index[-1]}.pkl")
    if os.path.exists(path):
        data = pickle.load(open(path,"rb"))
        df, added = data
        return df, added
    
    if df is None:
        df = geopandas.GeoDataFrame()
    
    with tqdm(total=len(df1)) as pbar:
        
        for index, row in tqdm(df1.iterrows()):
            if index not in added and row["geometry"] is not None:
                lable_df = df2_buffer.loc[df2["box_index"]==row["box_index"]]
                over_row_rough = geopandas.clip(lable_df, row["geometry"].buffer(0))
                
                if len(over_row_rough)==0:
                    df = df.append(row)
                else:
                    over_row = []
                    over_index = []
                    for jindex, jrow in df2.loc[over_row_rough.index].iterrows():
                        overlapped_area = cal_overlap(row["geometry"], jrow["geometry"])
                        if jrow["geometry"].area>0:
                            if overlapped_area/jrow["geometry"].area > overlap_threshold:
                                over_row.append(jrow)
                                over_index.append(jindex)
                            
                    temp = union_rows(row, over_row)
                    df = df.append(temp)
                    # if len(over_index)>1:
                    #     print(over_index)
                    added.extend(over_index)
                    
                added.append(index)
                    
                pbar.update(1)
            
            # if index>200:
            #     break   
            # break   
            
    df = geopandas.GeoDataFrame(df)
    if len(df)>0:
        df = df.set_crs(crs, allow_override=True)
    
    with open(path,"wb") as f:
        pickle.dump((df, added), f, protocol=pickle.HIGHEST_PROTOCOL)
    
    return df, added



def searh_rows3(df1, df2, added, crs='EPSG:4326', overlap_threshold = 0.3, df=None):
    df2_buffer = df2.buffer(0)
    
    if df is None:
        df = geopandas.GeoDataFrame()
    
        
    for index, row in tqdm(df1.iterrows()):
        if index not in added:
            over_row_rough = geopandas.clip(df2_buffer, row["geometry"].buffer(0))
            
            if len(over_row_rough)==0:
                df = df.append(row)
            else:
                over_row = []
                over_index = []
                for jindex, jrow in df2.loc[over_row_rough.index].iterrows():
                    overlapped_area = cal_overlap(row["geometry"], jrow["geometry"])
                    if jrow["geometry"].area>0:
                        if overlapped_area/jrow["geometry"].area > overlap_threshold:
                            over_row.append(jrow)
                            over_index.append(jindex)
                        
                temp = union_rows(row, over_row)
                df = df.append(temp)
                added.extend(over_index)
                
            added.append(index)
                

            
    df = geopandas.GeoDataFrame(df)
    df = df.set_crs(crs, allow_override=True)
    
    return df, added
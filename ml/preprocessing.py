import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.impute import SimpleImputer
import geopandas as gpd


def merge_cities(dataframesList):
    df = dataframesList[0]
    for df_next in dataframesList[1:]:
        df = df.append(df_next)
    return df
    # return gpd.GeoDataFrame(pd.concat(dataframesList, ignore_index=True), crs=dataframesList[0].crs)


def split( data ):
        data_train = data.dropna(subset='height')
        data_test = pd.concat(
                [data, data_train]
                ).drop_duplicates(keep=False)
        return data_train, data_test


def training_split(data, variable):
    y = data[variable]
    X = data.drop(variable, axis=1) 
    return X, y

def columns_selectors(data):
    numerical_features = ['ntl', 'area']
    categorical_features = make_column_selector(dtype_include = object)
    discrete_features = ['lcz', 'wsf', 'index_right'] 
    return numerical_features, categorical_features, discrete_features

def sub_pipelines(data):
    
    numerical_pipeline = make_pipeline(
        SimpleImputer( strategy='mean'),
        StandardScaler(),
    )
    categorical_pipeline = make_pipeline(
        SimpleImputer( strategy='most_frequent'),
        OneHotEncoder()
    )
    discrete_pipeline = make_pipeline(
        SimpleImputer( strategy='most_frequent'),
        StandardScaler(),
    )
    return numerical_pipeline, categorical_pipeline, discrete_pipeline

def preprocesor(data):

    numerical_features, categorical_features, discrete_features = columns_selectors(data)
    numerical_pipeline, categorical_pipeline, discrete_pipeline = sub_pipelines(data)
    
    preprocessor = make_column_transformer( 
        (numerical_pipeline, numerical_features),
        (categorical_pipeline, categorical_features),
        (discrete_pipeline, discrete_features)
    )

    return preprocessor


def clean_columns(data):
    data.drop(['geometry', 'source', 'orient','type_level_0', 'type_level_1'], axis=1, inplace=True)
    dup_2 = {
        'no tag': 'others',
    }
    data['type_level_2'] = data['type_level_2'].replace(dup_2)
    return data
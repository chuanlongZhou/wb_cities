import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.impute import SimpleImputer


def merge_cities(dataframesList):
    '''
    Concatenates rows of several DataFrames

    :param List dataframesList: List of DataFrames
    :return DataFrame: Merged DataFrame
    '''
    df = dataframesList[0]
    for df_next in dataframesList[1:]:
        df = df.append(df_next)
    return df


def split( data, variable ):
    '''
    Splits a DataFrame in two, given a variable with values or NaN-values

    :param DataFrame data: 
    :param String variable: Column to split from
    :return DataFrame Tuple: Two Dataframes, the first one contains no NaN value on the column 'variable'
    '''
    data_train = data.dropna(subset=variable)
    data_test = pd.concat(
            [data, data_train]
            ).drop_duplicates(keep=False)
    return  data_train, data_test



def training_split(data, variable):
    '''
    Returns the tuple X,y ready to be fed into a pipeline

    :param DataFrame data: 
    :param String variable: The y variable
    :return DataFrame, Series tuple: X, y
    '''
    y = data[variable]
    X = data.drop(variable, axis=1) 
    return X, y

def columns_selectors():
    '''
    Creates the column_selectors to handle preprocessing given each variable type

    :return column_selector tuple: 
    '''
    numerical_features = make_column_selector(dtype_include = np.number)
    categorical_features = make_column_selector(dtype_include = object)
    return numerical_features, categorical_features

def sub_pipelines():
    '''
    Creates the sub-pipeline to scale or encode each variable.

    :return pipeline tuple:
    '''
    numerical_pipeline = make_pipeline(
        SimpleImputer( strategy='mean'),
        StandardScaler(),
    )
    categorical_pipeline = make_pipeline(
        SimpleImputer( strategy='most_frequent'),
        OneHotEncoder()
    )

    return numerical_pipeline, categorical_pipeline

def preprocesor():
    '''
    Creates the complete preprocessing steps for ML pipeline - eg. column_selectors, sub_pipelines and calls a column_transformer

    :return column_transformer: complete preprocessing steps
    '''
    numerical_features, categorical_features = columns_selectors()
    numerical_pipeline, categorical_pipeline= sub_pipelines()
    
    preprocessor = make_column_transformer( 
        (numerical_pipeline, numerical_features),
        (categorical_pipeline, categorical_features)
    )

    return preprocessor


def format_type(data):
    '''
    Binarizes the 'Residential' building type. 

    :param DataFrame data: 
    :return DataFrame: 'residential' variable is now boolean.
    '''
    data['type_level_2'] = data['type_level_2'].replace({'no tag': np.nan})
    data_formatted = pd.get_dummies(data, columns=['type_level_2'])
    data_formatted.loc[data.type_level_2.isnull(), data_formatted.columns.str.startswith("type_level_2_")] = np.nan
    data_formatted = data_formatted.drop(['type_level_2_industrial' , 'type_level_2_others'], axis=1)
    data_formatted.columns = data_formatted.columns.str.replace('type_level_2_', '')
    return data_formatted


def clean_columns(data):
    '''
    Removes useless columns in respect to the ML pipeline (eg. 'geometry, etc.)

    :param DataFrame data: 
    :return DataFrame: Truncated DataFrame to meaningful variables only
    '''
    data.drop(['geometry', 'source', 'orient','type_level_0', 'type_level_1'], axis=1, inplace=True)
    return data
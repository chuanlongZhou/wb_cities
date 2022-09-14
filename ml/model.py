from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from imblearn.ensemble import BalancedRandomForestClassifier, BalancedBaggingClassifier
from sklearn.metrics import *
from sklearn.base import is_classifier
import pandas as pd
import os
from region_new import Region

# List of possible estimators
estimators = [
    KNeighborsClassifier(),
    RandomForestClassifier(),
    BalancedRandomForestClassifier(),
    BalancedBaggingClassifier()
]

# Dictionary of corresponding estimator parameters for GridSearchCV
grid_params = {
    0: {
        'estimator__n_neighbors': [2,5,8],
        'estimator__weights': ['uniform', 'distance'],
    },
    1: {
        'estimator__n_estimators': [10,100,1000],
        'estimator__criterion': ['gini', 'entropy', 'log_loss']
    },
    2: {
        'estimator__n_estimators': [10,100,1000]
    },
    3: {
        'estimator__base_estimator': [None, KNeighborsClassifier()]
    }
}


def select_best_estimator(X, y, preprocessor, estimators=estimators):
    '''
    Compares estimators for a given task using multiple GridSearchCV

    :param DataFrame X: Features
    :param Series y: Variable to predict
    :param column_transformer preprocessor: Complete preprocessing steps
    :param estimator estimators: List of estimators to compare, defaults to estimators
    :return estimator: Best performing estimator
    '''
    if type(y[0]) == str:
        y = pd.get_dummies(y, drop_first=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=42)
    print(X_train.shape, y_train.shape)
    best_grid = None
    best_score = 0.0   
    for i in range(len(estimators)):
        print(estimators[i])
        pipeline = Pipeline( 
            [
                ("preprocessor", preprocessor),
                ("estimator", estimators[i])
            ]
        )
        grid = GridSearchCV(
            pipeline,
            param_grid = grid_params[i],
        )
        grid.fit(X_train, y_train)
        if is_classifier(estimators[i]):
            cm = ConfusionMatrixDisplay.from_estimator(grid, X_test, y_test)
        else: 
            print(mean_squared_error(y_test, grid.predict(X_test)))
        print("f1 score : ", f1_score(y_test, grid.predict(X_test)))
        if grid.best_score_ > best_score:
            best_score = grid.best_score_
            best_grid = grid
        print('Score : ', grid.best_score_)
    
    return best_grid.best_estimator_


def predict(model, variable, train_set, pred_set, saved_set):
    '''
    Return the prediction for the testing set

    :param estimator model: Best performing estimator
    :param string variable: Varianle to predict
    :param DataFrame train_set: Training set
    :param DataFrame pred_set: Testing set
    :param DataFrame saved_set: Complete set
    :return DataFrame: Complete set with predicted values for a given variable
    '''
    pred_set[variable+'_pred'] = model.predict(pred_set)
    train_set[variable+'_pred'] = train_set[variable]
    result = pd.concat([train_set, pred_set])
    saved_set = saved_set.merge(result[variable+'_pred'], how='inner', left_index=True, right_index=True )
    saved_set = saved_set.to_crs('EPSG:3395')
    saved_set = saved_set.loc[:, ['city', 'geometry', 'area', 'density', 'height', variable+'_pred']]
    return saved_set 


def breakdown_cities(data):
    '''
    Splits DataFrame in one for each city it contains

    :param DataFrame data: 
    :return DataFrame List: One DataFrame for each city value
    '''
    citiesList = list(data.city.unique())
    dataframesList = []
    for city in citiesList:
        dataframesList.append( data[ data.city == city ] )  
    return dataframesList


def prediction_to_raster(data, variable):
    '''
    Returns rasterized Xarray from vectorized DataFrame

    :param DataFrame data: 
    :param string variable: predicted variable
    :return Xarray DataSet: Rasterized predicted variable
    '''
    raster = Region.vector2raster(data, ['height', 'density', 'area', variable], resolution=(-100,100))
    raster[variable] /= raster['density']
    raster = raster.fillna(0)
    return raster


def write_result(raster, variable, name):
    '''
    Writes rasterized prediction to disk

    :param Xarray DataSet raster: Rasterized prediction
    :param string variable: Predicted variable
    :param string name: City name as file name
    '''
    w_path = os.path.join('data', 'ml', 'prediction', variable, name+'.tif')
    raster[variable+'_pred'].rio.to_raster(w_path)
    return

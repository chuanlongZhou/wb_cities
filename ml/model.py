from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import *
import pandas as pd
import os
from region_new import Region


classifiers = [
    RandomForestClassifier(random_state=42),
    SVC(probability=True, random_state=42),
    LogisticRegression(random_state=42),
    DecisionTreeClassifier(random_state=42),
    KNeighborsClassifier(),
]


grid_params = {
    0 : { 
        'classifier__n_estimators': [200, 300],
        'classifier__max_features': ['sqrt', 'log2'],
        'classifier__max_depth' : [4,5,6,7,8],
        'classifier__criterion' :['gini', 'entropy'],
    },     
    1 : {
        'classifier__kernel': ['linear', 'poly', 'rbf'],
        'classifier__degree': [2, 3, 4],
    },
    2 : {
        'classifier__penalty': ['l1', 'l2', 'elasticnet'],
        'classifier__C': [0.1, 1.0, 10, 100]
    },
    3: {
        'classifier__criterion': ['gini', 'entropy', 'log_loss'],
        'classifier__max_depth' : [4,5,6,7,8],
        'classifier__max_features': ['sqrt', 'log2'],
    },
    4: {
        'classifier__n_neighbors': [2,5,8],
        'classifier__weights': ['uniform', 'distance'],
    },
}


def select_best_estimator(X, y, preprocessor, classifiers=classifiers):

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(X_train.shape, y_train.shape)
    best_grid = None
    best_score = 0.0   
    for i in range(len(classifiers)):
        pipeline = Pipeline( 
            [
                ("preprocessor", preprocessor),
                ("classifier", classifiers[i])
            ]
        )
        grid = GridSearchCV(
            pipeline,
            param_grid = grid_params[i],
        )
        grid.fit(X_train, y_train)
        print(classifiers[i])
        cm = ConfusionMatrixDisplay.from_estimator(grid, X_test, y_test)
        if grid.best_score_ > best_score:
            best_score = grid.best_score_
            best_grid = grid
        print('Current Best Score : ', best_score)
    
    return best_grid.best_estimator_


def predict(model, variable, train_set, pred_set, saved_set):
    pred_set[variable+'_pred'] = model.predict(pred_set)
    train_set[variable+'_pred'] = train_set[variable]
    result = pd.concat([train_set, pred_set])
    saved_set = saved_set.merge(result[variable+'_pred'], how='inner', left_index=True, right_index=True )
    saved_set = saved_set.to_crs('EPSG:3395')
    saved_set = saved_set.loc[:, ['city', 'geometry', 'area', 'density', 'height', variable+'_pred']]
    return saved_set 


def breakdown_cities(data):
    citiesList = list(data.city.unique())
    dataframesList = []
    for city in citiesList:
        dataframesList.append( data[ data.city == city ] )  
    return dataframesList


def prediction_to_raster(data, variable):
    raster = Region.vector2raster(data, ['height', 'density', 'area', variable], resolution=(-100,100))
    raster[variable] /= raster['density']
    raster = raster.fillna(0)
    return raster


def write_result(raster, variable, name):
    w_path = os.path.join('data', 'ml', 'prediction', variable, name+'.tif')
    raster[variable+'_pred'].rio.to_raster(w_path)
    return

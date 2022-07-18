import geopandas as gpd
import pandas as pd
import os 
import argparse
import requests
import zipfile  
from io import BytesIO
import shapely.speedups
from shapely.geometry import Point, Polygon, box    
    

# Global variables 
# Bounding Box dictionary : city : xmin, ymin, xmax, ymax
bounding_boxes ={
        'Cairo' : [
            30.8329690129,
            29.7593128571,
            31.8217385441,
            30.4175936744
            ],
        'Adana' : [
            35.2181632405,
            36.9487243006,
            35.4104239827,
            37.0682576306
            ],
        'Johannesburg' : [
            27.7076346761,
            -26.5428853333,
            28.5686881429,
            -25.600467535
            ]
        } 

# The URL might need to be updated
URL = "https://minedbuildings.blob.core.windows.net/global-buildings/2022-05-02/"
noDL = False

def isInCity(x, y, xmin, ymin, xmax, ymax):
    """Bool. Returns True if the point x,y is in the city area."""
    return x>=xmin and x<=xmax and y>=ymin and y<=ymax 

def swapSpaceUnderscore(string):
    return string.replace("_", " ")

def removeSpace(string):
    return string.replace(" ", "")

def createDir(country):
    path = "./"+removeSpace(country)
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)
    return 


def requestCountryFile(country):
    filename = country+".zip"
    fullURL = URL+filename
    print(fullURL)
    req = requests.get(fullURL)
    file=zipfile.ZipFile(BytesIO(req.content))
    file.extractall('./'+removeSpace(country))
    return


def splitCountryFile(country):
    """Splits the GeoJSONL file into smaller chunks of data to 
       avoid memory overflow."""
    filename = country+"/"+country
    value = os.system("split -l 100000 "+filename+".geojsonl "+filename+"_ --additional-suffix=.geojsonl")
    value = os.system("rm "+filename+".geojsonl") 
    return value


def filterSubfiles(country, xmin, ymin, xmax, ymax):
    """Filters all split subfiles given four coordinates of a bounding box"""
    shapely.speedups.enable()
    bounding_box = Polygon([(xmin,ymin), (xmin, ymax), (xmax, ymax), (xmax,ymin)])
    gdf_filtered = gpd.GeoDataFrame()
    cpt = 0
    total = len([filename for filename in os.scandir(country)])
    for filename in os.scandir(country):
        print("Files processed :", cpt, "/", total)
        cpt+=1
        gdf = gpd.read_file(filename.path)
        gdf = gdf[gdf.geometry.within(bounding_box, align=False)]
        gdf_filtered = gpd.GeoDataFrame( pd.concat( [gdf_filtered, gdf], ignore_index=True) )
    return gdf_filtered


def writeCityFile(cityGdf, city):
    cityGdf.to_file(city+".json", driver="GeoJSON")
    return


def main():
    description = "This script downloads all buildings from the Microsoft building database and outputs a GeoJSON containing only those in a bounding box whose coordinates need to be specified by the user."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('country', type=str, help='The country name')
    parser.add_argument('city', type=str, help='The city name, name of the ouput file')
    parser.add_argument('--no_dl', default=False, action='store_true', help='An optional argument, avoid downloading the country file.')
    
    args = parser.parse_args()
    country = swapSpaceUnderscore(args.country)
    city = swapSpaceUnderscore(args.city)
    xmin = bounding_boxes[city][0]
    ymin = bounding_boxes[city][1]
    xmax = bounding_boxes[city][2]
    ymax = bounding_boxes[city][3]
    noDL = args.no_dl 

    print("Country=",country)
    print("City=",city)
    print("BB coordinates=",xmin, ymin, xmax, ymax)
    if not noDL:
        createDir(country)
        requestCountryFile(country)
        print("File Downloaded")
        country = removeSpace(country)
        splitCountryFile(country)
    country = removeSpace(country)
    result = filterSubfiles(country, xmin, ymin, xmax, ymax)
    writeCityFile(result, city)
    return


main()

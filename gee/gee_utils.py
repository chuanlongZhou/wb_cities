import numpy
import requests
import io
import urllib.request 
import os
import ee
import zipfile


def getMonthlyData(year, month):
    '''Query LST monthly average image
    Args:
        year (_string_): use '01' typo for January, and so on
        month (_string_): same as above
    '''
 
    min_date = year+'-'+month+'-01'
    max_date = year+'-'+month+'-28'
    band = 'LST_Day_1km'
    collection = 'MODIS/061/MOD11A1'

    data = ee.ImageCollection(collection).filterDate(min_date, max_date).first()
                     
    return data



def downloadAsLink(year, data_list):
    '''Provide links to download all image elements in a list

    Args:
        data_list (_list_): _list of ee-queried images
        year (str): use '01' typo for January, and so on
    '''
    coords = [[42.02005066750512,
                39.03387755848272],               
                [42.02005066750512,
                36.859763930345395],
                [39.922495635935796,
                36.859763930345395],
                [39.922495635935796,
                39.03387755848272]]
    
    region = ee.Geometry.Polygon(coords)
    for i in range(12):
        name = "lst_"+str(year)+"_ordu_"+str(i+1)
        url=data_list[i].getDownloadUrl({
            'name': name,
            'bands': ['LST_Day_1km'],
            'region':region
        })
        path = os.path.join("..", "data", "lst")
        filehandle, _ = urllib.request.urlretrieve(url)
        with zipfile.ZipFile(filehandle, 'r') as zipObj:
            names = zipObj.namelist()
            for fileName in names:
                zipObj.extract(fileName, path)
        
        
def getYearlyData(year):
    '''Returns a list of monthly cropped images

    Args:
        year (string): use 4 digits typo ex : '2021'
    '''
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    
    data_list = []
    for m in months:
        data_list.append( getMonthlyData(year, m) )
    return data_list



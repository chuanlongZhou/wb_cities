import numpy
import requests
import io
import os
import ee
import json


def getMonthlyData(year, month):
    '''Query LST monthly average image
    Args:
        year (_string_): use '01' typo for January, and so on
        month (_string_): same as above
    '''
 
    min_date = year+'-'+month+'-01'
    max_date = year+'-'+month+'-28'
    collection = 'MODIS/061/MOD11A1'

    data = ee.ImageCollection(collection).filterDate(min_date, max_date).mean()
                     
    return data
        
        
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


def downloadAsLink( data_list, city, year):
    '''Provide links to download all image elements in a list

    Args:
        data_list (_list_): _list of ee-queried images
        year (str): use '01' typo for January, and so on
    '''
    bounding_box = json.load(open('../bounding_box.json'))
    box = bounding_box[city]
    [(ymax, xmin), (ymin, xmax)] = box['box']
    margin = 0.001
    region = ee.Geometry.BBox(xmin-margin, ymin+margin, xmax+margin, ymax+margin)
    for i in range(12):
        name = str(city)+"_"+str(year)+"_"+str(i+1)+'.tif'
        url=data_list[i].getDownloadUrl({
            'name': name,
            'bands': ['LST_Day_1km', 'LST_Night_1km'],
            'region':region,
            'format':'GEO_TIFF',
            'scale':1000
        })
        path = os.path.join("..", "data", "lst", "")
        with open(path+name, 'wb') as out_file:
            content = requests.get(url, stream=True).content
            out_file.write(content)
import numpy
import requests
import io
import os
import ee


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
    bounding_box = dict(
    Cairo=dict(box=[(30.4, 30.8),  (29.7, 31.8)]),
    Johannesburg=dict(box=[(-25.7, 27.7),  (-26.6, 28.5)]),
    Adana=dict(box=[(37.07143800485324, 35.17329182281017),  (36.91227725278698, 35.51638118905048)]),
    Ordu=dict(box=[(41.02005066750512, 37.859763930345395),  (40.922495635935796, 38.03387755848272)]),
    Trabzon=dict(box=[(41.021005197945385, 39.65238569404653),  (40.95879910380294, 39.80587291303715)]),
    Manisa=dict(box=[(38.69341901846549, 27.27799521554712),  (38.5893040428113, 27.491450649299416)]),
    )

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
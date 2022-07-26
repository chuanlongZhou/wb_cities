from shapely.geometry import Polygon

def create_polygon(box):
    """create box polygon for clipping the geopands df
    """
    (max_lat, min_lon), (min_lat, max_lon) = box
    return Polygon([(min_lon, max_lat), 
                    (min_lon, min_lat), 
                    (max_lon, min_lat), 
                    (max_lon, max_lat), 
                    (min_lon, max_lat)])

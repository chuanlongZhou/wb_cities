import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
# Pop Data Preprocessing

def to_degree(path, cities):
    dst_crs = 'EPSG:4326'
    for city in cities:
        filename = path+city+'.tif'
        with rasterio.open(filename) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })  
            with rasterio.open(filename, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

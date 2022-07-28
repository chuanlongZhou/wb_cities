import rioxarray

class Raster:
    def __init__(self, tiff, box=None, var_name="tif", meta="", cmap="pink", grid_data=False):
        # geopandas df of poylgon vectors
        self.tiff = tiff
        # the bounding box of the region
        self.box = box
        # information for the vector
        self.meta = meta
        # colormap for the tiff
        self.cmap = cmap
        
        if not grid_data:
            if box is not None:
                grid = Raster.box_clip(self.tiff, box)
                self.tiff = grid.to_dataset(name=var_name)
        else:
            self.tiff = tiff
            
    def reproject(self, crs):
        self.tiff = self.tiff.rio.reproject(crs)
        
    def interp(self, like_grid, var="all", method="linear"):
        """interpolate grid to a similar grid

        Args:
            like_grid (xarray array): template data array
            var (str, optional): variable need to be interpolated. Defaults to "all".
            method (str, optional): use "nearest" for categorical data. Defaults to "linear".

        Returns:
            xarray array: interpolated data array
        """
        if var=="all":
            res = self.tiff.interp_like(like_grid, method=method)
        else:
            res = self.tiff[var].interp_like(like_grid, method=method)
        return res
    
    @staticmethod
    def export_var(ds, var, file_path="test.tif"):
        ds = ds.transpose('band', 'y', 'x')
        ds[var].rio.to_raster(file_path)
    
    @staticmethod
    def box_clip(tiff_path, box):
        (max_lat, min_lon), (min_lat, max_lon) = box
        with rioxarray.open_rasterio(tiff_path) as src:
            grid = src.rio.clip_box(minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat)
        return grid
from .utils import create_polygon
import pandas as pd


class Vector:
    def __init__(self, geo_df, box=None, level=None, meta=""):
        # geopandas df of poylgon vectors
        self.geo_df = geo_df
        # the column name for selecting the regions
        self.level = level
        # the bounding box of the region
        self.box = box
        # information for the vector
        self.meta = meta

        if level is not None:
            self.geo_df = geo_df.dissolve(level).reset_index()
        if box is not None:
            polygon = create_polygon(box)
            self.geo_df = self.geo_df.clip(polygon)

    def bound_data(self, data_df, column, keep=None):
        """add additional data column to the geo_df, the different year should be different column

        Args:
            data_df (DataFrame): the df for the additional data
            column (str): the indexing column name, the value should be consistant with the "level" column in geo_df
            keep ([str], optional): the columns will be kept. Defaults to None.
        """
        # binding data to poylgons
        self.geo_df = self.geo_df.merge(
            data_df, left_on=self.level, right_on=column)
        if keep is not None:
            self.geo_df = self.geo_df[keep]

    @staticmethod
    def clip_house(city_name, house_df, clip_polygon, geojson=True):
        """clip house from MS database in a certain region

        Args:
            city_name (str): region name for saved files
            house_df (geodf): MS database
            clip_polygon (polygon): region polygon

        Returns:
            geodf: clipped house with hosue area (m2) in the region
        """
        st = 0
        inc = 100000
        h = None
        while st <= len(house_df)+inc:
            temp = house_df[st:st+inc].buffer(0).clip(clip_polygon)
            print(st, len(temp))
            if h is None:
                h = temp
            else:
                h = pd.concat([h, temp])
            st += inc

        df = h.to_frame(name="geometry")
        df = df.to_crs("EPSG:3395")
        df["density"] = 1
        df["area"] = df.area
        if geojson:
            df.to_file(f"{city_name}.json", driver="GeoJSON")
        df.to_pickle(f"{city_name}.pkl")

        return df

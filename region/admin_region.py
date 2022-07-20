from shapely.geometry import Polygon


def create_polygon(top, bottom):
    top_lat, top_lon = top
    bottom_lat, bottom_lon = bottom
    return Polygon([(top_lon, top_lat), (top_lon, bottom_lat), (bottom_lon, bottom_lat), (bottom_lon, top_lat), (top_lon, top_lat)])


class AdminRegion:
    def __init__(self, region, level):
        self.level = level
        self.region = region.dissolve(level).reset_index()
        self.box = None
        
    def select(self, region_list):
        self.region = self.region.loc[self.region[self.level].isin(region_list)]
        
    def create_box(self, bound_box):
        polygon = create_polygon (bound_box[0],  bound_box[1])
        self.region = self.region.clip(polygon)
        self.box = bound_box
        
        
class Census(AdminRegion):
    census_col = [
                    "population",
                    "household_number",
                    "household_size"
                    ]

    def __init__(self, region, level):
        super().__init__(region, level)
        
    def bound_census(self, df, column, keep=None):
        if keep is None:
            keep = self.census_col
        else:
            keep = []
        keep.extend([self.level,"geometry"])
        keep = list(set(keep))
        self.region = self.region.merge(df, left_on=self.level, right_on=column)
        self.region= self.region[keep]
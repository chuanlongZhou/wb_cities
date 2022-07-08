from utils import *

class Region:
    def __init__(self, df, bound_box, city):
        self.df = df
        polygon = create_polygon (bound_box[0],  bound_box[1])
        self.region = df.clip(polygon)
        self.city = None
        for c in city:
            if self.city is None:
                self.city= df.loc[df[c]==city[c]]
            else:
                self.city = self.city.loc[self.city[c]==city[c]]
        
    def clip_house(self, house):
        # self.house = parallelize(house, clip_func, self.region, cups=-1)
        st=0
        inc = 100000
        h=None
        while st<=len(house)+inc:
            temp = house[st:st+inc].buffer(0).clip(self.region)
            print(st, len(temp))
            if h is None:
                h = temp
            else:
                h = pd.concat([h,temp])
            st+=inc
        
        self.house = h
        
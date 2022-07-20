import matplotlib.pyplot as plt
import folium
import contextily as cx
from rasterio.plot import show
import rasterio

from utils import *
from .admin_region import AdminRegion, Census
from lclu import LCZ


class Region:
    colormap = "OrRd"
    bg_color="#b3b3b3"
    bg_edge_color ="#636363"
    outer_box_color = "#56b3f5"
    outer_box_edge_color = "#6279b5"
    
    def __init__(self, df, level, name=None, lcz_path=None):
        self.df = df
        self.name = name
        self.admin_region = Census(df, level)
        self.inner_box = Census(df, level)
        self.outer_box = Census(df, level)
        self.house = None
        self.lcz = None
        if lcz_path is not None:
            self.lcz = LCZ(lcz_path)
            
    def clip_house(self, house):
        st=0
        inc = 100000
        h=None
        while st<=len(house)+inc:
            temp = house[st:st+inc].buffer(0).clip(self.box_small.region)
            print(st, len(temp))
            if h is None:
                h = temp
            else:
                h = pd.concat([h,temp])
            st+=inc
        
        self.house = h
        
    def create_map_static(self, column, ax=None, dpi=100, legend=True):
        if ax is None:
            fig = plt.figure(figsize=(12,8), dpi=dpi)
            ax = plt.gca()
        ax = self.admin_region.region.plot(alpha=0.2, color=self.bg_color, edgecolor=self.bg_edge_color, ax=ax)
        ax = self.outer_box.region.plot(alpha=0.4, color=self.outer_box_color, edgecolor=self.outer_box_edge_color,ax=ax)
        ax = self.inner_box.region.plot(alpha=0.4, ax=ax, column=column, cmap=self.colormap,edgecolor=self.outer_box_edge_color, legend=legend, zorder=20)
        if self.lcz is not None:
            w, bounds = self.lcz.get_region(self.inner_box.box)
            rasterio.plot.show(w, extent=bounds, ax=ax, cmap=self.lcz.lcz_cmap, alpha=0.6, zorder=10)
            for im in ax.get_images():
                im.set_clim(1, 17)
        ax.axis('off')    
        cx.add_basemap(ax, crs="EPSG:4326")
        
        return ax
    
    def create_map_interactive(self, column):
        m = self.admin_region.region.explore(
            name="country region",
            tooltip=self.admin_region.level,
            popup=False,
            # opacity=0.3,
            style_kwds=dict(color=self.bg_color, edgecolor=self.bg_edge_color)
            )
        
        self.outer_box.region.explore(
            m=m,
            name="outer box",
            tooltip=self.admin_region.level, # show "BoroName" value in tooltip (on hover)
            popup=False,
            # opacity=0.5,
            style_kwds=dict(color=self.outer_box_color, edgecolor=self.outer_box_edge_color)
            )

        self.inner_box.region.explore(
            m=m,
            name="wb project region",
            column=column, # make choropleth based on "BoroName" column
            tooltip=[self.inner_box.level, column], # show "BoroName" value in tooltip (on hover)
            popup=True, # show all values in popup (on click)
            tiles=column, # use "CartoDB positron" tiles
            cmap=self.colormap, # use "Set1" matplotlib colormap
            style_kwds=dict(edgecolor=self.outer_box_edge_color) # use black outline
            )
        
        if self.lcz is not None:
            w, bounds = self.lcz.get_region(self.inner_box.box)
            img= folium.raster_layers.ImageOverlay(
                name="LCZ",
                image=w,
                bounds=self.inner_box.box,
                colormap=lambda x: self.lcz.lcz_color_rgb[x],
                interactive=True,
                cross_origin=False,
                zindex=999,
            )
            img.add_to(m)

        folium.TileLayer('Stamen Toner', control=True, opacity=0.6).add_to(m)  # use folium to add alternative tiles
        folium.LayerControl().add_to(m)  # use folium to add layer control
        
        return m
    

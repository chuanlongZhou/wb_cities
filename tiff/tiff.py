import rasterio
from rasterio.windows import Window
import matplotlib.pyplot as plt
import numpy as np
from .constant import lcz_cmap, lcz_detail, lcz_color, lcz_color_rgb, lcz_weights

class TIFF:
    def __init__(self, tiff_path, prob_tiff_path=None):
        self.tiff_path = tiff_path

    def get_region(self, box):
        path = self.tiff_path
        (lat_1, lon_1), (lat_2, lon_2) = box
        
        with rasterio.open(path) as src:
            transformer = src.transform
            x_1, y_1 = ~transformer* (lon_1, lat_1)
            x_2, y_2 = ~transformer* (lon_2, lat_2)
            w = src.read(1, window=Window(x_1, y_1, x_2-x_1, y_2-y_1))
            bounds = ( lon_1,lon_2, lat_2, lat_1)
        
        return w, bounds


class LCZ(TIFF):
    def __init__(self, tiff_path, prob_tiff_path=None):
        super().__init__(tiff_path)
        self.lcz_cmap = lcz_cmap
        self.lcz_detail = lcz_detail
        self.lcz_color = lcz_color
        self.lcz_color_rgb = lcz_color_rgb   
        self.lcz_weights = lcz_weights

    def plot_region(self, box, fig_size=(10,10), ax = None, hist=True, hist_ax=None):
        # get a LCZ map and histogram from a box-bounded region
        plt.rcParams["figure.figsize"] = fig_size
        lcz_path = self.tiff_path
        
        if ax is None:
            fig, ax = plt.subplots(figsize=fig_size)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            ax.axis('off')
            w = self.get_region(box)
            content = ax.imshow(w, cmap=lcz_cmap)
            content.set_clim(1,17)
        
        if hist_ax is None:
            fig, hist_ax = plt.subplots(figsize=fig_size)
            
        hist = np.histogram(w.flatten(), bins=range(1,19))        
        hist_ax.bar(np.arange(1,18), hist[0], color = list(self.lcz_color.values()))
        hist_ax.set_xticks(np.arange(1, 18))
        hist_ax.set_xticklabels(list(self.lcz_detail.values()), rotation=45, ha="right")
            
        return (ax, hist_ax), content, w, hist

    def generate_global(self):
        # not useful only for test
        lcz_path = self.tiff_path
        
        dpi = 3000
        xsize=389620
        ysize=155995
        x_add = 256*20

        plt.rcParams["figure.figsize"] = (x_add/dpi,ysize/2/dpi)
        with rasterio.open(lcz_path) as src:
            curr = 0
            fig_num = 77
            while curr<xsize:
                print(fig_num)
                
                fig, ax = plt.subplots()
                plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
                ax.axis('off')
                
                w = src.read(1, window=Window(curr, 0, x_add, ysize/2))
                ax = plt.imshow(w, ax=ax, cmap=lcz_cmap)
                plt.savefig(f"{fig_num}.png", dpi=300)
                curr+=x_add
                fig_num+=1
                
            curr = 0
            while curr<xsize:
                print(fig_num)
                w = src.read(1, window=Window(curr, ysize/2, x_add, ysize/2))
                
                fig, ax = plt.subplots()
                plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
                ax.axis('off')
                
                ax = plt.imshow(w, ax=ax, cmap=lcz_cmap)
                plt.savefig(f"{fig_num}.png", dpi=300)
                curr+=x_add
                fig_num+=1

    def get_weight(self, val):
        return lcz_weights[val]
    
    def get_average_weight(self, w):
        vweight = np.vectorize(self.get_weight)
        w_weights = vweight(w)
        return w_weights.mean()
    
    def fetch_LCZ(self, box):
        w, bounds = self.get_region(box)
        result = self.get_average_weight(w)
        return result
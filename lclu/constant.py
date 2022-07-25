from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from PIL import ImageColor

lcz_color ={
    0:"#cce0ff",
    1:'#910613',
    2:'#D9081C',
    3:'#FF0A22',
    4:'#C54F1E',
    5:'#FF6628',
    6:'#FF985E',
    7:'#FDED3F',
    8:'#BBBBBB',
    9:'#FFCBAB',
    10:'#565656',
    11:'#006A18',
    12:'#00A926',
    13:'#628432',
    14:'#B5DA7F',
    15:'#000000',
    16:'#FCF7B1',
    17:'#656BFA',
}

lcz_color_rgb = {}
for k in lcz_color:
    lcz_color_rgb[k] = ImageColor.getcolor(lcz_color[k], "RGB")

lcz_cmp = []
for i in lcz_color:
    lcz_cmp.append(lcz_color[i])
lcz_cmap = ListedColormap(lcz_cmp)
lcz_cmap.set_under('#cce0ff')

lcz_detail={
    1:'Compact highrise',
    2:'Compact midrise',
    3:'Compact lowrise',
    4:'Open highrise',
    5:'Open midrise',
    6:'Open lowrise',
    7:'Lightweight low-rise',
    8:'Large lowrise',
    9:'Sparsely built',
    10:'Heavy Industry',
    11:'Dense trees',
    12:'Scattered trees',
    13:'Bush, scrub',
    14:'Low plants',
    15:'Bare rock or paved',
    16:'Bare soil or sand',
    17:'Water',
}
# E = emission*(building base emission + human activities emission)* region modifier * temporal modifier * other modifier 
#    = emission*( house_density*builidng type factor + house_area*house_lcz_height)* population * (surface T) * (night light) 

# emission_simple = lambda ds: (ds.density + ds.area*ds.lcz_height)* ds.population
from math import log


def emission_simple(ds):
    e = (ds.density + ds.area*ds.lcz_height)* ds.population
    return e 

def building_surface(ds):
    s = ds.area / ds.density
    return s

def building_volume(ds):
    v = ds.surface * ds.height
    return v

def pop_desaggregation_v(ds, pop):
    p = ds.volume * int(pop)
    return p

def pop_desaggregation_s(ds, pop):
    p = ds.surface * int(pop)
    return p
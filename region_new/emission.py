# E = emission*(building base emission + human activities emission)* region modifier * temporal modifier * other modifier 
#    = emission*( house_density*builidng type factor + house_area*house_lcz_height)* population * (surface T) * (night light) 

# emission_simple = lambda ds: (ds.density + ds.area*ds.lcz_height)* ds.population

def emission_simple(ds):
    e = (ds.density + ds.area*ds.lcz_height)* ds.population
    return e 


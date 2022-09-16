# WB : Residential 

 - GHSL data must be downloaded by hand for the upcoming cities, [https://ghsl.jrc.ec.europa.eu/download.php](here), in tiles. Having been lazy, I renamed each tile with the name of the city it contains, meaning I duplicated tiles that contained multiple cities. Additionally, all the data comes in Molleweide CRS, so we must convert it before using it : funtion `to_degree` in `utils.py` converts all the tiles for a given variable and overwrites the downloaded ones. 
 - Folder `microsoft_buildings` contains the script to download MB within the FUAs bounding boxes.
 - Folder `ml` contains the script `v3_prepare.py` to combine all the features for each city. Note that : 
   1. I did not run it for Cairo and Johannesburg.
   2. It is not multiprocessed. 
   3. Only the first point of each polygon is considered for the intersection (faster, less precise, esp. with WSF3D, you might want to change that).
 - In folder `region_new` : renamed `emissions` as `equations` as I added more equations to compute additional variables on the Xarray. I also added in the `region.py` file the `region_from_cities` method so we dont have to cal the .add_layer method every time (although it should probably be moved in `utils.py`).
   

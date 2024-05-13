import os, csv
import pickle
import numpy as np
import pandas as pd
# import geopandas as gpd
# from shapely.geometry import Point


def Compute_Name(config):
    name = str(config["centroids_type"])
    return name


def load_zones_from_file(file_path):
    zone_lists = []
    with open(file_path, 'r', newline='') as file:
        print("file_path ", file_path)
        csv_reader = csv.reader(file, delimiter='\t')
        for row in csv_reader:
            # Convert each element in the row to an integer and store it in the list
            zone_row = []
            for cell in row:
                # Split the cell content by commas, convert to integers, and append to the row
                cell_values = [int(val.strip()) for val in cell.split(',') if val.strip()]  #
                zone_row.extend(cell_values)
            zone_lists.append(zone_row)

    # build a zone dictionary based on zone_list
    zone_dict = {}
    for index, sublist in enumerate(zone_lists):
        for item in sublist:
            zone_dict[item] = index

    return zone_lists, zone_dict

def get_distance(row):
    ''' helper function for calculating distance from student to school, get
    distance in miles between two lat-lon pairs'''
    lat1 = row['Lat']
    lon1 = row['Lon']
    lat2 = row['st_lat']
    lon2 = row['st_lon']
    return calculate_euc_distance(lat1, lon1, lat2, lon2)

def calculate_euc_distance(lat1, lon1, lat2, lon2):
    # print(str(lat1) + "  " + str(lon1) + "  " + str(lat2) + "  " + str(lon2) + "  " )
    return 6371.01 * np.arccos(np.sin(lat1 * np.pi / 180) * np.sin(lat2 * np.pi / 180) + \
                               np.cos(lat1 * np.pi / 180) * np.cos(lat2 * np.pi / 180) \
                               * np.cos((lon1 - lon2) * np.pi / 180)) * 0.621371  # return distance in miles


def load_census_shapefile(level):
    # # get census block shapefile
    # path = os.path.expanduser(
    #     "Zone_Generation/Zone_Data/GEO_EXPORT/geo_export_d4e9e90c-ff77-4dc9-a766-6a1a7f7d9f9c.shp"
    # )
    # census_sf = gpd.read_file(path)
    # census_sf["Block"] = (
    #     census_sf["geoid10"].fillna(value=0).astype("int64", copy=False)
    # )
    #
    # df = pd.read_csv("Zone_Generation/Zone_Data/block_blockgroup_tract.csv")
    # df["Block"].fillna(value=0, inplace=True)
    # df["Block"] = df["Block"].astype("int64")
    #
    # census_sf = census_sf.merge(df, how="left", on="Block")
    #
    # census_sf.dropna(subset=['BlockGroup', 'Block'], inplace=True)
    # census_sf[level] = census_sf[level].astype('int64')
    #
    # census_sf = census_sf[["Block", "BlockGroup"]]
    # census_sf.to_csv('census_sf.csv', index=False)
    # print("census_sf ", census_sf)
    loaded_df = pd.read_csv('Zone_Generation/Zone_Data/census_sf.csv')

    return loaded_df

def load_euc_distance_data(level, area2idx, complete_bg = False):
    if level == "attendance_area":
        save_path = "Zone_Generation/Zone_Data/distances_aa2aa.csv"
    elif level == "BlockGroup":
        save_path = "Zone_Generation/Zone_Data/distances_bg2bg.csv"
    elif (level == "Block") & (complete_bg == False):
        save_path = "Zone_Generation/Zone_Data/distances_b2b_schools.csv"
    elif (level == "Block") & (complete_bg == True):
        save_path = "Zone_Generation/Zone_Data/distances_b2b.csv"

    if os.path.exists(os.path.expanduser(save_path)):
        distances = pd.read_csv(save_path, index_col=level)
        distances.columns = [int(float(x)) for x in distances.columns]

        distance_dict = {}
        rows = distances.index.tolist()
        cols = list(distances.columns)

        # Change the csv file into a double dictionary, so the distances can be accessed easier
        for area_i in rows:
            inner_dict = {}
            for area_j in cols:
                inner_dict[area2idx[area_j]] = distances.loc[area_i, area_j]
            distance_dict[area2idx[area_i]] = inner_dict

        return distance_dict

    if level == "Block":
        census_sf = load_census_shapefile(level)
        df = census_sf.dissolve(by="Block", as_index=False)
        df["centroid"] = df.centroid
        df["Lat"] = df["centroid"].apply(lambda x: x.y)
        df["Lon"] = df["centroid"].apply(lambda x: x.x)
        df = df[["Block", "Lat", "Lon"]]
        df.loc[:, "key"] = 0
        df = df.merge(df, how="outer", on="key")

        df.rename(
            columns={
                "Lat_x": "Lat",
                "Lon_x": "Lon",
                "Lat_y": "st_lat",
                "Lon_y": "st_lon",
                "Block_x": "Block",
            },
            inplace=True,
        )
    elif level == "BlockGroup":
        census_sf = load_census_shapefile(level)
        df = census_sf.dissolve(by="BlockGroup", as_index=False)
        df["centroid"] = df.centroid
        df["Lat"] = df["centroid"].apply(lambda x: x.y)
        df["Lon"] = df["centroid"].apply(lambda x: x.x)
        df = df[["BlockGroup", "Lat", "Lon"]]
        df.loc[:, "key"] = 0
        df = df.merge(df, how="outer", on="key")
        df.rename(
            columns={
                "Lat_x": "Lat",
                "Lon_x": "Lon",
                "Lat_y": "st_lat",
                "Lon_y": "st_lon",
                "BlockGroup_x": "BlockGroup",
            },
            inplace=True,
        )
    elif level == "attendance_area":
        df = units_data[["attendance_area", "lat", "lon"]]
        df.loc[:, "key"] = 0
        df = df.merge(df, how="outer", on="key")
        df.rename(
            columns={
                "lat_x": "Lat",
                "lon_x": "Lon",
                "lat_y": "st_lat",
                "lon_y": "st_lon",
                "attendance_area_x": "attendance_area",
            },
            inplace=True,
        )

    df["distance"] = df.apply(get_distance, axis=1)
    df[level] = df[level].astype('Int64')

    table = pd.pivot_table(
        df,
        values="distance",
        index=[level],
        columns=[level + "_y"],
        aggfunc=np.sum,
    )
    table.to_csv(save_path)
    return table

def load_bg2att(level, census_sf = None):
    savename = 'Zone_Generation/Zone_Data/bg2aa_mapping.pkl'

    if os.path.exists(os.path.expanduser(savename)):
        file = open(savename, "rb")
        bg2att = pickle.load(file)
        # print("bg to aa map was loaded from file")
        return bg2att

    # load attendance area geometry + its id in a single dataframe
    path = os.path.expanduser('Zone_Generation/Zone_Data/ESAA/2013 ESAAs SFUSD.shp')
    sf = gpd.read_file(path)
    sf = sf.to_crs('epsg:4326')
    sc_merged = make_school_geodataframe()
    translator = sc_merged.loc[sc_merged['category'] == 'Attendance'][['school_id', 'index_right']]
    translator['school_id'] = translator['school_id'].fillna(value=0).astype('int64', copy=False)
    sf = sf.merge(translator, how='left', left_index=True, right_on='index_right')

    # load blockgroup/block  geometry + its id in a single dataframe
    df = census_sf.dissolve(level, as_index=False)

    bg2att = {}
    for i in range(len(df.index)):
        area_c = df['geometry'][i].centroid
        for z, row in sf.iterrows():
            aa_poly = row['geometry']
            # if aa_poly.contains(area_c) | aa_poly.touches(area_c):
            if aa_poly.contains(area_c):
                bg2att[df[level][i]] = row['school_id']

    file = open(savename, "wb")
    pickle.dump(bg2att, file)
    file.close()

    return bg2att


def make_school_geodataframe(school_path ='Zone_Generation/Zone_Data/schools_rehauled_1819.csv'):
    ''' make sc_merged '''
    sch_df = pd.read_csv(school_path)

    # make GeoDataFrame
    geometry = [Point(xy) for xy in zip(sch_df['lon'], sch_df['lat'])]
    school_geo_df = gpd.GeoDataFrame(sch_df, crs='epsg:4326', geometry=geometry)

    # read shape file of attendance areas
    path = os.path.expanduser('Zone_Generation/Zone_Data/ESAA/2013 ESAAs SFUSD.shp')
    sf = gpd.read_file(path)
    sf = sf.to_crs('epsg:4326')
    print("succesfully read SF")
    print(sf)

    # school data and shape file merged
    sc_merged = gpd.sjoin(school_geo_df, sf, how="inner", op='intersects')

    return sc_merged

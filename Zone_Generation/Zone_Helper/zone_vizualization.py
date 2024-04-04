import fiona
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point



class ZoneVisualizer:
    def __init__(self, level, year='1819'):
        self.level = level
        self.year = year
        self._read_data()


    def _read_data(self):
        # pd.set_option("display.max_rows", None, "display.max_columns", None)

        # get school latitude and longitude
        sc_ll = pd.read_csv(f'Zone_Generation/Zone_Data/schools_rehauled_{self.year}.csv')
        geometry = [Point(xy) for xy in zip(sc_ll['lon'], sc_ll['lat'])]
        # almost the sc_ll file (school data) + Points(lon/lat) of them, in a geo-data-frame
        school_geo_df = gpd.GeoDataFrame(sc_ll, crs='epsg:4326', geometry=geometry)
        # read shape file of attendance areas
        if self.level == 'attendance_area':
            # Used to be in downloads folder, but I moved it to SFUSD folder
            with fiona.Env(SHAPE_RESTORE_SHX='YES'):
                # Now, try to open your shapefile within this context
                path = os.path.expanduser('Zone_Generation/Zone_Data/ESAA/2013 ESAAs SFUSD.shp')
                self.sf = gpd.read_file(path)
                self.sf.set_crs(epsg='4326', allow_override=True, inplace=True)

            # path = os.path.expanduser('Zone_Generation/Zone_Data/2013_ESAAs_SFUSD.shp')
            # self.sf = gpd.read_file(path)

        elif (self.level == 'BlockGroup') | (self.level == 'Block'):
            # Changed to shape files folder from 2010 census
            path = os.path.expanduser('Zone_Generation/Zone_Data/GEO_EXPORT/geo_export_d4e9e90c-ff77-4dc9-a766-6a1a7f7d9f9c.shp')
            self.sf = gpd.read_file(path)
            self.sf['geoid10'] = self.sf['geoid10'].fillna(value=0).astype('int64', copy=False)

            df = pd.read_csv('Zone_Generation/Zone_Data/block_blockgroup_tract.csv')
            df['Block'] = df['Block'].fillna(value=0).astype('int64', copy=False)
            self.sf = self.sf.merge(df, how='left', left_on='geoid10', right_on='Block')
        self.sf = self.sf.to_crs(epsg=4326)

        if self.level == 'attendance_area':
            # school data and shape file merged
            # sc_merged includes all data in school_geo_df, and also showing in which attendance area(?) each Point is.
            # This info is available in an extra columnt, 'index_right'
            sc_merged = gpd.sjoin(school_geo_df, self.sf, how="inner", op='intersects')
            self.labels = sc_merged.loc[sc_ll['category'] == 'Citywide'][['school_id', 'index_right', 'geometry']]

            # make zone to attendance area id translator
            translator = sc_merged.loc[sc_ll['category'] == 'Attendance'][['school_id', 'index_right', 'geometry']]
            self.translator = translator.rename(columns={'school_id': 'aa_zone'})
            self.sc_merged = sc_merged.merge(self.translator, how='left', on='index_right')


    def show_plot(self, save_path, title):

        plt.title(title)
        plt.gca().set_yticklabels([])
        plt.gca().set_xticklabels([])
        plt.gca().set_xlim(-122.525, -122.350)
        plt.gca().set_ylim(37.70, 37.84)


        if save_path != "":
            print(save_path + '.png')
            plt.savefig(save_path + '.png')
        plt.show()
        print("Finished plotting")
        return plt

    def zones_from_dict(self, zone_dict, label=False, title="",
                        centroid_location=-1, save_path=""):

        # for each aa_zone (former school_id), change it with whichever zone index this gets
        # matched to based on the LP solution in zone_dict
        if self.level == 'attendance_area':
            self.sc_merged['zone_id'] = self.sc_merged['aa_zone'].replace(zone_dict)
            df = self.sf.merge(self.sc_merged, how='left', right_on='index_right', left_index=True)
            # df['zone_id'] = df['aa_zone'].replace(zone_dict)

            df['filter'] = df['zone_id'].apply(lambda x: 1 if int(x) in range(65) else 0)
            df = df.loc[df['filter'] == 1]

            plt.figure(figsize=(15, 15))
            ax = self.sf.boundary.plot(ax=plt.gca(), alpha=0.4, color='grey')

            if label:
                self.translator.apply(
                    lambda x: ax.annotate(fontsize=12, s=x.aa_zone, xy=x.geometry.centroid.coords[0], ha='center'),
                    axis=1);
                self.labels.apply(
                    lambda x: ax.annotate(fontsize=12, s=x.school_id, xy=x.geometry.centroid.coords[0], ha='center'),
                    axis=1);

        elif (self.level == 'BlockGroup') | (self.level == 'Block'):
            plt.figure(figsize=(20, 20))
            ax = self.sf.boundary.plot(ax=plt.gca(), alpha=0.4, color='grey')

            self.sf.dropna(subset=[self.level], inplace=True)
            # drop rows that have NaN for zone_id
            if label:
                # self.sf.apply(lambda x: ax.annotate(fontsize=8, s= int(x.BlockGroup), xy=x.geometry.centroid.coords[0], ha='center'), axis=1);
                self.sf.apply(lambda x: ax.annotate(fontsize=8,
                                                    text=int(x.BlockGroup),
                                                    xy=x.geometry.centroid.coords[0], ha='center'), axis=1);
                # self.sf.apply(lambda x: ax.annotate(fontsize=15, s= int(x.Block) if int(x.Block) == 60750255002023 else ".", xy=x.geometry.centroid.coords[0], ha='center'), axis=1);

            self.sf['zone_id'] = self.sf[self.level].replace(zone_dict)
            self.sf['filter'] = self.sf['zone_id'].apply(lambda x: 1 if int(x) in range(62) else 0)
            df = self.sf.loc[self.sf['filter'] == 1]

        # plot zones
        df.plot(ax=ax, column='zone_id', cmap='tab20', legend=True, aspect=1)
        plt.title(title)

        # plot centroid locations
        # plt.scatter(centroid_location['lon'], centroid_location['lat'], s=3, c='black', marker='s')
        # for lon, lat, id in zip(centroid_location['lon'], centroid_location['lat'], centroid_location['school_id']):
        #     plt.text(lon, lat, id, ha='center', va='center')

        # # plot school locations
        # aa = self.sc_merged.loc[self.sc_merged['category']=='Attendance']
        # citywide = self.sc_merged.loc[self.sc_merged['category']=='Citywide']
        # print("this is the number of all schools")
        # print(len(aa)+len(citywide))
        # plt.scatter(aa['lon'],aa['lat'],s=10, c='red',marker='s')
        # plt.scatter(citywide['lon'],citywide['lat'],s=10, c='black',marker='^')

        self.show_plot(save_path, title)


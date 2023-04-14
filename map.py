from utils.load import load_everthing

import pandas as pd
import geopandas as gpd
import country_converter as coco
import folium
import numpy as np

def make_merged_df(country_code):

    """ Takes 
            - The country code of the country under examination
        Returns:
            - A dataframe with the connections between one country and all others
            - A dataframe of all the shapefile containing the geological data
    """

  
    # Loading in the Facebook data
    friendship_data = pd.read_csv("data/friendship_data/countries-countries-fb-social-connectedness-index-october-2021.tsv", delimiter="\t")
    # Only choosing the countries that are connected to the location we are interested in
    country_connect = friendship_data[friendship_data['user_loc'] == country_code]

    # Reading in the shapefile using Geopandas
    # shapefile gotten from Version 4.1 https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/
    shapefile = 'src/Visualisations/map/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
    geo_df = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
    geo_df.columns = ['country', 'country_code', 'geometry']

    # Dropping Antarctica since it's too big and not relevant
    geo_df = geo_df.drop(geo_df.loc[geo_df['country'] == 'Antarctica'].index)

    # Converting the country codes
    iso3_codes = geo_df['country'].to_list()
    iso2_codes_list = coco.convert(names=iso3_codes, to='ISO2', not_found='NULL')
    geo_df['iso2_code'] = iso2_codes_list
    # There are some countries for which the converter could not find a country code. 
    # We will drop these countries.
    geo_df = geo_df.drop(geo_df.loc[geo_df['iso2_code'] == 'NULL'].index)

    return country_connect, geo_df


def Choropleth_map(country_code):


    friendship_df, geo_df = make_merged_df(country_code)


    # Logging the scaled_sci column to make changes appear more easily in the map
    friendship_df['scaled_sci'] = np.log2(friendship_df['scaled_sci']+1)
    friendship_df = friendship_df.round({'scaled_sci'})
    # Merging the Geodf with our Friendship DF
    df = pd.merge(left=geo_df, right=friendship_df, how='left', left_on='iso2_code', right_on='fr_loc')
    df = df[df['fr_loc'] != country_code]

    # Creating the map 
    m = folium.Map(location=[0, 0], zoom_start=2)
    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(m)

    cp = folium.Choropleth(
        geo_data=df,
        data=df,
        columns=['country_code', 'scaled_sci'],
        key_on='feature.properties.country_code',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Legend Title'
    ).add_to(m)

    # Adding a tooltip to each country and saving the map

    folium.GeoJsonTooltip(['country_code', 'scaled_sci']).add_to(cp.geojson)
    m.save('src/Visualisations/map/index.html')




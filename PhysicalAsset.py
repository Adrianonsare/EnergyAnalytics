import os
import pandas as pd
import requests
import requests
import json
import matplotlib.pyplot as plt
import plotly.express as px
from pandas.io.json import json_normalize
import config
import seaborn as sns
import joblib
from windpowerlib import ModelChain, WindTurbine, create_power_curve
from windpowerlib import data as wt
import datetime as datetime
from datetime import date, timedelta
import logging
import streamlit as st

# Get logging messages from winpowerlib
logging.getLogger().setLevel(logging.DEBUG)


# Setting Coordinates of Lake Turkana Wind
latitude = 2.48903
longitude = 36.79317
tz = 'Africa/Nairobi'

# Set start and end date for the wind turbine power calculations
# Time period goes back 12 days
end = pd.Timestamp(datetime.date.today(), tz=tz)
start = end - timedelta(12)

# Obtain weather data from the Open weather API
lat = latitude
lon = longitude
urls = "https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s" % (
    lat, lon, config.api_key)

# Run requests from the API
jsonDatas = requests.get(urls).json()
dat_weath = pd.DataFrame(jsonDatas['list'])


# Some of the columns have dictionary values
# These need to be converted to pandas series
# and then concatenated into the original dataframe
main = dat_weath.main.apply(pd.Series)
wind = dat_weath.wind.apply(pd.Series)
weather = dat_weath.weather.apply(pd.Series)
dat_weath = pd.concat([dat_weath, main, wind, weather], axis=1).drop(['main', 'wind',
                                                                      'weather', 'clouds', 'sys', 0], axis=1)

# Feature Engineering
# Temperature conversion from Kelvin to Celsius for input into model
dat_weath['temp'] = dat_weath['temp']+273
# Pressure conversion to pascals
dat_weath['pressure'] = dat_weath['pressure']*100
# Select fields that windpowerlib accepts as inputs
dat_weath = dat_weath[['dt_txt', 'speed', 'temp', 'pressure']]
# Rename columns
dat_weath = dat_weath.rename(
    columns={'speed': 'wind_speed', 'temp': 'temperature', 'pressure': 'pressure'})
# Set index
dat_weath = dat_weath.set_index('dt_txt')

# ---------------------------------------------------------------------------
# set a value to roughness index and hub height
dat_weath['roughness_length'] = 0.001
dat_weath['height'] = 8
# Input requires multilevel index
dat_weath = dat_weath.set_index('height', append=True).unstack('height')

# ----------------------------------------------------------------------------
# specification of own wind turbine (Note: power curve values and
# nominal power have to be in Watt)
my_vestas_turbine = {
    'nominal_power': 850e3,  # in W
    'hub_height': 60,  # in m
    'power_curve': pd.DataFrame(
        data={'value': [p * 1000 for p in [
            0, 1.7, 30.8, 77.4, 139.7, 211.6, 294.1, 438.9, 578.4, 668, 783.6, 819.4, 841.8, 850.4, 851.9]],  # in W
            'wind_speed': [0.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                           11.0, 12.0, 13.0, 14.0, 15.0, 16.0]})  # in m/s
}
# initialiss_ze WindTurbine object.
my_vestas_turbine = WindTurbine(**my_vestas_turbine)


# -----------------------------------------------------------------------
# The ModelChain is a class that provides all necessary steps to calculate the power output of a wind turbine. When calling the 'run_model' method, first the wind speed and density (if necessary) at hub height are calculated and
#  then used to calculate the power output.
#   You can either use the default methods for the calculation steps,
#   as done for 'my_turbine', or choose different methods, as done for the 'e126'.
#    Of course, you can also use the default methods while only changing one or two of them,
#     as done for 'my_turbine2'.


# own specifications for ModelChain setup
modelchain_data = {
    'wind_speed_model': 'logarithmic',      # 'logarithmic' (default),
                                            # 'hellman' or
                                            # 'interpolation_extrapolation'
    # 'barometric' (default), 'ideal_gas'
    'density_model': 'ideal_gas',
                                            #  or 'interpolation_extrapolation'
    'temperature_model': 'linear_gradient',  # 'linear_gradient' (def.) or
                                            # 'interpolation_extrapolation'
    'power_output_model':
        'power_coefficient_curve',          # 'power_curve' (default) or
                                            # 'power_coefficient_curve'
    'density_correction': True,             # False (default) or True
    'obstacle_height': 0,                   # default: 0
    'hellman_exp': None}                    # None (default) or None


# power output calculation for example_turbine
# own specification for 'power_output_model'
mc_example_turbine = ModelChain(
    my_vestas_turbine,
    wind_speed_model='hellman').run_model(dat_weath)
my_vestas_turbine.power_output = mc_example_turbine.power_output


# ---------------------------------------------------------------------------
my_vestas_turbine.power_output = (my_vestas_turbine.power_output)*365/10**6
my_vestas_turbine.power_output
Pout = my_vestas_turbine.power_output.reset_index()

# ---------------------------------------------------------------------------
Pout['timestamp_local'] = pd.to_datetime(Pout['dt_txt'])
Pout.set_index('timestamp_local', inplace=True)
df_vals= list(Pout['feedin_power_plant'].unique())

# _____________________________________________________________________


def get_database():
    from pymongo import MongoClient
    import pymongo

    client = pymongo.MongoClient("mongodb+srv://adrianonsare:#PE$_vVB4tZp~#3@cluster0.r3enc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    # Create the database for our example (we will use the same database throughout the tutorial
    return client['New_Data']
    
# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":    
    
    # Get the database
    dbname = get_database()

collection_name = dbname["Energy Data"]
collection_name.insert_many(Pout.to_dict('records'))

#Creating collections for the DB
test_collection = collection_name.test.find()
#Inserting into DB
collection_name.test_collection.delete_many({"feedin_power_plant": df_vals})
collection_name.test_collection.insert_many(Pout.to_dict("records"))


# # if file does not exist write header 
# if not os.path.isfile('Pout.csv'):
#     Pout.to_csv('Pout.csv', header='column_names')
# else: # else it exists so append without writing the header
#     Pout.to_csv('Pout.csv', mode='a', header=False)

# df=pd.read_csv('Pout.csv')

from matplotlib.colors import PowerNorm
import pymongo
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import passkey
import requests
import config
from windpowerlib import ModelChain, WindTurbine, create_power_curve
import Forecast
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import altair as alt
from windpowerlib import data as wt

# Streamlit App Title


st.set_page_config(
    page_title="Wind Turbine Calculator")

st.title("Wind Turbine Analyser and Forecaster")

# st.write(""" ### Forecast Model for Lake Turkana Wind
# """)
@st.cache(ttl=3600, max_entries=10)
def get_mongo():
#Read in data from mongo DB documents
    client = pymongo.MongoClient("mongodb+srv://%s:%s@cluster0.r3enc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"% (
    passkey.username, passkey.password))

    db = client.EnergyData
    collection = db["Lake_Turkana"]
    #convert data to pandas dataframe
    data = pd.DataFrame(list(collection.find())).drop_duplicates(subset='Timestamp')
    #Change 'dt_txt to datetime and set it as index

    data['Timestamp']=pd.to_datetime(data['Timestamp'])
    data=data.set_index(data['Timestamp'])
    return data
data=get_mongo()
#Initiate selectbox for date selection of start and end dates
# StartDate=st.sidebar.selectbox("Start Date",data.index)#data.dt_txt)
# st.write(StartDate)

# EndDate=st.sidebar.selectbox("End Date",data.index)#data.dt_txt)
# st.write(EndDate)
st.sidebar.info("Select and Enter Calculation Parameters")
InputLatitude=st.sidebar.number_input(" Enter Latitude")
InputLongitude=st.sidebar.number_input(" Enter Longitude")
WindHeight=st.sidebar.number_input(" Wind MEasurement Height")
InputrughIndex=st.sidebar.number_input(" Enter Roughness Index")

lat = InputLatitude
lon = InputLongitude
urls = "https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&units=metric" % (
    lat, lon, config.api_key)

# Run requests from the API
jsonDatas = requests.get(urls).json()
#CreateDatabase.collection_name.delete_many({"feedin_power_plant": df_vals})

#CreateDatabase.collection_name.insert_many(jsonDatas['list'])
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
# Select fields that windpowerlib accepts as inputs
dat_weath = dat_weath[['dt_txt', 'speed', 'temp', 'pressure']]

# Rename columns
dat_weath = dat_weath.rename(
    columns={'speed': 'wind_speed', 'temp': 'temperature', 'pressure': 'pressure'})
# Set index
dat_weath=dat_weath.rename(columns={'dt_txt':'Timestamp'})
dat_weath = dat_weath.set_index('Timestamp')
weather_dat=dat_weath.copy().reset_index()


# set a value to roughness index and windspeed measurement height
dat_weath['roughness_length'] = InputrughIndex
dat_weath['height'] = WindHeight
# Input requires multilevel index
dat_weath = dat_weath.set_index('height', append=True).unstack('height')


################################################################################
# ----------------------------------------------------------------------------
# Windpowerlib has a library of wind turbines, if turbine does not exist, it can be created
# specification of  wind turbine
# #Created by defining nominal power, hub height, and power curve values
# (Note: power curve values and
# nominal power have to be in Watt)


@st.cache(ttl=3600, max_entries=10)
def turbinedata():
    #Select Turbine
    turbines = wt.get_turbine_types(print_out=False)
    #Select Turbine Manufacturer
    
    return turbines
turbines=turbinedata()
TurbineMake=turbines.manufacturer.drop_duplicates()

MakeSelect=st.sidebar.selectbox("Select Turbine Make",TurbineMake)#data.dt_txt)
st.write(MakeSelect)
TurbineModel= turbinedata()['turbine_type'].loc[turbinedata()['manufacturer']== MakeSelect]
ModelSelect=st.sidebar.selectbox("Select Turbine Model",TurbineModel)#data.dt_txt)
st.write(ModelSelect)


@st.cache(ttl=3600, max_entries=10)
def hubrange(a,b,c):
    min=a
    defaultval=b
    maxval=c
    return min,defaultval,maxval
min,defaultval,maxval= hubrange(0,0,100)
HubHeight=st.sidebar.slider("Select Hub Height",0,0,100)

TurbineChoice = {
    "turbine_type": ModelSelect,  # turbine type as in register
    "hub_height": HubHeight,  # in m
}
Turbine = WindTurbine(**TurbineChoice)

######################################################################
# -----------------------------------------------------------------------
# The ModelChain is a class that provides all necessary steps to calculate the power output of a wind turbine. When calling the 'run_model' method, first the wind speed and density (if necessary) at hub height are calculated and
#  then used to calculate the power output.
#   You can either use the default methods for the calculation steps,
#   as done for 'my_turbine', or choose different methods, as done for the 'e126'.
#    Of course, you can also use the default methods while only changing one or two of them,
#     as done for 'my_turbine2'.


# own specifications for ModelChain setup
# modelchain_data = {
#     'wind_speed_model': 'logarithmic',      # 'logarithmic' (default),
#                                             # 'hellman' or
#                                             # 'interpolation_extrapolation'
#     # 'barometric' (default), 'ideal_gas'
#     'density_model': 'ideal_gas',
#                                             #  or 'interpolation_extrapolation'
#     'temperature_model': 'linear_gradient',  # 'linear_gradient' (def.) or
#                                             # 'interpolation_extrapolation'
#     'power_output_model':
#         'power_coefficient_curve',          # 'power_curve' (default) or
#                                             # 'power_coefficient_curve'
#     'density_correction': True,             # False (default) or True
#     'obstacle_height': 0,                   # default: 0
#     'hellman_exp': None}                    # None (default) or None

mc_example_turbine = ModelChain(
    Turbine,
    wind_speed_model='hellman').run_model(dat_weath)
Turbine.power_output = mc_example_turbine.power_output

#######################################################33

Turbine.power_output = (Turbine.power_output)/10**6
Turbine.power_output
@st.cache()
def outputdat():

    Pout = Turbine.power_output.reset_index()
    Pout['timestamp_local'] = pd.to_datetime(Pout['Timestamp'])
    Pout.set_index('timestamp_local', inplace=True)
    #Drop "_id" column added by mongoDB as a document field identifier
    # Pout=Pout.drop(columns='_id')
    #Drop duplicates
    Pout=Pout.drop_duplicates(subset='Timestamp')
    return Pout
Pout=outputdat()

###################################################################

PowerPlot = px.line(Pout,
    x=Pout.index, y=Pout.feedin_power_plant,
    color_discrete_sequence=["red"],
    title='Forecast Power Production',
    labels={'feedin_power_plant': 'Power Output(MW)'},
    height=550,width=900)

st.plotly_chart(PowerPlot)

##################################################################################
Forecast.weather_dat=Forecast.weather_dat.drop_duplicates()
Forecast.weather_dat['date']=pd.to_datetime(Forecast.weather_dat['Timestamp'])
Forecast.weather_dat=Forecast.weather_dat.set_index('date')
# Forecast.weather_dat=Forecast.weather_dat[StartDate:EndDate]
WeatherPlot = px.line(Forecast.weather_dat,
    x=Forecast.weather_dat.Timestamp, y=Forecast.weather_dat.wind_speed,
    title='Site Wind Speed Over Time',
    labels={'dt_txt':'Date','wind_speed': 'Wind Speed(m/s)'},
    height=550,width=900)
WeatherPlot["layout"].pop("updatemenus")
# WeatherPlot.show()
#WeatherPlot["layout"].pop("updatemenus")

st.plotly_chart(WeatherPlot)


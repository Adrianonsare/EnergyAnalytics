from matplotlib.colors import PowerNorm
import pymongo
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import passkey
import Forecast
import plotly.express as px
import matplotlib.pyplot as plt
import altair as alt

# Streamlit App Title



st.title("Lake Turkana Wind Power")
st.write(""" ### Forecast Model for Lake Turkana Wind
""")



#Read in data from mongo DB documents
client = pymongo.MongoClient("mongodb+srv://%s:%s@cluster0.r3enc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"% (
    passkey.username, passkey.password))

db = client.EnergyData
collection = db["Lake_Turkana"]

#convert data to pandas dataframe
data = pd.DataFrame(list(collection.find())).drop_duplicates(subset='dt_txt')
#Change 'dt_txt to datetime and set it as index
data['date']=pd.to_datetime(data['dt_txt'])
data=data.set_index(data['date'])

#Initiate selectbox for date selection of start and end dates
StartDate=st.sidebar.selectbox("Start Date",data.index)#data.dt_txt)
st.write(StartDate)

EndDate=st.sidebar.selectbox("End Date",data.index)#data.dt_txt)
st.write(EndDate)

#Drop "_id" column added by mongoDB as a document field identifier
data=data.drop(columns='_id')
#Drop duplicates
data=data.drop_duplicates(subset='dt_txt')

# Plot power output using plotly  express
PowerPlot = px.line(data,
    x=data.index, y=data.feedin_power_plant,
    color_discrete_sequence=["red"],
    title='Forecast Power Production',
    labels={'dt_txt':'Date','feedin_power_plant': 'Power Output(MW)'},
    height=550,width=900)

st.plotly_chart(PowerPlot)


#Plot Wind speeds
# st.write('''### Plot of Weather Data
# ''')
Forecast.weather_dat=Forecast.weather_dat.drop_duplicates()
Forecast.weather_dat['date']=pd.to_datetime(Forecast.weather_dat['dt_txt'])
Forecast.weather_dat=Forecast.weather_dat.set_index('date')
# Forecast.weather_dat=Forecast.weather_dat[StartDate:EndDate]
WeatherPlot = px.line(Forecast.weather_dat,
    x=Forecast.weather_dat.dt_txt, y=Forecast.weather_dat.wind_speed,
    title='Site Wind Speed Over Time',
    labels={'dt_txt':'Date','wind_speed': 'Wind Speed(m/s)'},
    height=550,width=900)
#WeatherPlot["layout"].pop("updatemenus")

st.plotly_chart(WeatherPlot)


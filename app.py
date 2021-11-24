import pymongo
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import passkey
import Forecast
import plotly.express as px
import matplotlib.pyplot as plt

st.title("Lake Turkana Wind Power")
st.write(""" ## Forecast Model for Lake Turkana Wind
""")

client = pymongo.MongoClient("mongodb+srv://%s:%s@cluster0.r3enc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"% (
    passkey.username, passkey.password))

db = client.EnergyData
collection = db["Lake_Turkana"]
data = pd.DataFrame(list(collection.find()))

data['dt_txt']=pd.to_datetime(data['dt_txt'])

data=data.set_index(data['dt_txt'])
StartDate=st.sidebar.selectbox("Start Date",data.index)#data.dt_txt)
st.write(StartDate)

EndDate=st.sidebar.selectbox("End Date",data.index)#data.dt_txt)
st.write(EndDate)
data=data.drop(columns='_id')#px.line(data,x=data.index,y='feedin_power_plant',
#title="Energy Forecast Per Day")
data=data.drop_duplicates()
data=data[StartDate :EndDate]
x = data.index
y = data.feedin_power_plant
fig, ax = plt.subplots()
ax.plot(x, y)
ax.tick_params(axis='x',labelrotation=90)

st.pyplot(fig)

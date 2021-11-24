import pymongo
import pandas as pd
from pymongo import MongoClient
import streamlit as st
import passkey


client = pymongo.MongoClient("mongodb+srv://%s:%s@cluster0.r3enc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"% (
    passkey.username, passkey.password))

db = client.EnergyData
collection = db["Lake_Turkana"]
data = pd.DataFrame(list(collection.find()))


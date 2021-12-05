import pandas as pd
import streamlit as st
# import passkey
import requests
# import config
from windpowerlib import ModelChain, WindTurbine, create_power_curve,TurbineClusterModelChain, WindTurbineCluster, WindFarm
import plotly.graph_objects as go
import plotly.express as px
import altair as alt
from windpowerlib import data as wt
import os 

# lat = 2
# lon = 35.5
# api_key=st.secrets["api_key"]
# urls = "https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&units=standard" % (lat, lon,api_key)

# Streamlit App Title
st.title("Wind Farm Analyser")
st.markdown("""
This application allows users to estimate and forecast power output from proposed 
wind farm sites. It makes use of the followign resurces.
* **Windpowerlib Library** : This is a python library which makes use of turbine data and weather foreast data
 to predict wind turbine and wind farm output.
* **Open Weather API** : This is an interface which provided weather forecasts for geoloecated places.
""")
st.sidebar.info("Select and Enter Calculation Parameters")

#Import turbine Database from Records
def turbinedata():
    #Select Turbine
    turbines = wt.get_turbine_types(print_out=False)
    
    
    return turbines
turbines=turbinedata()
#Select Unique Turbine Manufacturer
TurbineMake=turbines.manufacturer.drop_duplicates()

# Select box to allow user to select turbine make and model
col1, col2 = st.columns(2)
with col1:
    MakeSelect=st.selectbox("Select Turbine Make",TurbineMake)
    st.write(MakeSelect)
with col2:
    TurbineModel= turbines ['turbine_type'].loc[turbines ['manufacturer']== MakeSelect]
    ModelSelect=st.selectbox("Select Turbine Model",TurbineModel)
    st.write(ModelSelect)

#Hub Height Selector
@st.cache
def hubrange(a,b,c):
    minval=a
    defaultval=b
    maxval=c
    return minval,defaultval,maxval
minval,defaultval,maxval= hubrange(0,0,100)

#####################################################################333333
myForm=st.sidebar.form(key="my_form")
WindFarmName=myForm.text_input(" Enter Farm Name")
InputLatitude=myForm.number_input(" Enter Latitude")
InputLongitude=myForm.number_input(" Enter Longitude")
InputRoughLength=myForm.number_input(" Enter Roughness Length")
NoTurbines=myForm.number_input(" Enter Turbine Qty")
WindHeight=myForm.number_input(" Wind Measurement Height")
HubHeight=myForm.slider("Select Hub Height",minval,defaultval,maxval)
FarmEfficiency=myForm.number_input(" Farm Efficiency")
Calculate=myForm.form_submit_button("Calculate")


#If the user clicks the calculate button, then the rest of the script is executed
if Calculate:
    #Load Weather Data
    @st.cache
    def loadWeatherData():
        lat = InputLatitude
        lon = InputLongitude
        urls = "https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=686a8268d2d60adfa1efd1b0f3d7ffe5&units=standard" % (lat, lon)
        print(urls)
        # Run requests from the API
        jsonDatas = requests.get(urls).json()
        dat_weath = pd.DataFrame(jsonDatas['list'])

        # Some of the fields have values in dictionary format
        # These need to be converted to pandas series
        # and then concatenated into the original dataframe
        main = dat_weath.main.apply(pd.Series)
        wind = dat_weath.wind.apply(pd.Series)
        weather = dat_weath.weather.apply(pd.Series)
        WeatherPart = pd.concat([dat_weath, main, wind, weather], axis=1).drop(['main', 'wind',
                                                                    'weather', 'clouds', 'sys', 0], axis=1)
        # Data Preparation
        # Select fields that windpowerlib accepts as inputs
        dat_weath = WeatherPart[['dt_txt', 'speed', 'temp', 'pressure']]
        # Rename columns
        dat_weath = dat_weath.rename(
        columns={'speed': 'wind_speed', 'temp': 'temperature', 'pressure': 'pressure'})
        # Set index
        dat_weath=dat_weath.rename(columns={'dt_txt':'Timestamp'})
        dat_weath = dat_weath.set_index('Timestamp')        
        # set a value to windspeed measurement height
        #Also set value for roughness Length
        dat_weath['roughness_length'] = InputRoughLength
        dat_weath['height'] = WindHeight
        # Input requires multilevel index
        dat_weath = dat_weath.set_index('height', append=True).unstack('height')
        return dat_weath
    dat_weath=loadWeatherData()

    ################################################################################
    # ----------------------------------------------------------------------------
    # Windpowerlib has a library of wind turbines, if turbine does not exist, it can be created
    # specification of  wind turbine
    # #Created by defining nominal power, hub height, and power curve values
    # (Note: power curve values and nominal power have to be in Watt)

    TurbineChoice = {
        "turbine_type": ModelSelect,  # turbine type as selected by user
        "hub_height": HubHeight,  # in m as selected by user
    }
    Turbine = WindTurbine(**TurbineChoice)#initiating turbine object
    

    ##########################################################################

    # specification of wind farm data where turbine fleet is provided in a
    # pandas.DataFrame
    # The number of turbines is specified by user

    FarmData= {
        'name': WindFarmName,
        'wind_turbine_fleet': [Turbine.to_group(NoTurbines)],
        'efficiency': FarmEfficiency}

    # initialize WindFarm object
    WindFarmCalc= WindFarm(**FarmData)

    # power output calculation for user farm
    # initialize TurbineClusterModelChain with default parameters and use
    # run_model method to calculate power output
    mc_example_farm = TurbineClusterModelChain(WindFarmCalc).run_model(dat_weath)
    # write power output time series to WindFarm object
    WindFarmCalc.power_output = (mc_example_farm.power_output)/10**6

    st.header("Analysis Results", anchor=None)
  
    # Process power output time series into pandas dataframe
    def outputdat():

        Pout = WindFarmCalc.power_output.reset_index()
        Pout['timestamp_local'] = pd.to_datetime(Pout['Timestamp'])
        Pout.set_index('timestamp_local', inplace=True)
        return Pout
    Pout=outputdat()
    colz1,colz2,colz3,colz4=st.columns(4)

    #Obtain Turbine Rating
    TurbineRating=int(TurbineChoice.get('turbine_type').split('/')[1])
    #Plot select metrics
    with colz1:
        MedianPower=st.metric(label="Av. Forecast Power(MW)",value=round(Pout['feedin_power_plant'].mean(),2))
    with colz2:
        CapcityFactor=st.metric(label="Capacity Factor",value=round((1000*Pout['feedin_power_plant'].median()/(NoTurbines*TurbineRating)),2))
    with colz3:
        PoutDisp=st.metric(label="Max Forecast Power(MW)",value=round(Pout['feedin_power_plant'].max(),2))
    with colz4:
        PRating=st.metric(label="Rated Capacity(MW)",value=round(NoTurbines*TurbineRating/10**3,2))


    ###########################################################################

    #In this section, several plots are made,including power output,wind speed,correlation matrix,
    # Power output histogram

    c = alt.Chart(Pout).mark_area(opacity=0.7, color='#FF0000').encode(
    x='Timestamp', y='feedin_power_plant').properties(
    width=700,
    height=450,title='Forecast Power Production for '+str(WindFarmName)+' Wind Farm')
    st.write(c)
#######################################################################################

    #Combine weather data with power output data   
    reweather=pd.melt(dat_weath.reset_index(), col_level=0, id_vars=['Timestamp','wind_speed','temperature','pressure'])
    
    #Wind speed Plot
    SpeedPlot = px.line(reweather,
        x=reweather.Timestamp, y=reweather.wind_speed,
        color_discrete_sequence=["red"],
        title='Wind Speed Forecast for '+str(WindFarmName)+' Wind Farm',
        labels={'wind_speed': 'Wind Speed(m/s)'},height=500,
        width=800)
    st.write(SpeedPlot)

    combined=pd.merge(Pout,reweather,on=['Timestamp']).drop(columns='value')
    combined['lat']=InputLatitude
    combined ['lon']=InputLongitude

    cols1,cols2=st.columns(2)
    corr=combined.corr()

    
    #Correlation matrix
    corrplot = px.imshow(corr)
    st.markdown(""" #### Correlation Matrix of Power and Weather Variables""")
    st.write(corrplot)
    with cols1:
        powerhist= alt.Chart(combined).mark_bar().encode(
            alt.X("feedin_power_plant:Q", bin=True),
            y='count()',
)       
        st.markdown(""" #### Energy Output Histogram """)
        st.write(powerhist)
    with cols2:
        scatChart=alt.Chart(combined).mark_circle(
    color='red',
    opacity=0.3
).encode(
    x='wind_speed:Q',
    y='feedin_power_plant:Q'
)
        st.markdown(""" #### Wind Farm Power Curve """)
        st.write(scatChart)
    st.map(combined)
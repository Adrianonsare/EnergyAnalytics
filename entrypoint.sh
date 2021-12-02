#!/bin/bash
#parameter from shell
parameter_directory="$1"
# Python script 1
python config.py --outpath $parameter_directory

# Python script 2
python passkey.py $parameter_directory 

# Python script 3
python Forecast.py $parameter_directory

#Python script 4
python app.py $parameter_directory


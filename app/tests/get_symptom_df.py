#!/usr/bin/python3

# Test mongo api module

# Need to make sure mongodb is running 
#  and accessible at port 27017

import pytest
import os,sys
import re
import pymongo
import pandas as pd



# Need to have PYTHONPATH defined

PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or \
    "../.."

if not os.environ.get('PYTHONPATH'):
    PYTHONPATH = os.path.join(
        PROJECT_ROOT,
        "app"
    )
    sys.path.append(PYTHONPATH)


from main import api, process
from main import db as DB



def get_symptoms_encounters_df(db,symptoms_list):
    df = process.symptoms_encounters_df(db,symptoms_list)
    return df


if __name__ == "__main__":
    client = DB.connect()
    symptoms_db = client.symptoms_db
    symptoms_list = ["Fever"]
    df = get_symptoms_encounters_df(
        symptoms_db,
        symptoms_list
    )
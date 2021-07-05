#!/usr/bin/python3

# Test mongo process module

# Need to make sure mongodb is running 
#  and accessible at port 27017

import pytest
import os,sys
import re
import pymongo
import pandas as pd
import numpy as np
from datetime import datetime,timezone,timedelta



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

## Use api connect as fixture
@pytest.fixture(scope="module")
def db():
    client = DB.connect()
    symptoms_db = client.symptoms_db
    return symptoms_db

@pytest.fixture(scope="module")
def symptom_pathology_dataframe(db):
    client = DB.connect()
    symptoms_list = ["Fever","Cough"]
    df = process.andsymptoms_pathology_df(db,symptoms_list)
    return df


@pytest.mark.parametrize(
    ["symptoms_list"],
    [
        (["Fever"],)
    ]
)
def test_andsymptoms_pathology_df(db,symptoms_list):
    df = process.andsymptoms_pathology_df(db,symptoms_list)
    assert isinstance(df,pd.core.frame.DataFrame)
    for symptom in symptoms_list:
        assert all(df['symptoms_texts_severities'].str.\
            contains(symptom))

@pytest.mark.parametrize(
    ["symptoms_list"],
    [
        (["Fever"],)
    ]
)
def test_orsymptoms_pathology_df(db,symptoms_list):
    df = process.orsymptoms_pathology_df(db,symptoms_list)
    assert isinstance(df,pd.core.frame.DataFrame)
    for symptom in symptoms_list:
        assert all(df['symptoms_texts_severities'].str.\
            contains(symptom))


@pytest.mark.parametrize(
    ["pathology"],
    [
        ("COVID-19",),
        ("Acute allergic reaction",),
        ("Joint pain (finding)",)
    ]
)
def test_pathology_stats(db,pathology):
    pathology_stats = process.pathology_stats(db,pathology)
    assert isinstance(pathology_stats,dict)
    assert 'age' in pathology_stats
    assert isinstance(pathology_stats['symptoms'],dict)


def test_all_stats(db,symptom_pathology_dataframe):
    stats = process.all_stats(db,symptom_pathology_dataframe)
    all_pathologies = symptom_pathology_dataframe['pathology'].unique()
    assert all([p in stats for p in all_pathologies])
    assert len(all_pathologies) == len(stats)
    assert sum([p['freq'] for p in stats.values()]) > 0



#!/usr/bin/python3

# Test mongo api module

# Need to make sure mongodb is running 
#  and accessible at port 27017

import pytest
import os,sys
import re
import pymongo
import pandas as pd
from datetime import datetime
import json


# Need to have PYTHONPATH defined

PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or \
    "../.."

if not os.environ.get('PYTHONPATH'):
    PYTHONPATH = os.path.join(
        PROJECT_ROOT,
        "app"
    )
    sys.path.append(PYTHONPATH)


from main import api
from main import db as DB
from main import _process_helpers as ph
import json


SYMPTOM_OBJS_LEN = 100

## Use api connect as fixture
@pytest.fixture(scope="module")
def db():
    client = DB.connect()
    symptoms_db = client.symptoms_db
    return symptoms_db

@pytest.fixture(scope="module")
def encounter_obj(db):
    encounter = db.Encounter.find_one()
    return encounter

@pytest.fixture(scope="module")
def patient_obj(db):
    patient = db.Patient.find_one()
    return patient

@pytest.fixture(scope="module")
def condition_obj(db):
    condition = db.Condition.find_one()
    return condition

@pytest.fixture(scope="module")
def symptom_objs(db):
    objs_cursor = db.symptoms.find().limit(SYMPTOM_OBJS_LEN)
    objs = list(objs_cursor)
    return objs

@pytest.fixture(scope="module")
def symptom_obj():
    symptom_json_file = os.path.join(
        PROJECT_ROOT,
        "app",
        "tests",
        "symptoms_obj.json"
    )
    with open(symptom_json_file,"r") as f:
        symptomObj = json.load(f)
    return symptomObj


def test_get_encounter_ids(db):
    encounters_dict = api.get_encounters_with_symptoms(
        db,
        ["Fever"]
    )
    encounter_ids = ph._get_encounter_ids(encounters_dict)
    assert isinstance(encounter_ids,list)
    assert len(encounter_ids) >= 0
    assert all([re.match(r"^urn:uuid:.*$",e_id) for e_id in \
        encounter_ids])

def test_get_encounter_types(encounter_obj):
    etype_codes,etype_disps = ph._get_encounter_types(encounter_obj)
    print()
    print(f"code: {etype_codes}")
    print(f"display: {etype_disps}")
    assert isinstance(etype_codes,str)
    assert isinstance(etype_disps,str)

def test_get_reasonCodes(encounter_obj):
    rc_codes,rc_disps = ph._get_reasonCodes(encounter_obj)
    print()
    print(f"code: {rc_codes}")
    print(f"display: {rc_disps}")
    assert isinstance(rc_codes,str)
    assert isinstance(rc_disps,str)

def test_get_encounter_period(encounter_obj):
    start,end = ph._get_encounter_period(encounter_obj)
    print()
    print(f"Start: {start.strftime('%m/%d/%Y %H:%M')}")
    print(f"End: {end.strftime('%m/%d/%Y %H:%M')}")
    assert isinstance(start,datetime)
    assert isinstance(end,datetime)
    assert end > start


def test_get_encounter_status(encounter_obj):
    es = ph._get_encounter_status(encounter_obj)
    print(es)
    assert isinstance(es,str)

def test_get_encounter_class(encounter_obj):
    ec = ph._get_encounter_class(encounter_obj)
    print(ec)
    assert isinstance(ec,str)

def test_get_patient_gender(patient_obj):
    gender = ph._get_patient_gender(patient_obj)
    assert gender in ["male","female"]

def test_get_patient_birthDate(patient_obj):
    birthdate = ph._get_patient_birthDate(patient_obj)
    assert isinstance(birthdate,datetime)

def test_get_condition_code(condition_obj):
    comma_sep_codes, cond_text = ph._get_condition_code(\
    condition_obj)
    assert isinstance(comma_sep_codes,str)
    assert isinstance(cond_text,str)

def test_get_root_cause(db,encounter_obj):
    conds = api.get_encounter_conditions(
        db,
        encounter_obj['fullUrl']
    )
    if len(conds) > 0:
        root_cause = conds[-1]['resource']['code']['text']
        rc = ph._get_root_cause(conds)
        assert rc == root_cause

def test_symptom_patient_id(symptom_obj):
    patient_id = ph._symptom_patient_id(symptom_obj)
    assert isinstance(patient_id, str)
    assert patient_id[0:9] == "urn:uuid:"

def test_symptom_patient_gender(symptom_obj):
    patient_gender = ph._symptom_patient_gender(symptom_obj)
    assert isinstance(patient_gender,str)
    assert patient_gender in ["M","F"]

def test_symptom_patient_age(symptom_obj):
    patient_age = ph._symptom_patient_age(symptom_obj)
    assert isinstance(patient_age,int)
    assert patient_age == 4

def test_symptom_texts_severities(symptom_obj):
    sts = ph._symptom_texts_severities(symptom_obj)
    assert isinstance(sts,str)
    assert "Cough:1" in sts

def test_symptom_pathology(symptom_obj):
    pathology = ph._symptom_pathology(symptom_obj)
    assert pathology == "Acute viral pharyngitis (disorder)"

def test_df_from_symptoms(symptom_objs):
    df = ph.df_from_symptoms(symptom_objs)
    assert(df.shape[0]) == len(symptom_objs)
    assert len(symptom_objs) == SYMPTOM_OBJS_LEN
    assert isinstance(df,pd.core.frame.DataFrame)

@pytest.mark.parametrize(
    ["pathology"],
    [
        ("COVID-19",),
        ("Acute allergic reaction",),
        ("Joint pain (finding)",)
    ]
)
def test_pathology_stats_from_symptoms(db,pathology):
    symptom_objs = api.pathology_symptoms(db,pathology)
    pathology_stats = ph.pathology_stats_from_symptoms(symptom_objs)
    print(len(symptom_objs))
    assert sum(pathology_stats['age'].values()) == len(symptom_objs)
    assert sum(pathology_stats['gender'].values()) == len(symptom_objs)
    assert pathology_stats['count'] == len(symptom_objs)

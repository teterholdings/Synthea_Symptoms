#!/usr/bin/python3

# Test mongo api module

# Need to make sure mongodb is running 
#  and accessible at port 27017

import pytest
import os,sys
import re
import pymongo


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


## Use api connect as fixture
@pytest.fixture(scope="module")
def db():
    client = DB.connect()
    symptoms_db = client.symptoms_db
    return symptoms_db

def test_db_connect(db):
    collections = db.list_collection_names()
    for q in collections:
        print(q)
    assert "Condition" in collections
    assert "Encounter" in collections
    assert "Observation" in collections
    assert "Procedure" in collections


def test_all_symptoms(db):
    symptom_list = api.get_all_symptoms(db)
    assert isinstance(symptom_list,list)
    for symptom in symptom_list:
        print(symptom)

def test_all_symptoms_old(db):
    symptom_list = api.get_all_symptoms_old(db)
    assert isinstance(symptom_list,list)
    for symptom in symptom_list:
        print(symptom)

def test_diagnosticReport_data(db):
    data_str = api.get_diagnosticReport_data(
        db,
        {
            "resource.category.coding.code":"34117-2"
        }
    )
    assert len(data_str) > 0
    print(data_str)


def test_all_genders(db):
    gender_list = api.get_all_genders(db)
    assert 'male' in gender_list
    assert 'female' in gender_list

def test_symptom_genders(db):
    gender_list = api.get_symptom_genders(db)
    assert 'M' in gender_list
    assert 'F' in gender_list

def test_all_pathologies(db):
    pathology_list = api.get_all_pathologies(db)
    assert 'Viral sinusitis (disorder)' in pathology_list
    assert 'Normal pregnancy' in pathology_list

def test_encounters_with_symptoms(db):
    symptoms_list = api.get_all_symptoms_old(db)
    encounter_dict = api.get_encounters_with_symptoms(
        db,
        [symptoms_list[0]]
    )
    assert symptoms_list[0] in encounter_dict
    assert len(encounter_dict[symptoms_list[0]]) > 0
    for encounter in encounter_dict[symptoms_list[0]]:
        assert re.match(
            r"^urn:uuid:.*$",
            encounter
        )
    print(encounter_dict[symptoms_list[0]][0])
    if len(symptoms_list) > 1:
        encounter_dict = api.get_encounters_with_symptoms(
            db,
            symptoms_list[0:2]
        )
        assert symptoms_list[0] in encounter_dict
        assert len(encounter_dict[symptoms_list[0]]) > 0
        assert symptoms_list[1] in encounter_dict
        assert len(encounter_dict[symptoms_list[1]]) > 0
        for symptom in symptoms_list[0:2]:
            for encounter in encounter_dict[symptom]:
                assert re.match(
                    r"^urn:uuid:.*$",
                    encounter
                )



@pytest.mark.parametrize(
    ["projection"],
    [
        (None,),
        ({},),
        ({"resource.subject":1},)
    ]
)
def test_encounter_info(db,projection):
    e = db.Encounter.find_one()
    e_uuid = e['fullUrl']
    encounter_info = api.get_encounter_info(db,e_uuid,
        projection)
    if projection is None:
        assert encounter_info['fullUrl'] == e_uuid
        assert "Encounter" in encounter_info['resource']['resourceType']
        assert "subject" in encounter_info['resource']
    else:
        for field in projection:
            field_list = field.split(".")
            i = 0
            assert field_list[i] in encounter_info
            while i < (len(field_list) - 1):
                obj = encounter_info[field_list[i]]
                i += 1
                assert field_list[i] in obj


@pytest.mark.parametrize(
    ["projection"],
    [
        (None,),
        ({},),
        ({
            "resource.gender":1,
            "fullUrl":1,
            # "resource.birthDate":1
        },)
    ]
)
def test_patient_info(db,projection):
    p = db.Patient.find_one()
    p_uuid = p['fullUrl']
    patient_info = api.get_patient_info(db,p_uuid,
        projection)
    if projection is None:
        assert patient_info['fullUrl'] == p_uuid
        assert "gender" in patient_info['resource']
        assert "birthDate" in patient_info['resource']
        assert patient_info['resource']['resourceType'] == "Patient"
    else:
        for field in projection:
            field_list = field.split(".")
            i = 0
            assert field_list[i] in patient_info
            while i < (len(field_list) - 1):
                obj = patient_info[field_list[i]]
                i += 1
                assert field_list[i] in obj



@pytest.mark.parametrize(
    ["projection"],
    [
        (None,),
        ({},),
        ({"resource.subject":1},)
    ]
)
def test_mult_encounter_info(db,projection):
    c = db.Encounter.find()
    e_uuid_list = []
    for _ in range(3):
        e = next(c)
        e_uuid_list.append(e['fullUrl'])
    encounter_cursor = api.\
        get_multiple_encounter_info(db,e_uuid_list,\
            projection)
    assert isinstance(encounter_cursor,
        pymongo.cursor.Cursor)
    for _ in range(3):
        encounter_info = next(encounter_cursor)
        if projection is None:
            assert encounter_info['fullUrl'] in e_uuid_list
            assert "Encounter" in encounter_info['resource']\
                ['resourceType']
            assert "subject" in encounter_info['resource']
        else:
            for field in projection:
                field_list = field.split(".")
                i = 0
                assert field_list[i] in encounter_info
                while i < (len(field_list)-1):
                    obj = encounter_info[field_list[i]]
                    i+=1
                    assert field_list[i] in obj


@pytest.mark.parametrize(
    ["projection"],
    [
        (None,),
        ({},),
        ({"resource.gender":1,
            "fullUrl":1,
            "resource.birthDate":1},)
    ]
)
def test_mult_patient_info(db,projection):
    c = db.Patient.find()
    p_uuid_list = []
    for _ in range(3):
        p = next(c)
        p_uuid_list.append(p['fullUrl'])
    patient_cursor = api.\
        get_multiple_patient_info(db,p_uuid_list,projection)
    assert isinstance(patient_cursor,
        pymongo.cursor.Cursor)
    for _ in range(3):
        patient_info = next(patient_cursor)
        if projection is None:
            assert patient_info['fullUrl'] in p_uuid_list
            assert "gender" in patient_info['resource']
            assert "birthDate" in patient_info['resource'] 
            assert patient_info['resource']['resourceType']\
                == "Patient"
        else:
            for field in projection:
                field_list = field.split(".")
                i = 0
                assert field_list[i] in patient_info
                while i < (len(field_list)-1):
                    obj = patient_info[field_list[i]]
                    i+=1
                    assert field_list[i] in obj


@pytest.mark.parametrize(
    ["projection"],
    [
        (None,),
        ({},),
        ({"resource.subject":1},)
    ]
)
def test_encounter_conditions(db,projection):
    encounter = db.Encounter.find_one()
    encounter_url = encounter['fullUrl']
    conditions = api.get_encounter_conditions(
        db,
        encounter_url,
        projection
    )
    print()
    print(len(conditions))
    for c in conditions:
        print(c['resource']['code']['text'])
    assert all([c['resource']['encounter']['reference'] == \
        encounter_url for c in conditions])


@pytest.mark.parametrize(
    ["symptom_list"],
    [
        (["Cough"],),
        (["Cough","Swollen Lymph Nodes","Fatigue","Decreased Appetite"],)
    ]
)
def test_andsymptom_objs(db,symptom_list):
    symptom_objs = api.get_andsymptoms_objs(db,symptom_list)
    assert isinstance(symptom_objs, list)
    print(len(symptom_objs))
    for symptom_obj in symptom_objs:
        symptom_texts = [s['text'] for s in \
            symptom_obj['resource']['symptoms']]
        assert all([symptom in symptom_texts for \
            symptom in symptom_list])

@pytest.mark.parametrize(
    ["symptom_list","age","gender"],
    [
        (["Cough"],22,"M"),
        (["Cough","Swollen Lymph Nodes","Fatigue","Decreased Appetite"],
            45,"F")
    ]
)
def test_andsymptom_objs_agegender(db,symptom_list,age,gender):
    symptom_objs = api.get_andsymptoms_objs(db,symptom_list,\
        age_begin=age,gender=gender)
    assert isinstance(symptom_objs, list)
    print(len(symptom_objs))
    assert all([s['resource']['gender'] == gender for \
        s in symptom_objs])
    assert all([s['resource']['age_begin'] == age for \
        s in symptom_objs])
    for symptom_obj in symptom_objs:
        symptom_texts = [s['text'] for s in \
            symptom_obj['resource']['symptoms']]
        assert all([symptom in symptom_texts for \
            symptom in symptom_list])


@pytest.mark.parametrize(
    ["symptom_list"],
    [
        (["Cough"],),
        (["Cough","Swollen Lymph Nodes","Fatigue",
            "Decreased Appetite"],)
    ]
)
def test_orsymptom_objs(db,symptom_list):
    symptom_objs = api.get_orsymptoms_objs(db,symptom_list)
    assert isinstance(symptom_objs, list)
    print(len(symptom_objs))
    for symptom_obj in symptom_objs:
        symptom_texts = [s['text'] for s in \
            symptom_obj['resource']['symptoms']]
        assert any([symptom in symptom_texts for \
            symptom in symptom_list])

@pytest.mark.parametrize(
    ["symptom_list","age","gender"],
    [
        (["Cough"],22,"M"),
        (["Cough","Swollen Lymph Nodes","Fatigue","Decreased Appetite"],
            45,"F")
    ]
)
def test_orsymptom_objs_agegender(db,symptom_list,age,gender):
    symptom_objs = api.get_orsymptoms_objs(db,symptom_list,\
        age_begin=age,gender=gender)
    assert isinstance(symptom_objs, list)
    print(len(symptom_objs))
    assert all([s['resource']['gender'] == gender for \
        s in symptom_objs])
    assert all([s['resource']['age_begin'] == age for s in \
        symptom_objs])
    for symptom_obj in symptom_objs:
        symptom_texts = [s['text'] for s in \
            symptom_obj['resource']['symptoms']]
        assert any([symptom in symptom_texts for \
            symptom in symptom_list])


@pytest.mark.parametrize(
    ["pathology"],
    [
        ("COVID-19",),
        ("Acute allergic reaction",),
        ("Joint pain (finding)",)
    ]
)
def test_pathology_symptoms(db,pathology):
    symptoms_objs = api.pathology_symptoms(db,pathology)
    print(len(symptoms_objs))
    assert all([p['resource']['pathology'] == pathology \
        for p in symptoms_objs])

@pytest.mark.parametrize(
    ["pathology","age","gender"],
    [
        ("COVID-19",71,"M"),
        ("Acute allergic reaction",44,"F"),
        ("Joint pain (finding)",58,"F")
    ]
)
def test_pathology_symptoms_agegender(db,pathology,age,gender):
    symptoms_objs = api.pathology_symptoms(db,pathology,\
        age_begin=age,gender=gender)
    print(len(symptoms_objs))
    assert all([p['resource']['gender'] == gender for p \
        in symptoms_objs])
    assert all([p['resource']['age_begin'] == age for p \
        in symptoms_objs])
    assert all([p['resource']['pathology'] == pathology \
        for p in symptoms_objs])

@pytest.mark.parametrize(
    ['query'],
    [
        (None,),
        ({},),
        ({"resource.gender":"F"},),
        ({"resource.pathology":"Acute allergic reaction"},)
    ]
)
def test_symptom_collection_count(db,query):
    count = api.symtpom_collection_count(db,query)
    assert isinstance(count,int)
    assert count >= 0
    print(count)


def test_symptom_collection_count_est(db):
    count = api.symtpom_collection_count_est(db)
    assert isinstance(count,int)
    assert count > 0
    print(count)

def test_age_gender_pathology_counts(db):
    agp_counts = api.age_gender_pathology_counts(db)
    assert agp_counts[(24,'F','Normal pregnancy')] > 0


@pytest.mark.parametrize(
    ['symptom'],
    [
        ('Cough',)
    ]
)
def test_pathology_symptom_severity_counts(db,symptom):
    pss_counts = api.pathology_symptom_severity_counts(db,symptom)
    assert pss_counts[('Viral sinusitis (disorder)',True,1)] > 0
    assert pss_counts[('Normal pregnancy',False,0)] > 0

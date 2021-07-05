#!/usr/bin/python3

import pymongo
import json
import os,sys
from datetime import datetime
import re
import pandas as pd
import uuid



def get_patient_by_id(db_cxn,patient_id):
    patient = db_cxn.Patient.find_one({"fullUrl":patient_id})
    return patient

def str2datetime(input_str):
    fixed_str = re.sub(r"([+,-][0-9]{2}):",r"\1",input_str)
    dt = datetime.strptime(fixed_str,"%Y-%m-%dT%H:%M:%S%z")
    return dt

def get_patient_pathology_encounters(db_cxn,patient_id,pathology):
    conditions = db_cxn.Condition.find(
        {
            "resource.subject.reference": patient_id,
            "resource.code.text": pathology
        }
    )
    cond_list = list(conditions)
    if len(cond_list) > 0:
        onset_dts = [str2datetime(cond['resource']['onsetDateTime'])\
            for cond in cond_list]
        output = [
            {
                'datetime':o,
                'condition':cond_list[i]
            } for i,o in enumerate(onset_dts)
        ]
        output.sort(key=lambda z: z['datetime'])
    else:
        output = []
    return output

def age_in_years(encounter_dt, birthDate):
    year1 = encounter_dt.year
    year0 = birthDate.year
    if (encounter_dt.month == 2) and (encounter_dt.day == 29):
        encounter_dt = encounter_dt.replace(month=3,day=1)
    if encounter_dt.month > birthDate.month:
        age = year1 - year0
    elif (encounter_dt.month == birthDate.month) and \
        (encounter_dt.day >= birthDate.day):
        age = year1 - year0
    else:
        age = year1 - year0 - 1
    return age

def find_symptoms_condition(db_cxn,symptom_row,rep=0):
    patient_id = f"urn:uuid:{symptom_row['PATIENT']}"
    age_begin = symptom_row['AGE_BEGIN']
    pathology = symptom_row['PATHOLOGY']
    patient_obj = get_patient_by_id(db_cxn,patient_id)
    conditions = get_patient_pathology_encounters(db_cxn,patient_id,\
        pathology)
    patient_birthDate = datetime.strptime(patient_obj['resource']\
        ['birthDate'],"%Y-%m-%d")
    ages = [age_in_years(cond['datetime'],patient_birthDate) \
            for cond in conditions]
    agecheck_bool = [a >= age_begin for a in ages]
    if any(agecheck_bool):
        first_cond_index = agecheck_bool.index(True)
        cond_index = min(first_cond_index + rep,len(agecheck_bool)-1)
        cond_out = conditions[cond_index]['condition']
    else:
        cond_out = {
            'fullUrl': '[None]',
            'resource': {
                'encounter':{
                    'reference': '[None]'
                }
            }
        }
    return cond_out

def create_symptom_entry(symptom_row,condition):
    symptoms = symptom_row['SYMPTOMS']
    if symptom_row['NUM_SYMPTOMS'] > 0:
        symptoms_list_0 = symptoms.split(";")
        symptoms_list_1 = [s.split(":") for s in symptoms_list_0]
    else:
        symptoms_list_0 = []
        symptoms_list_1 = []
    for i in range(len(symptoms_list_1)):
        while len(symptoms_list_1[i]) < 3:
            symptoms_list_1[i].append(0)
    output_dict = {
        "fullUrl": f"urn:uuid:{uuid.uuid4()}",
        "resource": {
            "symptoms":[
                {
                    "text": s[0],
                    "severity": s[1],
                    "duration": s[2]
                }
                for s in symptoms_list_1
            ],
            "subject":{
                "reference": f"urn:uuid:{symptom_row['PATIENT']}"
            },
            "age_begin": int(symptom_row['AGE_BEGIN']),
            "age_end": int(symptom_row['AGE_END']) if \
                symptom_row['AGE_END'] == symptom_row['AGE_END']\
                else int(-1),
            "pathology": symptom_row['PATHOLOGY'],
            "gender": symptom_row['GENDER'],
            "race": symptom_row['RACE'],
            "ethnicity": symptom_row['ETHNICITY'],
            "num_symptoms": int(symptom_row['NUM_SYMPTOMS']),
            "encounter": {
                "reference": condition['resource']['encounter']\
                    ['reference']
            },
            "condition":{
                "reference": condition['fullUrl']
            }
        }
    }
    return output_dict

def load_symptoms(db_cxn):
    symptoms_df = pd.read_csv(SYMPTOMS_CSV)
    patient_id = 'none'
    pathology = 'none'
    age = -1
    rep = 0
    symptoms = db_cxn['symptoms']
    for row_index in range(symptoms_df.shape[0]):
        row = symptoms_df.iloc[row_index]
        new_patient_id = row['PATIENT']
        new_pathology = row['PATHOLOGY']
        new_age = row['AGE_BEGIN']
        if (new_patient_id == patient_id) and \
           (new_pathology == pathology) and \
           (int(new_age) == age):
            rep += 1
        else:
            rep = 0
        patient_id = new_patient_id
        pathology = new_pathology
        age = new_age
        condition = find_symptoms_condition(db_cxn,row,rep=rep)
        insert_dict = create_symptom_entry(row,condition)
        symptoms.insert_one(insert_dict)



if __name__ == "__main__":
    client = pymongo.MongoClient(
        "localhost",
        27017
    )

    db = client.symptoms_db
    PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or "../"
    DATA_DIR = os.path.join(PROJECT_ROOT,"data",\
        "synthea_output","fhir")
    SYMPTOMS_CSV = os.path.join(PROJECT_ROOT,"data",\
        "synthea_output","symptoms","csv","symptoms.csv")
    if os.path.exists(DATA_DIR):
        FILES = os.listdir(DATA_DIR)
        collection_names = db.list_collection_names()
        for collection in collection_names:
            records = db[collection]
            c = records.count_documents({})
            print(f"Removing {c} {collection}s")
            records.delete_many({})
            print(f"All {collection}s deleted.")
            c = records.count_documents({})
            print(f"{c} {collection}s remaining")
        for file in FILES:
            with open(os.path.join(DATA_DIR,file),'r') as f:
                json_record = json.load(f)
                for entry in json_record['entry']:
                    records = db[entry["resource"]["resourceType"]]
                    record_id = records.insert_one(entry)

    if os.path.exists(SYMPTOMS_CSV):
        load_symptoms(db)

    client.close()


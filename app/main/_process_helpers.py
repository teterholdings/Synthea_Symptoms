from datetime import datetime
from . import utils
import pandas as pd
from collections import Counter


def _get_encounter_ids(encounters_dict: dict) -> list:
    encounter_ids = list(
        set(
            [
                e for symptom in encounters_dict \
                    for e in encounters_dict[symptom]
            ]
        )
    )
    return encounter_ids

def _get_encounter_types(encounter_obj: dict) \
    -> tuple[str,str]:
    etypes = [c['coding'] for c in encounter_obj\
        ['resource']['type']]
    etype_codes = ",".join(
        [c[0]['code'] for c in etypes]
    )
    etype_disps = ",".join(
        [c[0]['display'] for c in etypes]
    )
    return etype_codes,etype_disps

def _get_reason_or_type(resource_obj):
    if "reasonCode" in resource_obj:
        return resource_obj["reasonCode"]
    # elif "type" in resource_obj:
    #   return resource_obj["type"]
    else:
        return [{"coding": [{"code": "[Not provided]",\
            "display":"[Not provided]"}],"text": "[Not provided]"}]

def _get_reasonCodes(encounter_obj: dict) \
    -> tuple[str,str]:
    reasonCodes = [c['coding'] for c in \
        _get_reason_or_type(encounter_obj['resource'])]
    reasonCode_codes = ",".join(
        [c[0]['code'] for c in reasonCodes]
    )
    reasonCode_disps = ",".join(
        [c[0]['display'] for c in reasonCodes]
    )
    return reasonCode_codes,reasonCode_disps

def _get_encounter_period(encounter_obj: dict) \
    -> tuple[datetime,datetime]:
    start = utils.fhir_datetime(
        encounter_obj['resource']['period']['start'])
    end = utils.fhir_datetime(
        encounter_obj['resource']['period']['end']
    )
    return start,end


def _get_encounter_status(encounter_obj: dict) -> str:
    return encounter_obj['resource']['status']

def _get_encounter_class(encounter_obj: dict) -> str:
    return encounter_obj['resource']['class']['code']

def _get_patient_gender(patient_obj: dict) -> str:
    return patient_obj['resource']['gender']

def _get_patient_birthDate(patient_obj: dict) -> str:
    birthdate = datetime.strptime(patient_obj['resource']\
            ['birthDate'],"%Y-%m-%d")
    return birthdate

def _get_condition_code(condition_obj: dict) -> tuple[str,str]:
    code_list = condition_obj['resource']['code']['coding']
    codes = [c['code'] for c in code_list]
    codes_str = ",".join(codes)
    code_text = condition_obj['resource']['code']['text']
    return codes_str,code_text

def _get_root_cause(cond_obj_list: list) -> str:
    cond_obj_list.sort(
        key = lambda obj: utils.fhir_datetime(
            obj['resource']['recordedDate']
        )
    )
    if len(cond_obj_list) > 0:
        root_cause = cond_obj_list[-1]['resource']['code']['text']
    else:
        root_cause = "[Not Found]"
    return root_cause

def _symptom_patient_id(symptom_obj: dict) -> str:
    patient_id = symptom_obj["resource"]['subject']['reference']
    return patient_id

def _symptom_patient_gender(symptom_obj: dict) -> str:
    patient_gender = symptom_obj["resource"]['gender']
    return patient_gender

def _symptom_patient_age(symptom_obj: dict) -> str:
    patient_age = symptom_obj["resource"]['age_begin']
    return int(patient_age)

def _symptom_texts_severities(symptom_obj: dict) -> str:
    symptoms = symptom_obj['resource']['symptoms']
    symptoms_str = ";".join(
        [f"{s['text']}:{s['severity']}" for s in symptoms]
    )
    return symptoms_str

def _symptom_pathology(symptom_obj: dict) -> str:
    pathology = symptom_obj["resource"]['pathology']
    return pathology

def df_from_symptoms(symptoms_obj_list: list) \
    -> pd.core.frame.DataFrame:

    df_dict = {
        "patient_id":[],
        "patient_gender":[],
        "patient_age":[],
        "symptoms_texts_severities": [],
        "pathology": []
    }

    for s in symptoms_obj_list:
        # get data
        patient_id = _symptom_patient_id(s)
        patient_gender = _symptom_patient_gender(s)
        patient_age = _symptom_patient_age(s)
        symptoms_texts_severities = _symptom_texts_severities(s)
        pathology = _symptom_pathology(s)
        
        # build dict
        df_dict['patient_id'].append(patient_id)
        df_dict['patient_gender'].append(patient_gender)
        df_dict['patient_age'].append(patient_age)
        df_dict['symptoms_texts_severities'].append(symptoms_texts_severities)
        df_dict['pathology'].append(pathology)
    
    return pd.DataFrame(df_dict)


def pathology_stats_from_symptoms(
    symptom_objs: list,
) -> dict: 
    """
    Get basic statistics from a list of symptoms objects.

    Args:
        symptom_objs: (list) list of symptom objects from the 
        database.

    Returns:
        dict containing symptom, age, and gender frequencies.
    """
    p_stats = {}

    # Ages
    ages = [int(s['resource']['age_begin']) for s in symptom_objs]
    age_counter = Counter(ages)
    age_counts = age_counter.most_common()
    age_counts.sort(key=lambda a: a[0])
    p_stats['age'] = {a[0]:a[1] for a in age_counts}

    # Gender
    genders = [s['resource']['gender'] for s in symptom_objs]
    gender_counter = Counter(genders)
    gender_counts = gender_counter.most_common()
    gender_counts.sort(key=lambda g: g[0])
    p_stats['gender'] = {g[0]:g[1] for g in gender_counts}

    # Symptoms
    symptoms = [o for s in symptom_objs for o in \
        s['resource']['symptoms']]
    symptom_text = [o['text'] for o in symptoms]
    symptom_text_counter = Counter(symptom_text)
    symptom_text_counts = symptom_text_counter.most_common()
    symptom_dict = {}
    for i,symptom_count in enumerate(symptom_text_counts):
        symptom_dict[symptom_count[0]] = {'count':symptom_count[1]}
        severity = [int(o['severity']) for o in symptoms if o['text'] == \
            symptom_count[0]]
        severity_counter = Counter(severity)
        severity_counts = severity_counter.most_common()
        severity_counts.sort(key = lambda s: s[0])
        symptom_dict[symptom_count[0]]['severity'] = severity_counts
    
    p_stats['symptoms'] = symptom_dict

    # Count
    p_stats['count'] = len(symptom_objs)

    return p_stats

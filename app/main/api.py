

import base64
import pymongo # not strictly necessary.
import datetime
from . import utils
from collections import Counter

def get_all_symptoms_old(db: pymongo.database.Database) -> list:
    """
    Gets a list of all symptoms from fhir records.
    Assumes database records are in collections by
    resource type.  Currently looks in "Condition"
    collection for codings that end with "(finding)"

    Args:
        db: (pymongo.database.Database) Mongo database connection

    Returns:
        list of symptoms
    """
    symptoms_findings = db.Condition.distinct(
        "resource.code.text",
        {
            "resource.code.text":{
                "$regex": r"^.*\(finding\)$"
            }
        }
    )
    symptoms_list = [s.replace(" (finding)","") for \
        s in symptoms_findings]
    return symptoms_list

def get_all_symptoms(db: pymongo.database.Database) -> list:
    """
    Gets a list of all symptoms from symptoms records.

    Args:
        db: (pymongo.database.Database) Mongo database connection

    Returns:
        list of symptoms
    """
    symptoms = db.symptoms.distinct(
        "resource.symptoms.text",
        {
            "resource.pathology":{
                "$not": {
                    "$regex": r"^.*\(finding\)$"
                }
            }
        }
    )
    symptoms_list = list(symptoms)
    return symptoms_list


def get_encounters_with_symptoms(
        db: pymongo.database.Database,
        symptoms_list: list
    ) -> dict:
    """
    Gets encounter fullUrls for all encounters for which
    patients presented with the given list of symptoms

    Args:
        db: (pymongo.database.Database) Mongo database instance
        symptoms_list: list of symptom strings

    Returns:
        dict of Encounter fullUrl strings for each symptom
    """
    encounter_dict = {}
    for symptom in symptoms_list:
        query = {"resource.code.text": f"{symptom} (finding)"}
        projection = {"resource.encounter.reference":1}
        response = list(db.Condition.find(query,projection))
        encounter_dict[symptom] = [r['resource']['encounter']\
            ['reference'] for r in response]
    return encounter_dict


def get_diagnosticReport_data(
        db: pymongo.database.Database,
        query: dict = {}
    ) -> str:
    """
    Gets and decodes the base64 encoded data object(s) attached
    to a diagnostic report.  This function is just a proof of concept.

    Args:
        db: (pymongo.database.Database) Mongo database instance
        query: (dict) mongo query object

    Returns:
        string of joined decoded data fields.
    """
    response = db.DiagnosticReport.find_one(query)
    if ("presentedForm" in response['resource']) \
        and ("data" in response['resource']['presentedForm'][0]):
        data_list = [base64.b64decode(d['data']).decode() for d in \
            response['resource']['presentedForm']]
        data_str = "\n\n".join([
            f"FORM {i}\n\n{j}\n\n\n" for i,j in \
                enumerate(data_list)
        ])
        return data_str
    else:
        return ""


def get_all_genders(db: pymongo.database.Database) -> list:
    """
    Gets a list of all patient genders

    Args:
        db: (pymongo.database.Database) Mongo database connection

    Returns:
        list of unique patient genders that are in database
    """
    genders = db.Patient.distinct(
        "resource.gender",
    )
    return genders

def get_symptom_genders(db: pymongo.database.Database) -> list:
    """
    Gets a list of all patient genders

    Args:
        db: (pymongo.database.Database) Mongo database connection

    Returns:
        list of unique patient genders that are in database
    """
    genders = db.symptoms.distinct(
        "resource.gender",
    )
    return genders


def get_all_pathologies(db: pymongo.database.Database) -> list:
    """
    Gets a list of all pathologies in the symptoms collection

    Args:
        db: (pymongo.database.Database) Mongo database connection

    Returns:
        list of unique pathologies
    """
    pathologies = db.symptoms.distinct(
        "resource.pathology",
    )
    return pathologies

def get_encounter_info(
    db: pymongo.database.Database,
    encounter_url: str,
    projection: dict = None
) -> dict:
    """
    Get encounter object.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        encounter_url: (str) fullUrl reference to encounter
        projection: (dict) projection to pass to mongo query.

    Returns:
        dict with encounter info
    """
    if projection is None:
        encounter_info = db.Encounter.find_one(
            {"fullUrl": encounter_url}
        )
    else:
        encounter_info = db.Encounter.find_one(
            {"fullUrl": encounter_url},
            projection
        )
    return encounter_info


def get_multiple_encounter_info(
    db: pymongo.database.Database,
    encounter_url_list: list,
    projection: dict = None
) -> pymongo.cursor.Cursor:
    """
    Get multiple encounters.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        encounter_url: (list) encounter "fullUrl"s
        projection: (dict) projection to pass to mongo query.

    Returns:
        pymongo.cursor.Cursor object
    """
    if projection is None:
        encounter_cursor = db.Encounter.find(
            {
                "fullUrl": {
                    "$in": encounter_url_list
                }
            }
        )
    else:
        encounter_cursor = db.Encounter.find(
            {
                "fullUrl": {
                    "$in": encounter_url_list
                }
            },
            projection
        )
    return encounter_cursor


def get_patient_info(
    db: pymongo.database.Database,
    subject_url: str,
    projection: dict = None
) -> dict:
    """
    Get patient object.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        subject_url: (str) fullUrl reference to patient
        projection: (dict) projection to pass to mongo query.

    Returns:
        dict with patient info
    """
    if projection is None:
        patient_info = db.Patient.find_one(
            {"fullUrl": subject_url}
        )
    else:
        patient_info = db.Patient.find_one(
            {"fullUrl": subject_url},
            projection
        )
    return patient_info

def get_multiple_patient_info(
    db: pymongo.database.Database,
    subject_url_list: list,
    projection: dict = None
) -> pymongo.cursor.Cursor:
    """
    Get multiple patient objects.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        subject_url: (list) subject "fullUrl"s 
        projection: (dict) projection to pass to mongo query

    Returns:
        pymongo.cursor.Cursor object
    """
    if projection is None:
        subject_cursor = db.Patient.find(
            {
                "fullUrl": {
                    "$in": subject_url_list
                }
            }
        )
    else:
        subject_cursor = db.Patient.find(
            {
                "fullUrl": {
                    "$in": subject_url_list
                }
            },
            projection
        )
    return subject_cursor


def get_encounter_conditions(
    db: pymongo.database.Database,
    encounter_url: str,
    projection: dict = None
) -> pymongo.cursor.Cursor:
    """
    Get all conditions related to a single encounter.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        encounter_url: (str) encounter fullUrl
        projection: (dict) projection to pass to mongo query

    Returns:
        pymongo.cursor.Cursor object
    """
    condition_cursor = db.Condition.find(
        {
            "resource.encounter.reference": encounter_url
        }
    )
    all_objs = list(condition_cursor)
    all_objs.sort(
        key = lambda obj: utils.fhir_datetime(\
            obj['resource']['recordedDate'])
    )

    return all_objs


def get_andsymptoms_objs(
    db: pymongo.database.Database,
    symptom_list: list,
    **kwargs
) -> list:
    """
    Get all symptoms objects that include all symptoms in symptoms list.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        symptoms_list: (list) list of symptoms to search for
        kwargs: (dict-like) other query specifications

    Returns:
        list of symptoms objects from mongo db
    """
    if len(symptom_list) > 0:
        query = {"resource.symptoms.text": {
                "$all": symptom_list
            }}
    else:
        query = {}
    for key,value in kwargs.items():
        if value is not None:
            query[f"resource.{key}"] = value
    result = db.symptoms.find(
        query
    )
    symptoms_objs = list(result)
    return symptoms_objs

def get_orsymptoms_objs(
    db: pymongo.database.Database,
    symptom_list: list,
    **kwargs
) -> list:
    """
    Get all symptoms objects that include any symptom in symptoms list.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        symptoms_list: (list) list of symptoms to search for

    Returns:
        list of symptoms objects from mongo db
    """
    if len(symptom_list) > 0:
        query = {"resource.symptoms.text": {
                "$in": symptom_list
            }}
    else:
        query = {}
    
    for key,value in kwargs.items():
        query[f"resource.{key}"] = value
    result = db.symptoms.find(
        query
    )
    symptoms_objs = list(result)
    return symptoms_objs


def pathology_symptoms(
    db: pymongo.database.Database,
    pathology: str,
    **kwargs
) -> list:
    """
    Get all instances of a pathology from symptoms collection.

    Args:
        db: (pymongo.database.Database) Mongo database connection
        pathology: (str) The pathology to search
        kwargs: (dict-like) Additional query criteria
    
    Returns:
        list containing allsymptoms objects from mongo db
    """
    query = {"resource.pathology": pathology}
    for key,value in kwargs.items():
        query[f"resource.{key}"] = value
    
    result = db.symptoms.find(
        query
    )
    symptoms_objs = list(result)
    return symptoms_objs


def symtpom_collection_count(
    db: pymongo.database.Database,
    query: dict = None
) -> int:
    """
    Gets the count of records in the symptoms database collection.

    Args:
        db: (pymongo.database.Database) Mongo database connection.
        query: (dict) Mongo query object (default None).

    Returns:
        int number of documents.
    """
    if query is None:
        result = db.symptoms.count_documents({})
    else:
        result = db.symptoms.count_documents(query)
    
    return int(result)

def symtpom_collection_count_est(
    db: pymongo.database.Database
) -> int:
    """
    Gets the estimated count of records in the symptoms 
    database collection.

    Args:
        db: (pymongo.database.Database) Mongo database connection.

    Returns:
        int number of documents.
    """
    result = db.symptoms.estimated_document_count()
    
    return int(result)

def age_gender_pathology_counts(
    db: pymongo.database.Database
) -> dict:
    """
    Gets counts of age,gender,pathology combinations from symptoms
    collection.

    Args:
        db: (pymonbo.database.Database) Mongo database connection.

    Returns:
        dict of (age,gender,pathology) counts
    """

    result = db.symptoms.aggregate([
        {
            "$group": {
                "_id":[
                    "$resource.age_begin",
                    "$resource.gender",
                    "$resource.pathology"
                ],
                "count": {"$sum":1}
            }
        }
    ])
    result_dict = {tuple(r['_id']):r['count'] for r in result}
    return result_dict


def pathology_symptom_severity_counts(
    db: pymongo.database.Database,
    symptom: str
) -> dict:
    """
    Gets counts of pathology, symptom, severity combinations from 
    symptoms collection.

    Args:
        db: (pymonbo.database.Database) Mongo database connection.

    Returns:
        dict of (pathology, symptom [bool], severity) counts
    """
    #
    result = db.symptoms.aggregate([
        {
            "$project":{
                "pathology":"$resource.pathology",
                "symptom": {
                    "$cond":{
                        "if":{"$in":[symptom,\
                            "$resource.symptoms.text"]},
                        "then":{
                            "present":True,
                            "severity": {
                                "$toInt":{
                                    "$arrayElemAt":[
                                        "$resource.symptoms.severity",
                                        {"$indexOfArray":[
                                            "$resource.symptoms.text",
                                            symptom
                                        ]}
                                    ]
                                }
                            }
                        },
                        "else":{
                            "present":False,
                            "severity":0
                        }
                    }
                }
            }
        },
        {
            "$group": {
                "_id":[
                    "$pathology",
                    "$symptom.present",
                    "$symptom.severity"
                ],
                "count": {"$sum":1}
            }
        }
    ])
    result_dict = {tuple(r['_id']):r['count'] for r in result}
    return result_dict


from . import api
import pymongo #not strictly necessary
import pandas as pd
from datetime import datetime
from . import _process_helpers as ph


def andsymptoms_pathology_df(
    db: pymongo.database.Database,
    symptoms_list: list
) -> pd.core.frame.DataFrame:
    """
    Create a dataframe of patients, diagnoses, and other relevant
    information from a list of symptoms.  

    Args:
        db: (pymongo.database.Database) pymongo database object
        symptoms_list: (list) list of symptoms to query (and query)

    Returns:
        pandas dataframe with one line per patient-pathology incident
            that exhibits all of the symptoms.
    """
    symptoms_objs = api.get_andsymptoms_objs(
        db,
        symptoms_list
    )
    df = ph.df_from_symptoms(symptoms_objs)
    return df

def orsymptoms_pathology_df(
    db: pymongo.database.Database,
    symptoms_list: list
) -> pd.core.frame.DataFrame:
    """
    Create a dataframe of patients, diagnoses, and other relevant
    information from a list of symptoms.  

    Args:
        db: (pymongo.database.Database) pymongo database object
        symptoms_list: (list) list of symptoms to query (or query)

    Returns:
        pandas dataframe with one line per patient-pathology incident
            that exhibits all of the symptoms.
    """
    symptoms_objs = api.get_orsymptoms_objs(
        db,
        symptoms_list
    )
    df = ph.df_from_symptoms(symptoms_objs)
    return df


def pathology_stats(
    db: pymongo.database.Database,
    pathology: str
) -> dict:
    """
    Get basic statistics from a pathology.

    Args:
        pathology: (str) Pathology to search in symptoms collection.

    Returns:
        dict containing symptom, age, and gender frequencies.
    """
    symptom_objs = api.pathology_symptoms(db,pathology)
    stats = ph.pathology_stats_from_symptoms(symptom_objs)
    return stats


def all_stats(
    db: pymongo.database.Database,
    symptom_pathology_df:pd.core.frame.DataFrame
) -> dict:
    """
    Get all pathology stats from a symptoms list (or query).

    Args:
        symptom_list: (list) list of symptom strings to search for
        (or query).

    Returns:
        dict containing all pathologies and their interesting stats.
    """
    stats = {}
    total_records = api.symtpom_collection_count_est(db)
    pathologies = symptom_pathology_df['pathology'].unique()
    for p in pathologies:
        p_stats = pathology_stats(db,p)
        p_stats['freq'] = p_stats['count']/total_records
        stats[p] = p_stats

    return stats    



import pytest
import os,sys
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

from main import bayesian_graph

@pytest.fixture(scope="module")
def symptoms():
    symptoms = [
        "Sinus Pain",
        "Fever",
        "Headache",
        "Cough",
        "Anxiety",
        "Confusion",
        "Sensitivity to Pain",
        "Sweating"
    ]
    return symptoms

@pytest.fixture(scope="module")
def pathologies():
    pathologies = [
        "Major depression disorder",
        "Facial laceration",
        "Chronic sinusitis (disorder)"
    ]
    return pathologies

@pytest.fixture(scope="module")
def sfg(symptoms,pathologies):
    sfg = bayesian_graph.symptomsFactorGraph()
    sfg.pathologies = pathologies
    sfg.all_symptoms = symptoms
    sfg.build()

    return sfg

def test_symptomsFactorGraph_build(sfg,symptoms,pathologies):
    n = sfg.Nodes
    assert "Age" in sfg.Nodes
    assert "AgeFactor" in sfg.Nodes
    assert "Gender" in sfg.Nodes
    assert "GenderFactor" in sfg.Nodes
    assert "Pathology" in sfg.Nodes
    for symptom in symptoms:
        assert symptom in sfg.Nodes
        assert f"{symptom}_severity" in sfg.Nodes
        assert f"ssp_{symptom}" in sfg.Nodes
    for pathology in pathologies:
        assert pathology in sfg.Nodes['Pathology'].values


def test_symptomsFactorGraph_Factors(sfg,symptoms,pathologies):
    n = sfg.Nodes

    print("Age Tests:")
    for a in [-1,0,2,10,50,100,200]:
        print(f"P({a}) = {n['AgeFactor'].F(a)}")

    print("\n\n")
    print("Gender Tests:")
    for g in ['M','F',"H"]:
        print(f"P({g}) = {n['GenderFactor'].F(g)}")

    print("\n\n")

    print("GAP Tests:")
    for _ in range(10):
        a = np.random.choice(100)
        g = np.random.choice(['M','F'])
        p = np.random.choice(pathologies)
        print(f"P({p},{a},{g}) = {n['gap'].F(p,a,g)}")

    print("\n\n")
    print("Symptom Factor Tests:")
    for _ in range(10):
        p = np.random.choice(pathologies)
        s = np.random.choice(symptoms)
        coin = np.random.sample()
        if coin < 0.25:
            severity = 0
        elif coin < 0.5:
            severity = 1
        else:
            severity = np.random.choice(200)
        coin2 = np.random.sample()
        if coin2 < 0.5:
            symptom_present = False
        else:
            symptom_present = True
        node_name = f"ssp_{s}"
        print(f"Symptom: {s}; P({p},{symptom_present},{severity}) = "\
            f"{n[node_name].F(p,symptom_present,severity)}")

    # Age
    assert n['AgeFactor'].F(-1) == 0
    assert n['AgeFactor'].F(1) > 0
    assert n['AgeFactor'].F(25) > 0
    assert n['AgeFactor'].F(150) == 0
    
    # Gender
    assert n['GenderFactor'].F('M') > 0
    assert n['GenderFactor'].F('F') > 0
    assert n['GenderFactor'].F('H') == 0
    assert n['GenderFactor'].F('M') \
        + n['GenderFactor'].F('F') == 1
    
    # GAP
    assert n['gap'].F(
        'Chronic sinusitis (disorder)',45,'M'
    ) > 0

    # Symptoms
    assert n['ssp_Headache'].F(
        'Chronic sinusitis (disorder)',
        True,
        1
    ) > 0
    assert n['ssp_Headache'].F(
        'Chronic sinusitis (disorder)',
        False,
        100
    ) > 0
    assert n['ssp_Sweating'].F(
        'Facial laceration',
        True,
        1
    ) == 0
    assert n['ssp_Sweating'].F(
        'Facial laceration',
        True,
        0
    ) == 0
    assert n['ssp_Sweating'].F(
        'Facial laceration',
        False,
        0
    ) == 1
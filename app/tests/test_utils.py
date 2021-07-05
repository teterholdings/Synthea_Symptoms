#!/usr/bin/python3

# Test mongo api module

# Need to make sure mongodb is running 
#  and accessible at port 27017

import pytest
import os,sys
from datetime import datetime,timezone,timedelta
import pickle

# Need to have PYTHONPATH defined

PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or \
    "../.."

if not os.environ.get('PYTHONPATH'):
    PYTHONPATH = os.path.join(
        PROJECT_ROOT,
        "app"
    )
    sys.path.append(PYTHONPATH)


from main import utils

@pytest.mark.parametrize(
    ["datetime_str","fixed_str"],
    [
        ("1949-07-19T13:15:21-04:00","1949-07-19T13:15:21-0400"),
        ("1949-07-19T13:15:21+04:00","1949-07-19T13:15:21+0400"),
        ("2000-02-01T09:15:21+00:00","2000-02-01T09:15:21+0000")
    ]
)
def test_fix_timezonestr(datetime_str,fixed_str):
    fixed = utils._fix_timezonestr(datetime_str)
    assert fixed == fixed_str


@pytest.mark.parametrize(
    ["datetime_str","correct_dt"],
    [
        ("1949-07-19T13:15:21-04:00",\
            datetime(1949,7,19,13,15,21,\
                tzinfo=timezone(timedelta(hours=-4)))),
        ("1949-07-19T13:15:21+04:00",
            datetime(1949,7,19,13,15,21,\
                tzinfo=timezone(timedelta(hours=4)))),
        ("2000-02-01T09:15:21+00:00",\
            datetime(2000,2,1,9,15,21,\
                tzinfo=timezone.utc)),

    ]
)
def test_fhir_datetime(datetime_str,correct_dt):
    dt = utils.fhir_datetime(datetime_str)
    assert dt == correct_dt

def test_factorgraph_save():
    FACTORGRAPH_PATH = os.path.join(
        PROJECT_ROOT,
        'app',
        'data',
        'SFG.pkl'
    )
    OUTPUT_PATH = os.path.join(
        PROJECT_ROOT,
        "app",
        "tests",
        "sfg-util-save.pkl"
    )
    with open(FACTORGRAPH_PATH,'rb') as f:
        sfg = pickle.load(f)
    utils.factorgraph_save(
        sfg,
        OUTPUT_PATH,
        force_save = True
    )

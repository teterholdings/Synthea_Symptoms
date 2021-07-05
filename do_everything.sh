#!/usr/bin/sh

## Prerequisites.

# 1. Docker installed & running.
# 2. Python 3 and python virtual env


## Set environment variables and set up virtual environment

echo "\n\n============= SETTING UP PYTHON VIRTUAL ENVIRONMENT =============\n"

PROJECT_ROOT=$(pwd)
export PROJECT_ROOT

PYTHONPATH=$PROJECT_ROOT/app
export PYTHONPATH

FLASK_APP=$PROJECT_ROOT/app
export FLASK_APP

### Create python virtual environment if not exists.

if [ ! -d "$PROJECT_ROOT/env" ]; then
    python3 -m venv env
fi

### Activate virtual environment

source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


## Initialize mongo db

echo "\n\n============== INITIALIZING MONGO DOCKER CONTAINER ==============\n"

mkdir -p $PROJECT_ROOT/data/mongo

docker run --rm -d \
    --name symptoms-db \
    -v $PROJECT_ROOT/data/mongo:/data/db \
    -p 27017:27017 \
    -p 8081:8081 \
    mongo


## Get synthea and generate records

echo "\n\n============= GETTING SYNTHEA & GENERATING RECORDS ==============\n"

if [[ -z $1 ]]; then
    RECORD_COUNT=500
else
    RECORD_COUNT=$1
fi

export RECORD_COUNT


mkdir -p $PROJECT_ROOT/data
mkdir -p $PROJECT_ROOT/synthea-bin

if [ ! -f $PROJECT_ROOT/synthea-bin/synthea.jar ]; then
    curl -Lo $PROJECT_ROOT/synthea-bin/synthea.jar https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar
fi

### Delete any old Synthea data

rm -rf $PROJECT_ROOT/data/synthea_output
mkdir -p $PROJECT_ROOT/data/synthea_output

java -jar $PROJECT_ROOT/synthea-bin/synthea.jar \
    -p $RECORD_COUNT \
    -a 50-95 \
    --exporter.baseDirectory $PROJECT_ROOT/data/synthea_output \
    --exporter.symptoms.mode 1 \
    --exporter.years_of_history 0 \
    --exporter.symptoms.csv.export true \
    --generate.only_dead_patients true \
    --exporter.use_uuid_filenames true


## Load data into mongo database

echo "\n\n================= LOADING RECORDS INTO MONGO DB =================\n"

python load_data.py

## Start flask app

echo "\n\n================== STARTING FLASK APPLICATION ===================\n"
$PROJECT_ROOT/env/bin/flask run




# Symptoms research

This is the code repository for Team TeMa's proposed research area using Bayesian methods to investigate symptoms and underlying causes based on Synthea-generated data.


## Prerequisites.

1. Docker installed & running (for MongoDB backend).
1. Python 3 and python virtual env
1. Java (requirement to generate Synthea records)


## Steps to deploy minimal development application

The steps below assume a unix-like shell, e.g., `bash`

### Set environment variables
```bash
PROJECT_ROOT=$(pwd)
export PROJECT_ROOT

PYTHONPATH=$PROJECT_ROOT/app
export PYTHONPATH

FLASK_APP=$PROJECT_ROOT/app
export FLASK_APP
```

### Create python virtual environment if not exists.

```bash
if [ ! -d "$PROJECT_ROOT/env" ]; then
    python3 -m venv env
fi
```

### Activate virtual environment and install requirements

```bash
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Create directory for mongo data if it doesn't exist

```bash
mkdir -p $PROJECT_ROOT/data/mongo
```

### Start Mongo database container

```bash
docker run --rm -d \
    --name symptoms-db \
    -v $PROJECT_ROOT/data/mongo:/data/db \
    -p 27017:27017 \
    -p 8081:8081 \
    mongo
```

### Create data folder for Synthea output if it doesn't exist

```bash
mkdir -p $PROJECT_ROOT/data
```

### Create folder for Synthea binary if it doesn't exist

```bash
mkdir -p $PROJECT_ROOT/synthea-bin
```

### Get Synthea if it doesn't already exist

```bash
if [ ! -f $PROJECT_ROOT/synthea-bin/synthea.jar ]; then
    curl -Lo $PROJECT_ROOT/synthea-bin/synthea.jar https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar
fi
```

### Delete old Synthea data and prepare for new data

```bash
rm -rf $PROJECT_ROOT/data/synthea_output
mkdir -p $PROJECT_ROOT/data/synthea_output
```

### Generate Synthea records

The script below generates 500 records by default, but can be easily tailored by modifying the `RECORD_COUNT` variable.  More records will provide a better representation of the underlying distribution.

```bash
RECORD_COUNT=500
export RECORD_COUNT

java -jar $PROJECT_ROOT/synthea-bin/synthea.jar \
    -p $RECORD_COUNT \
    -a 50-95 \
    --exporter.baseDirectory $PROJECT_ROOT/data/synthea_output \
    --exporter.symptoms.mode 1 \
    --exporter.symptoms.csv.export true \
    --generate.only_dead_patients true \
    --exporter.use_uuid_filenames true
```


### Load data into mongo database

Use a python script to populate the Mongo database with the newly generated Synthea record data.

```bash
python db/load_data.py
```

### Start flask app

```bash
flask run
```

### Open the application in a browser

Browse to (http://localhost:5000)[http://localhost:5000].







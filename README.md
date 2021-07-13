# Symptoms research

This is the code repository for Team TeMa's prototype research to employ Bayesian methods to investigate symptoms and underlying causes based on Synthea-generated data.  This code constitutes part of team TeMa's submission to the [Synthetic Health Data Challenge](https://www.challenge.gov/challenge/synthetic-health-data-challenge/).

## Abstract.

Diagnosing an ailment is essentially a Bayesian problem; a doctor only knows what she can observe and must use this information to infer the patient's condition.  In this effort, we provide a prototype implementation that uses Synthea-generated synthetic electronic health records (EHRs) to study the complicated relationships between sets of symptoms and the likelihoods of possible underlying causes.  The goal of this work is to determine the most likely patient pathologies based on a given set of observed symptoms and patient demographics. We apply two distinct methods aimed at achieving this goal.  Our first method relies on a strictly empirical analysis of synthetic EHRs to obtain posterior pathology probabilities.  Our second approach uses the synthetic EHRs to populate probability distribution functions in a graph-based machine learning model.  We give a qualitative and quantitative comparison of these two methods.  Finally, we show how we validated these models, demonstrate how they can be used as a mechanism for validating the outputs of Synthea, and suggest promising research applications of the methods we have proposed.

More detail about the analysis methods employed can be found in the project report at `/write-up/submission.pdf` in this repository.  Also see our demonstration on [YouTube](https://youtu.be/l7_jHRNEuhk)

## What this code does.

The code in this repository uses Synthea to generate synthetic health records and symptoms data, ingests that data into a Mongo database backend, and hosts a browser-based (python flask) application that enables a user to select a set of symptoms, a patient age, patient gender, and the desired analysis method (empirical or Bayesian network; for details see the project report at `/write-up/submission.pdf`).  The application executes the selected method to find the most likely pathologies and associated posterior probabilities.  Selected symptoms and resulting pathologies can be analyzed in more detail by following subsequent links.  In each case, the application carries out all of the analyses using the selected method.  When multiple symptoms are selected, the app conducts the analysis assuming all symptoms are simultaneously present and result from the same underlying cause.  As a result, many combinations of symptoms return no results because they are unlikely to occur together due to a single pathology.

The Bayesian network analysis take about 1-3 minutes, which is considerably longer than the empirical analysis because of the computational resources required to build the factor graph and propagate the sum-product algorithm to all nodes.  

Note: this minimal application is intended only as a prototype to run in a local environment and demonstrate method functionality and utility.  It has not been sufficiently developed and debugged to be deployed in a production environment.


## Prerequisites.

1. Docker installed & running (for MongoDB backend).
1. Python 3 and python virtual env
1. Java (requirement to generate Synthea records)

## Quick Start

This documentation assumes a unix-like shell, e.g., `bash`.  The shell script provided, `do_everything.sh`, sets up the environment, downloads needed libraries and software (including Synthea), generates synthetic health records, and runs the flask application.  These steps are provided with additional context in the following section.  Note: the script `do_everything.sh` automates the execution of **all** of the steps listed in the next section. 

To automate the whole process and get the application running, execute the following.

```bash
git clone https://github.com/teterholdings/Synthea_Symptoms
cd Synthea_Symptoms
source do_everything.sh 500 # Generate 500 records
```

This process could take several hours, as the processes of generating the records and populating the Mongo database take some time.  If it executes successfully, it will start a flask application. Browse to [http://localhost:5000](http://localhost:5000).


## Steps to deploy minimal development application

This section provides additional explanation for each of the steps in `do_everything.sh`.

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

Browse to [http://localhost:5000](http://localhost:5000).

## Tests

The `/app` directory contains the flask application.  The `/app/main` folder contains the python code that accesses the data from the Mongo database, executes the analytical processes, and hosts the outputs as views.  

The `app/tests` folder contains tests and supporting files to ensure the data apis and analysis scripts function properly.  These tests also play a role in model validation, as described in the report (`write-up/submission.pdf`).  To execute these tests, ensure the python virtual environment is properly set-up and activated, and run the following shell commands.

```bash
cd app/tests
pytest
```





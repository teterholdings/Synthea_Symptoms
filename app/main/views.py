from flask import render_template, request, redirect,\
    url_for, current_app, abort, session
from . import main, api, utils, process, distributions
from . import db as DB
from wtforms import BooleanField, SubmitField, RadioField,\
    IntegerField
from flask_wtf import FlaskForm
import pickle,os,sys
import math
import plotly
import plotly.express as px
import pandas as pd
import json
from collections import Counter

FLASK_APP_DIR = os.environ.get('FLASK_APP') or "./app"

@main.route('/',methods=['GET','POST'])
def home():
    with DB.symptoms_db() as db:
        if not session.get("symptoms_list"):
            session['symptoms_list'] = api.get_all_symptoms(db)
        symptoms_list = session.get('symptoms_list')
        if not session.get('patient_genders'):
            session['patient_genders'] = api.get_symptom_genders(db)
        genders = session.get('patient_genders')

    class SymptomForm(FlaskForm):
        pass

    for symptom in symptoms_list:
        setattr(SymptomForm, symptom, BooleanField(symptom))

    setattr(SymptomForm, "gender", RadioField('Gender',\
        choices=[(gender, gender.capitalize()) for gender in \
        genders]))
    setattr(SymptomForm, "age", \
        IntegerField('Patient Age'))

    setattr(SymptomForm, "bayes", \
        SubmitField('Bayesian Network'))

    setattr(SymptomForm, "empirical", \
        SubmitField('Empirical Bayes'))


    form = SymptomForm()

    if (request.method == 'POST'):
        if request.form.get('bayes'):
            print("bayes")
            return(redirect(url_for('main.bayes_results'),code=307))
        elif request.form.get('empirical'):
            print("empirical")
            return(redirect(url_for('main.empirical_results'),\
                code=307))
        else:
            print("Neither")
            redirect(url_for('main.home'))
    
    return render_template('home.html', form=form, \
        symptoms=symptoms_list)


@main.route('/bayesian-graph/symptom_results', methods=['POST'])
def bayes_results():
    pkl_file = os.path.join(FLASK_APP_DIR,"data","SFG.pkl")
    if os.path.exists(pkl_file):
        with open(pkl_file,'rb') as f:
            sfg = pickle.load(f)
    else:
        pkl_dir = os.path.join(FLASK_APP_DIR,"data")
        os.makedirs(pkl_dir,exist_ok=True)
        from .bayesian_graph import symptomsFactorGraph
        sfg = symptomsFactorGraph()
        sfg.build()
        utils.factorgraph_save(sfg,pkl_file)

    if not session.get("symptoms_list"):
        session['symptoms_list'] = api.get_all_symptoms(db)

    symptoms_list = session.get('symptoms_list')
    gender = request.form.get('gender')
    age = int(request.form.get('age'))
    session['gender'] = gender
    session['age'] = age

    pos_symptoms_list = [
        key for key in list(request.form.keys()) if key \
            in symptoms_list
    ]
    session['pos_symptoms_list'] = pos_symptoms_list

    sfg.set_gender(
        gender
    )
    sfg.set_age(
        age
    )
    for symptom in pos_symptoms_list:
        sfg.set_symptom(symptom)
    sfg.sum_product()
    sfg.Nodes['Pathology'].compute_marginals()
    session['sfg'] = sfg
    prob_table = [(p,sfg.Nodes['Pathology'].marginal_pmf(p)) \
        for p in sfg.Nodes['Pathology'].values]
    prob_table = [p for p in prob_table if (not math.isnan(p[1]) and \
        p[1] > 0)]
    if len(prob_table) > 0:
        prob_table.sort(key = lambda z: z[1], reverse = True)
        prob_df = pd.DataFrame(
            prob_table,
            columns = ["Pathology","Probability"]
        )
        fig = px.bar(
            prob_df.iloc[::-1],
            y="Pathology",
            x="Probability",
            orientation = 'h',
            title = "Pathology conditional probabilities",
            labels = {
                "Pathology": ""
            }
        )
        fig.update_xaxes(range = [0,1])
        fig.update_layout(
            font = {
                "size": 18,
            }
        )
        graphJSON = json.dumps(fig,cls=plotly.utils.PlotlyJSONEncoder)

        # Another bar graph that shows dodged pathologies for each symptom?
        return render_template(
            'results.html',
            symptom_list = pos_symptoms_list,
            prob_table = prob_table,
            graphJSON = graphJSON,
            symptom_link = 'main.conditional_symptom',
            pathology_link = 'main.conditional_pathology',
            age = age,
            gender = "Male" if gender == "M" else "Female"
        )
    else:
        return render_template('no_results.html')


@main.route('/bayesian-graph/symptom/<symptom>', methods=['GET'])
def conditional_symptom(symptom):

    if session.get('sfg') is None:
        redirect(url_for("main.home"))
    
    sfg = session.get('sfg')
    age = session.get('age')
    gender = session.get('gender')

    sfg.Nodes[f"PSS_{symptom}"].compute_marginals()

    df = pd.DataFrame(
        tuple(
            list(key) + [value] \
            for key,value in sfg.Nodes[f"PSS_{symptom}"].\
                marginals.items()
        ),
        columns = [
            "Pathology",
            "Symptom",
            "Severity",
            "Probability"
        ]
    )
    df_grouped = df.loc[
        df['Symptom'],
        [
            "Pathology",
            "Probability"
        ]
    ].groupby(
        by = ["Pathology"],
        as_index = False
    ).sum()
    df_grouped.sort_values(
        by = "Probability",
        ascending = False,
        inplace = True
    )
    df_grouped['Probability'] = \
        df_grouped['Probability'] / df_grouped['Probability'].sum()
    
    max_rows = -1
    p = 1
    while (max_rows < 5) and (p > 0.00005) and \
        (df_grouped.shape[0] > (max_rows+1)):
        max_rows += 1
        p = df_grouped["Probability"].iloc[max_rows]
    
    plot1_title = f"Pathology Conditional Probabilities ({symptom} only)"
    plot2_title = f"Pathology {symptom} Severity"

    fig1 = px.bar(
        df_grouped.iloc[0:max_rows].iloc[::-1],
        y="Pathology",
        x="Probability",
        orientation = 'h',
        title = plot1_title,
        labels = {
            "Pathology": ""
        },
    )
    # fig.update_xaxes(range=[0,1])
    fig1.update_layout(
        font = {
            "size": 18,
        },
    )

    min_severity = df['Severity'].loc[df['Symptom'] & \
        (df['Probability'] > 0)].min()
    max_severity = df['Severity'].loc[df['Symptom'] & \
        (df['Probability'] > 0)].max()

    severity_len = max_severity - min_severity + 1
    df_severity = pd.DataFrame(
        {
            "Pathology": [i for i in df_grouped['Pathology'].\
                iloc[0:max_rows] for j in range(severity_len)],
            "Severity": list(range(min_severity,max_severity+1)) * \
                max_rows,
            "Probability Density": [0] * max_rows * severity_len
        }
    )
    for pathology in df_grouped['Pathology'].iloc[0:max_rows].values:
        df_path = df.loc[
            (df['Pathology'] == pathology) & df['Symptom'],
            ['Severity','Probability']
        ]
        knn = distributions.knn_dist(neighbors = min(5,\
            df_path.shape[0]))
        knn.fit(
            df_path['Severity'].values,
            df_path['Probability'].values
        )
        df_severity.loc[df_severity['Pathology'] == pathology,\
            'Probability Density'] = knn.pmf(df_severity['Severity'].\
                loc[df_severity['Pathology'] == pathology])

    fig2 = px.line(
        df_severity, 
        x = "Severity",
        y = "Probability Density",
        color = "Pathology",
        title = plot2_title
    )
    fig2.update_layout(
        font = {
            "size": 18,
        },
    )

    graphJSON_1 = json.dumps(fig1,cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_2 = json.dumps(fig2,cls=plotly.utils.PlotlyJSONEncoder)

    return(
        render_template(
            'two-plot.html',
            page_title = f"Symptom: {symptom}",
            graphJSON_1 = graphJSON_1,
            graphJSON_2 = graphJSON_2,
            plot1_title = plot1_title,
            plot2_title = plot2_title,
            age = age,
            gender = "Male" if gender == "M" else "Female"
        )
    )
   
@main.route('/bayesian-graph/pathology/<pathology>', methods=['GET'])
def conditional_pathology(pathology):

    if session.get('sfg') is None:
        redirect(url_for("main.home"))
    
    sfg = session.get('sfg')
    age = sfg.Nodes['Age'].fixed_value
    gender = sfg.Nodes['Gender'].fixed_value

    symptom_names = session.get('symptoms_list')
    
    symptoms = [s for s in symptom_names if sfg.Nodes[s].fixed_value]
    pathology_probs = []
    df_severity = pd.DataFrame(columns = ["Symptom","Severity",
        "Probability Density"])
    for s in symptoms:
        sfg.Nodes[f"PSS_{s}"].compute_marginals()
        df_symptom = pd.DataFrame(
            tuple(
                list(key) + [value] for key,value in \
                sfg.Nodes[f"PSS_{s}"].marginals.items()
            ),
            columns = [
                "Pathology",
                "Symptom",
                "Severity",
                "Probability"
            ]
        )
        df_grouped = df_symptom.loc[
            df_symptom['Symptom'],
            [
                "Pathology",
                "Probability"
            ]
        ].groupby(
            by = ["Pathology"],
            as_index = False
        ).sum()
        df_grouped['Probability'] = \
            df_grouped['Probability'] / df_grouped['Probability'].sum()
        pathology_prob = df_grouped['Probability'].loc[df_grouped\
            ['Pathology'] == pathology].iloc[0]
        pathology_probs.append((s,pathology_prob))
        min_severity = df_symptom['Severity'].loc[df_symptom\
            ['Symptom'] & (df_symptom['Probability'] > 0)].min()
        max_severity = df_symptom['Severity'].loc[df_symptom\
                ['Symptom'] & (df_symptom['Probability'] > 0)].max()

        severity_len = max_severity - min_severity + 1
        df_path = df_symptom.loc[
        (df_symptom['Pathology'] == pathology) & df_symptom['Symptom'],
            ['Severity','Probability']
        ]
        knn = distributions.knn_dist(neighbors = min(5,\
            df_path.shape[0]))
        knn.fit(
            df_path['Severity'].values,
            df_path['Probability'].values
        )
        df_severity = pd.concat(
            [
                df_severity,
                pd.DataFrame(
                    {
                        "Symptom": [s] * severity_len,
                        "Severity": list(range(min_severity,
                            max_severity + 1)),
                        "Probability Density": knn.pmf(list(range(
                            min_severity,max_severity+1)))
                    }
                )
            ],
            axis = 0
        )
    print(df_severity)
    df = pd.DataFrame(pathology_probs, columns = ['Symptom',\
        'Probability'])

    plot1_title = f"{pathology} Conditional Probabilities"
    plot2_title = f"{pathology} Symptom Severities"
    
    fig1 = px.bar(
        df,
        y="Symptom",
        x="Probability",
        orientation = 'h',
        title = plot1_title,
        labels = {
            "Symptom": "Conditioned on Symptom"
        },
    )
    # fig.update_xaxes(range=[0,1])
    fig1.update_layout(
        font = {
            "size": 18,
        },
    )

    fig2 = px.line(
        df_severity, 
        x = "Severity",
        y = "Probability Density",
        color = "Symptom",
        title = plot2_title
    )
    fig2.update_layout(
        font = {
            "size": 18,
        },
    )

    graphJSON_1 = json.dumps(fig1,cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_2 = json.dumps(fig2,cls=plotly.utils.PlotlyJSONEncoder)

    return(
        render_template(
            'two-plot.html',
            page_title = f"Pathology: {pathology}",
            graphJSON_1 = graphJSON_1,
            graphJSON_2 = graphJSON_2,
            plot1_title = plot1_title,
            plot2_title = plot2_title,
            age = age,
            gender = "Male" if gender == "M" else "Female"
        )
    )

@main.route('/bayes-empirical/symptom_results', methods=['POST'])
def empirical_results():
    symptoms_list = session.get('symptoms_list')

    pos_symptoms_list = [
        key for key in list(request.form.keys()) if key \
            in symptoms_list
    ]
    gender = request.form.get('gender')
    age = int(request.form.get('age'))
    session['gender'] = gender
    session['age'] = age
    session['pos_symptoms_list'] = pos_symptoms_list

    with DB.symptoms_db() as db:
        # Change to get_orsymptoms_objs for "OR" symptom query
        symptom_objs = api.get_andsymptoms_objs(
            db,
            pos_symptoms_list,
            gender=gender,
            age_begin = age
        )

    path_counter = Counter([s['resource']['pathology'] for \
        s in symptom_objs])
    path_counts = path_counter.most_common()
    total_records = len(symptom_objs)
    prob_table = [(p[0],p[1]/total_records) for p in path_counts]
    prob_table = [p for p in prob_table if (not math.isnan(p[1]) and \
        p[1] > 0)]
    if len(prob_table) > 0:
        prob_table.sort(key = lambda z: z[1], reverse = True)
        prob_df = pd.DataFrame(
            prob_table,
            columns = ["Pathology","Probability"]
        )
        fig = px.bar(
            prob_df.iloc[::-1],
            y="Pathology",
            x="Probability",
            orientation = 'h',
            title = "Pathology conditional probabilities",
            labels = {
                "Pathology": ""
            }
        )
        fig.update_xaxes(range = [0,1])
        fig.update_layout(
            font = {
                "size": 18,
            }
        )
        graphJSON = json.dumps(fig,cls=plotly.utils.PlotlyJSONEncoder)

        # Another bar graph that shows dodged pathologies for 
        # each symptom?
        return render_template(
            'results.html',
            symptom_list = pos_symptoms_list,
            prob_table = prob_table,
            graphJSON = graphJSON,
            symptom_link = 'main.empirical_symptom',
            pathology_link = 'main.empirical_pathology',
            age = age,
            gender = "Male" if gender == "M" else "Female"
        )
    else:
        return render_template('no_results.html')



@main.route('/bayes-empirical/symptom/<symptom>', methods=['GET'])
def empirical_symptom(symptom):
    
    age = session.get('age')
    gender = session.get('gender')

    with DB.symptoms_db() as db:
        symptom_objs = api.get_andsymptoms_objs(
            db,
            [symptom],
            age_begin = age,
            gender = gender
        )

    tups = [
        (
            o['resource']['pathology'],
            int(
                o['resource']['symptoms'][
                    [s['text'] for s in \
                        o['resource']['symptoms']].index(symptom)
                ]['severity']
            )
        ) for o in symptom_objs
    ]
    path_symptom_counter = Counter(tups)
    path_symptoms = path_symptom_counter.most_common()
    total_records = len(tups)
    df = pd.DataFrame(
        tuple(
            list(ps[0]) + [ps[1]/total_records] \
            for ps in path_symptoms
        ),
        columns = [
            "Pathology",
            "Severity",
            "Probability"
        ]
    )
    df_grouped = df.loc[
        :,
        [
            "Pathology",
            "Probability"
        ]
    ].groupby(
        by = ["Pathology"],
        as_index = False
    ).sum()
    df_grouped.sort_values(
        by = "Probability",
        ascending = False,
        inplace = True
    )
    df_grouped['Probability'] = \
        df_grouped['Probability'] / df_grouped['Probability'].sum()
    
    max_rows = -1
    p = 1
    while (max_rows < 5) and (p > 0.00005) and \
        (df_grouped.shape[0] > (max_rows+1)):
        max_rows += 1
        p = df_grouped["Probability"].iloc[max_rows]
    
    plot1_title = f"Pathology Conditional Probabilities ({symptom} only)"
    plot2_title = f"Pathology {symptom} Severity"

    fig1 = px.bar(
        df_grouped.iloc[0:max_rows].iloc[::-1],
        y="Pathology",
        x="Probability",
        orientation = 'h',
        title = plot1_title,
        labels = {
            "Pathology": ""
        },
    )
    # fig.update_xaxes(range=[0,1])
    fig1.update_layout(
        font = {
            "size": 18,
        },
    )

    min_severity = df['Severity'].loc[df['Probability'] > 0].min()
    max_severity = df['Severity'].loc[df['Probability'] > 0].max()

    severity_len = max_severity - min_severity + 1
    df_severity = pd.DataFrame(
        {
            "Pathology": [i for i in df_grouped['Pathology'].\
                iloc[0:max_rows] for j in range(severity_len)],
            "Severity": list(range(min_severity,max_severity+1)) * \
                max_rows,
            "Probability Density": [0] * max_rows * severity_len
        }
    )
    for pathology in df_grouped['Pathology'].iloc[0:max_rows].values:
        df_path = df.loc[
            df['Pathology'] == pathology,
            ['Severity','Probability']
        ]
        knn = distributions.knn_dist(neighbors = \
            min(df_path.shape[0],5))
        knn.fit(
            df_path['Severity'].values,
            df_path['Probability'].values
        )
        df_severity.loc[df_severity['Pathology'] == pathology,\
            'Probability Density'] = knn.pmf(df_severity['Severity'].\
                loc[df_severity['Pathology'] == pathology])


    fig2 = px.line(
        df_severity, 
        x = "Severity",
        y = "Probability Density",
        title = plot2_title,
        color = "Pathology"
    )
    fig2.update_layout(
        font = {
            "size": 18,
        }
    )

    graphJSON_1 = json.dumps(fig1,cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_2 = json.dumps(fig2,cls=plotly.utils.PlotlyJSONEncoder)

    return(
        render_template(
            'two-plot.html',
            page_title = f"Symptom: {symptom}",
            graphJSON_1 = graphJSON_1,
            graphJSON_2 = graphJSON_2,
            plot1_title = plot1_title,
            plot2_title = plot2_title,
            age = age,
            gender = "Male" if gender == "M" else "Female"
        )
    )
   
@main.route('/bayes-empirical/pathology/<pathology>', methods=['GET'])
def empirical_pathology(pathology):

    symptom_names = session.get('symptoms_list')
    age = session.get('age')
    gender = session.get('gender')
    symptoms = session.get('pos_symptoms_list')

    with DB.symptoms_db() as db:
        symptom_objs = api.get_orsymptoms_objs(
            db,
            symptoms,
            age_begin = age,
            gender = gender
        )

    pathology_probs = []
    df_severity = pd.DataFrame(columns = ["Symptom","Severity",
        "Probability Density"])
    total_records = len(symptom_objs)
    for s in symptoms:
        cond_world = [o for o in symptom_objs if any([sy['text'] \
            == s for sy in o['resource']['symptoms']])]
        cond_intersection = [o for o in cond_world if o['resource']\
            ['pathology'] == pathology]
        cond_prob = len(cond_intersection) / len(cond_world)
        pathology_probs.append((s,cond_prob))
        severities = [int(o['resource']['symptoms'][
            [sy['text'] for sy in o['resource']['symptoms']].\
                index(s)
        ]['severity']) for o in cond_intersection]
        severity_counter = Counter(severities)
        severity_counts = severity_counter.most_common()
        severity_counts.sort(key=lambda z: z[0])
        min_severity = severity_counts[0][0]
        max_severity = severity_counts[-1][0]
        severity_len = max_severity - min_severity + 1
        knn = distributions.knn_dist(neighbors = min(5,\
            len(severity_counts)))
        knn.fit(
            [i[0] for i in severity_counts],
            [i[1] for i in severity_counts]
        )
        df_severity = pd.concat(
            [
                df_severity,
                pd.DataFrame(
                    {
                        "Symptom": [s] * severity_len,
                        "Severity": list(range(min_severity,
                            max_severity + 1)),
                        "Probability Density": knn.pmf(list(range(
                            min_severity,max_severity+1)))
                    }
                )
            ],
            axis = 0
        )

    df = pd.DataFrame(pathology_probs, columns = ['Symptom',\
        'Probability'])
    
    plot1_title = f"{pathology} Conditional Probabilities"
    plot2_title = f"{pathology} Symptom Severities"

    fig1 = px.bar(
        df,
        y="Symptom",
        x="Probability",
        orientation = 'h',
        title = plot1_title,
        labels = {
            "Symptom": "Conditioned on Symptom"
        },
    )
    # fig.update_xaxes(range=[0,1])
    fig1.update_layout(
        font = {
            "size": 18,
        },
    )

    fig2 = px.line(
        df_severity, 
        x = "Severity",
        y = "Probability Density",
        color = "Symptom",
        title = plot2_title
    )
    fig2.update_layout(
        font = {
            "size": 18,
        },
    )

    graphJSON_1 = json.dumps(fig1,cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_2 = json.dumps(fig2,cls=plotly.utils.PlotlyJSONEncoder)

    return(
        render_template(
            'two-plot.html',
            page_title = f"Pathology: {pathology}",
            graphJSON_1 = graphJSON_1,
            graphJSON_2 = graphJSON_2,
            plot1_title = plot1_title,
            plot2_title = plot2_title,
            age = age,
            gender = "Male" if gender == "M" else "Female"
        )
    )



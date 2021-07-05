from __future__ import annotations
import pytest
import os,sys
import numpy as np
from datetime import datetime,timezone,timedelta
import pickle
from itertools import product



# Need to have PYTHONPATH defined

PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or \
    "../.."

if not os.environ.get('PYTHONPATH'):
    PYTHONPATH = os.path.join(
        PROJECT_ROOT
)
    sys.path.append(PYTHONPATH)



from app.main.bayesian_graph import FactorNode,\
    VariableNode,symptomsFactorGraph
from app.main import utils

PICKLE_SFG_PATH = os.path.join(
    PROJECT_ROOT,
    "app",
    "data",
    "SFG.pkl"
)

@pytest.fixture(scope="module")
def sfg():
    with open(PICKLE_SFG_PATH,'rb') as f:
        sfg = pickle.load(f)
    return sfg

def test_agp_node(sfg):
    n = sfg.Nodes['AGP']
    pr = 0
    arg_lists = [sfg.Nodes[v].values for v in n.function_args]
    args_product = product(*arg_lists)
    for args in args_product:
        pr += n.F(*args)
    print(pr)
    assert pr > 0

def test_agp_node2(sfg):
    n = sfg.Nodes['AGP']
    pr = 0
    arg_lists = [sfg.Nodes[v].values for v in n.function_args]
    args_product = product(*arg_lists)
    for args in args_product:
        pr += n.F(*args)
    print(pr)
    assert abs(1-pr) < 0.00001

def test_agp_node2(sfg):
    n = sfg.Nodes['AGP']
    pr = 0
    arg_lists = [sfg.Nodes[v].values for v in n.function_args]
    args_product = product(*arg_lists)
    for args in args_product:
        pr += n.F(*args)
    print(pr)
    assert abs(1-pr) < 0.00001

def test_pss_factor(sfg):
    pss_nodes = [n for n in sfg.Nodes if n[0:4] == "PSS_"]
    NODE = np.random.choice(pss_nodes)
    n = sfg.Nodes[NODE]
    arg_lists = [sfg.Nodes[v].values for v in n.function_args]
    for p in arg_lists[0]:
        pr = 0
        args_product = product(*arg_lists[1:])
        for args in args_product:
            pr += n.F(p,*args)
        assert abs(1-pr) < 0.00001


def test_variable_message_leaf(sfg):
    agp = sfg.Nodes['AGP']
    am = sfg.Nodes['Age'].message_out(agp)
    gm = sfg.Nodes['Gender'].message_out(agp)
    print(am[10])
    print(gm['M'])

def test_agp_message(sfg):
    agp = sfg.Nodes['AGP']
    am = sfg.Nodes['Age'].message_out(agp)
    gm = sfg.Nodes['Gender'].message_out(agp)
    agp.messages_in['Age'] = am
    agp.messages_in['Gender'] = gm
    agp_m = agp.message_out(sfg.Nodes['Pathology'])
    print(agp_m)


def test_sum_product(sfg):
    sfg.sum_product()
    for n in sfg.Nodes:
        sfg.Nodes[n].compute_marginals()
        print(f"{n}: {sum(sfg.Nodes[n].marginals.values())}")
        assert abs(1-sum(sfg.Nodes[n].marginals.values())) < 0.000000001
    utils.factorgraph_save(
        sfg,
        os.path.join(PROJECT_ROOT,'app','tests','sfg-m.pkl')
    )
    

def test_sum_product_gender(sfg):
    sfg.set_gender("M")
    sfg.sum_product()
    for n in sfg.Nodes:
        sfg.Nodes[n].compute_marginals()
        print(f"{n}: {sum(sfg.Nodes[n].marginals.values())}")
    
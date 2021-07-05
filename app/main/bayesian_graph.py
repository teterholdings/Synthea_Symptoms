#!/usr/bin/python3

### Bayesian network symptoms module

import numpy as np
from types import MethodType
from itertools import product

if __name__ == "__main__":

    import os,sys
    import numpy as np
    import pickle

    PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or \
        "../../"

    if not os.environ.get('PYTHONPATH'):
        PYTHONPATH = PROJECT_ROOT
        sys.path.append(PYTHONPATH)

    from app.main import api
    from app.main.db import symptoms_db

else:

    from .db import symptoms_db
    from . import api



class Node(object):

    nodeType = "GenericNode"

    def __init__(self,name,leaf=False):
        self.name = name
        self.leaf = leaf
        self.neighbors = []
        self.marginals = None
        self.messages_in = {}
    
    def get_name(self):
        return self.name
    
    def add_link(self,node_name):
        self.neighbors.append(node_name)
        
    def get_type(self):
        return self.nodeType

    def check_messages(self,out_node):
        if out_node not in self.neighbors:
            raise ValueError("Cannot send message to " \
                "non-neighboring node")
        no_message_in = [n for n in self.neighbors if n not in \
            self.messages_in]
        if any([n != out_node for n in no_message_in]):
            print(self.neighbors)
            raise RuntimeError("Not enough messages received "\
                f"for variable {self.get_name()}")

    def marginal_pmf(self,v):
        p = self.marginals.get(v) or 0
        total_p = sum(self.marginals.values())
        return p/total_p

class VariableNode(Node):

    def __init__(
        self,
        name: str,
        values: list = [],
        leaf: bool = False
    ):
        super().__init__(name,leaf)
        self.values = values
        self.fixed_value = None
        self.nodeType = "VariableNode"

    def set_value(
            self,
            value: object
        ) -> None:
        if value not in self.values:
            raise ValueError(
                f"Trying to set bad value ({value}) for " \
                f"{self.__class__.__name__}")
        self.fixed_value = value
    
    def message_out(
        self,
        out_node_obj: "FactorNode"
    ) -> dict:
        out_node = out_node_obj.get_name()
        self.check_messages(out_node)
        if self.leaf:
            out_message = {
                v: 1 for v in self.values 
            }
        else:
            out_message = {
                v: np.prod(
                    [
                        self.messages_in[n][v] for n in \
                            self.messages_in if n != out_node
                    ]
                ) for v in self.values
            }
        
        if self.fixed_value is not None:
            out_message = {
                v: out_message[v] if v == self.fixed_value else 0 \
                    for v in self.values
            }
        return out_message
    
    def compute_marginals(self):
        if len(self.messages_in) != len(self.neighbors):
            raise RuntimeWarning("Cannot compute marginal pmf until "\
                "all messages have been received at node "\
                f"{self.get_name()}")
        else:
            self.marginals = {
                v: np.product([self.messages_in[n][v] for \
                    n in self.messages_in]) \
                    for v in self.values
            }
        
    
class FactorNode(Node):

    def __init__(
        self,
        name: str,
        function_dict: dict = {},
        function_args: list = [],
        leaf=False
    ):
        super().__init__(name,leaf)
        self.function_args = function_args
        self.function_dict = function_dict
        self.nodeType = "FactorNode"

    def F(
        self,
        *args
    ) -> float:
        """ Evaluate factor function. Input arguments are values 
        for neighboring variable nodes.  This function should
        evaluate for any combination of permissible values.  Argument
        order is stored in self.function_args.

        Args:
           *args: (tuple) values for neighboring variable nodes.
        
        Returns:
            float evaluation of factor fuction
        """

        return self.function_dict.get(args) or 0

    def message_out(
        self,
        out_node_obj: VariableNode,
    ) -> dict:
        out_node = out_node_obj.get_name()
        self.check_messages(out_node)
        if self.leaf:
            out_message = {
                v: self.F(v) for v in \
                    out_node_obj.values
            }
        else:
            args_list = [(n,list(self.messages_in[n].keys())) \
                for n in self.messages_in if n != out_node]
            order = {key:i for i,key in enumerate(self.function_args)}
            args_list.sort(key = lambda z: order[z[0]])
            i = self.function_args.index(out_node)
            out_message = {}
            for v in out_node_obj.values:
                args_list_v = \
                    [al[1] for al in args_list[:i]] + \
                    [[v]] + \
                    [al[1] for al in args_list[i:]]
                
                args = product(*args_list_v)
                out_message[v] = sum([self.F(*a) * \
                    np.product([
                        self.messages_in[n][a[order[n]]] for n in \
                            self.messages_in if n != out_node
                    ]) for a in args
                ])
        return out_message

    def compute_marginals(self):
        if len(self.messages_in) != len(self.neighbors):
            raise RuntimeWarning("Cannot compute marginal pmf until "\
                "all messages have been received at node "\
                f"{self.get_name()}")
        else:
            args_list = [list(self.messages_in[n].keys()) \
                for n in self.function_args]
            args = product(*args_list)
            self.marginals = {
                a: self.F(*a)*np.product([
                    self.messages_in[self.function_args[i]][a[i]] \
                        for i in range(len(a))
                ]) for a in args
            }

    def marginal_pmf(self,*v):
        p = self.marginals.get(v) or 0
        total_p = sum(self.marginals.values())
        return p/total_p

class symptomsFactorGraph(object):

    """Class to construct and analysize symptoms factor graph"""

    def __init__(
        self,
        Nodes: dict = {}
    ):
        """
        Instanciate symptomsFactorGraph.

        Args:
            Nodes: (dict) nodes comprising the graph.
        
        Returns
            None
        """
        self.Nodes = {}
        

    def _age_variable(self) -> VariableNode:
        age_list = list(range(0,140))
        age_var = VariableNode(
            "Age",
            values = age_list,
            leaf = True
        )
        return age_var

    def _gender_variable(self) -> VariableNode:
        with symptoms_db() as db:
            gender_list = api.get_symptom_genders(db)
        gender_var = VariableNode(
            "Gender",
            values = gender_list,
            leaf = True
        )
        return gender_var

    def _age_gender_pathology_factor(self) -> FactorNode:
        """
        This factor function is just the joint empirical distribution
        of these three variables
        """
        with symptoms_db() as db:
            agp_counts = api.age_gender_pathology_counts(db)
        total_count = sum(agp_counts.values())
        agp_dict = {
            t: agp_counts[t]/total_count \
                for t in agp_counts
        }
        agp_factor = FactorNode(
            name="AGP",
            function_dict= agp_dict,
            function_args = ['Age','Gender','Pathology']
        )
        return agp_factor

    def _pathology_variable(self) -> VariableNode:
        with symptoms_db() as db:
            pathologies = api.get_all_pathologies(db)
        pathology_var = VariableNode(
            "Pathology",
            values = pathologies
        )
        return pathology_var

    def _pathology_symptom_severity_factor(
        self,
        symptom: str
    ) -> FactorNode:
        """
        This factor function is the joint distribution
        symptom and severity conditioned on pathology
        """
        with symptoms_db() as db:
            pss_counts = api.pathology_symptom_severity_counts(db,\
                symptom)
        
        pss_keys = list(pss_counts.keys())
        pathologies = list(set([pss_key[0] for pss_key in pss_keys]))
        pathology_counts = {
            p: sum([pss_counts[k] for k in pss_keys if k[0] == p]) \
                for p in pathologies
        }
        pss_dict = {
            k: pss_counts[k]/pathology_counts[k[0]] \
                for k in pss_counts
        }
        pss_factor = FactorNode(
            name=f"PSS_{symptom}",
            function_dict= pss_dict,
            function_args = [
                'Pathology',
                symptom,
                f'{symptom}_severity'
            ]
        )
        return pss_factor

    def _symptom_variable(
        self,
        symptom: str
    ) -> VariableNode:
        symptom_var = VariableNode(
            symptom,
            values = [True,False],
            leaf = True
        )
        return symptom_var

    def _severity_variable(
        self,
        symptom: str
    ) -> VariableNode:
        with symptoms_db() as db:
            values = db.symptoms.distinct(
                "resource.symptoms.severity",
                {"resource.symptoms.text":symptom}
            )
        values = [int(i) for i in values]
        if 0 not in values:
            values = [0] + values
        severity_var = VariableNode(
            f"{symptom}_severity",
            values = values,
            leaf = True
        )
        return severity_var

    def add_link(self,
        Node1: Node,
        Node2: Node
    ) -> None:
        """
        Adds link between two nodes by appending each other's names to
        each's neighbors attribute.

        Args:
             Node1: (Node) node to be linked.
             Node2: (Node) node to be linked.

        Returns:
            None
        """
        Node1.add_link(Node2.get_name())
        Node2.add_link(Node1.get_name())

    def add_node(
        self,
        node: Node
    ) -> None:
        """
        Add a node to the factor graph.

        Args:
            node: (Node) node to add to the graph.
        
        Returns:
            None
        """
        self.Nodes[node.get_name()] = node

    def build(self) -> None:
        """
        Build the factor graph from the symptoms (mongo) collection.
        Creates and links all nodes.  Establishes factor functions.

        Args: (None)

        Returns:
            None
        """
        age = self._age_variable()
        gender = self._gender_variable()
        agp_factor = self._age_gender_pathology_factor()
        self.add_link(age,agp_factor)
        self.add_link(gender,agp_factor)
        self.add_node(age)
        self.add_node(gender)
        pathology = self._pathology_variable()
        self.add_link(agp_factor,pathology)
        self.add_node(agp_factor)
        with symptoms_db() as db:
            symptoms = api.get_all_symptoms(db)
        for symptom in symptoms:
            symptom_node = self._symptom_variable(symptom)
            severity_node = self._severity_variable(symptom)
            factor_node = self._pathology_symptom_severity_factor(
                symptom
            )
            self.add_link(pathology,factor_node)
            self.add_link(severity_node,factor_node)
            self.add_link(symptom_node,factor_node)
            self.add_node(symptom_node)
            self.add_node(severity_node)
            self.add_node(factor_node)
        self.add_node(pathology)

    def sum_product(
        self,
        root_node: str ="Pathology"
    ) -> None:
        """ 
        Run the sum product algorithm and updates marginals in all
        Nodes.

        Args: 
            root_node: (str) Name of the root node in the algorithm.
                Defaults to "Pathology"
        
        Returns:
            None
        """
        self.clear(values = False)
        if root_node not in self.Nodes:
            raise ValueError(f"Cannot sum product; {root_node} not "\
                "in factor graph nodes.")

        ready = [n for n in self.Nodes if self.Nodes[n].leaf]
        not_ready = [n for n in self.Nodes if \
            (not self.Nodes[n].leaf) and n != root_node]
        while len(ready) > 0:
            node_name = ready.pop()
            new_node_list = [n for n in self.Nodes[node_name].\
                neighbors if n not in self.Nodes[node_name].\
                    messages_in]
            if len(new_node_list) != 1:
                raise RuntimeError("Node in ready list is not ready")
            new_node_name = new_node_list[0]
            msg = self.Nodes[node_name].message_out(
                self.Nodes[new_node_name]
            )
            self.Nodes[new_node_name].messages_in[node_name] = msg
            if (new_node_name in not_ready) and \
                ((len(self.Nodes[new_node_name].messages_in) + 1) == \
                    len(self.Nodes[new_node_name].neighbors)): 
                ready.append(new_node_name)
                not_ready.remove(new_node_name)
        
        if len(not_ready) > 0:
            print(not_ready)
            raise RuntimeError("Sum Product terminated before all "\
                "nodes have been reached.")
        
        if len(self.Nodes[root_node].messages_in) != len(self.\
            Nodes[root_node].neighbors):
            raise RuntimeError("Sum Product terminated without "\
                "all messages reaching the root node")
        
        not_ready = [n for n in self.Nodes if n != root_node]
        ready = [root_node]
        while len(ready) > 0:
            current_node = ready.pop()
            for neighbor in self.Nodes[current_node].neighbors:
                if current_node not in self.Nodes[neighbor].\
                    messages_in:
                    msg = self.Nodes[current_node].\
                        message_out(self.Nodes[neighbor])
                    self.Nodes[neighbor].messages_in[current_node] = \
                        msg
                    if not self.Nodes[neighbor].leaf:
                        ready.append(neighbor)

        check = [len(self.Nodes[n].neighbors) - \
            len(self.Nodes[n].messages_in) for n in self.Nodes]

        try:
            assert all([c == 0 for c in check])
        except AssertionError as e:
            raise RuntimeError("Sum Product Terminated before "\
                "all nodes were messaged.")

    def set_gender(self,gender: str) -> None:
        self.Nodes['Gender'].set_value(gender)
    
    def set_symptom(
        self,
        symptom: str,
        value: bool = True
    ) -> None:
        self.Nodes[symptom].set_value(value)

    def set_severity(
        self,
        symptom: str,
        value: int = 0
    ) -> None:
        self.Nodes[f"{symptom}_severity"].set_value(int(value))
    
    def set_age(
        self,
        age: int
    ) -> None:
        self.Nodes["Age"].set_value(int(age))
    
    def set_pathology(
        self,
        pathology: str
    ) -> None:
        self.Nodes["Pathology"].set_value(pathology)
    
    def clear(
            self,
            messages: bool = True,
            marginals: bool = True,
            values: bool = True
        ) -> None:
        """
        Clear all node messages, marginals, and/or values

        Args:
            messages: (bool) If True, clear messages for all nodes.
            marginals: (bool) If True, clear marginals for all nodes.
            values: (bool) If True, clear fixed values for all nodes.
        
        Returns:
            None
        """
        for n in self.Nodes:
            if messages:
                self.Nodes[n].messages_in = {}
            if marginals:
                self.Nodes[n].marginals = {}
            if values:
                self.Nodes[n].fixed_value = None


if __name__ == "__main__":

    from app.main import utils
    import sys
    
    sfg = symptomsFactorGraph()
    sfg.build()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "SFG.pkl"

    utils.factorgraph_save(sfg,file_path)



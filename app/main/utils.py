from datetime import datetime
import re
import pickle

def _fix_timezonestr(datetime_str: str) -> str:
    fixed_str = re.sub(
        r'([\-,\+][0-9]{2}):([0-9]{2})',
        r'\1\2',
        datetime_str
    )
    return fixed_str

def fhir_datetime(datetime_str: str) -> datetime:
    fixed_str = _fix_timezonestr(datetime_str)
    dt = datetime.strptime(
        fixed_str,
        "%Y-%m-%dT%H:%M:%S%z"
    )
    return dt

def factorgraph_save(
    fg,
    file_path: str,
    force_save: bool = False
) -> None:
    from .bayesian_graph import FactorNode,VariableNode,\
        symptomsFactorGraph
    if fg.__class__.__module__ == "__main__":
        new_fg = symptomsFactorGraph()
        for node in fg.Nodes:
            n = fg.Nodes[node]
            if (n.__class__.__name__ \
                    == "FactorNode") or force_save:
                new_node = FactorNode(
                    name = n.name,
                    leaf = n.leaf,
                    function_dict = n.function_dict,
                    function_args = n.function_args
                )
                new_node.neighbors = n.neighbors
            elif (n.__class__.__name__ \
                    == "VariableNode") or force_save:
                new_node = VariableNode(
                    name = n.name,
                    values = n.values,
                    leaf = n.leaf
                )
                new_node.neighbors = n.neighbors
            else: 
                raise ValueError("Invalid Node object")
            new_fg.add_node(new_node)
    else:
        new_fg = fg
        
    write_file = open(file_path, 'wb')
    pickle.dump(new_fg, write_file)

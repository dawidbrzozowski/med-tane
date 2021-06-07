import networkx as nx
import matplotlib.pyplot as plt
from itertools import chain,combinations,product
from collections import defaultdict
from graphviz import Digraph

class Visualiser:

    def _generate_dot_nodes(self, data, dot):
        unique_nodes = set()
        for dependency in data:
            unique_nodes.add(dependency[0])
            unique_nodes.add(dependency[1])

        with dot.subgraph(name='cluster0') as c:
            c.attr(color='blue')
            c.node_attr['style'] = 'filled'
            c.node('{}', '{}')
            c.attr(label='Zbiór pusty')

        for id, val in enumerate(unique_nodes):
            attr_num = self._get_number_of_elements_in_set(val)
            with dot.subgraph(name='cluster' + str(attr_num)) as c:
                c.attr(color='blue')
                c.node_attr['style'] = 'filled'
                c.node(val, val)
                c.attr(label='Zbiory o liczności ' + str(attr_num))

    def _get_number_of_elements_in_set(self, set):
        return set.count(',') + 1 if set else 0

    def _add_dot_edges(self, data, dot):
        for dependency in data:
            dot.edge(dependency[0], dependency[1])
            attr_num = self._get_number_of_elements_in_set(dependency[1])
            if attr_num == 1:
                dot.edge(dependency[1], '{}')

    def __init__(self, data):
        dot = Digraph(comment='Wizualizacja')
        self._generate_dot_nodes(data, dot)
        self._add_dot_edges(data, dot)
        dot.render('result.gv', view=True)





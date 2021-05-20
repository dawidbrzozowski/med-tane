import networkx as nx
import matplotlib.pyplot as plt


class Visualiser:

    def _generate_graph(self, data):
        graph = nx.DiGraph()
        for dependency in data:
            graph.add_edge(dependency[0], dependency[1], color='b', weight=3)

        return graph

    def __init__(self, data):
        graph = self._generate_graph(data)

        nx.draw(graph, node_size=1000, with_labels=True)
        plt.axis("equal")
        plt.show()

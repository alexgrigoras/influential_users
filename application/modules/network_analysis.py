import pickle

import networkx as nx
import matplotlib.pyplot as plt


class NetworkAnalysis:
    def __init__(self):
        self.graph = nx.empty_graph

    def __get_graph_info(self):
        return nx.info(self.graph)

    def create_network(self, file_path):
        self.graph = nx.read_edgelist(file_path + ".txt", create_using=nx.DiGraph(), edgetype=str)

        plt.figure(figsize=(20, 20))
        plt.axis('off')

        print(self.__get_graph_info())

        pos = nx.spring_layout(self.graph)
        pr = nx.pagerank(self.graph, alpha=0.9)

        node_color = [20000.0 * self.graph.degree(v) for v in self.graph]
        node_size = [v * 10000 for v in pr.values()]

        labels = pickle.load(open(file_path + ".pickle", "rb" ))

        nx.draw_networkx(self.graph, pos=pos, with_labels=True, node_color=node_color, node_size=node_size)

        var = sorted(pr, key=pr.get, reverse=True)[:5]
        print("PageRank:")
        index = 1
        for v in var:
            print("\t" + str(index) + ". " + labels[v])
            index += 1

        nx.write_gexf(self.graph, file_path + "gexf")

        plt.show()

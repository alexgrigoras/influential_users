import pickle

import networkx as nx
import matplotlib.pyplot as plt


class NetworkAnalysis:
    def __init__(self):
        self.__graph = nx.empty_graph
        self.__labels = dict()
        self.__page_rank = []

    def __get_graph_info(self):
        return nx.info(self.__graph)

    def export_to_gexf(self, file_path, file=""):
        nx.write_gexf(self.__graph, file_path + file + ".gexf")

    def create_network(self, file_path):
        self.__graph = nx.read_edgelist(file_path + ".txt", create_using=nx.DiGraph(), edgetype=str, delimiter=",")

        plt.figure(figsize=(20, 20))
        plt.axis('off')

        self.__labels = pickle.load(open(file_path + ".pickle", "rb"))

        print(self.__get_graph_info())

    def gen_gr(self):
        self.__graph = nx.gn_graph(10, kernel=lambda x: x ** 1.5)

    def compute_page_rank(self):
        self.__page_rank = nx.pagerank(self.__graph, alpha=0.9)
        var = sorted(self.__page_rank, key=self.__page_rank.get, reverse=True)[:5]
        print("PageRank:")
        index = 1
        for v in var:
            print("\t" + str(index) + ". " + self.__labels[v])
            index += 1

    def display_network(self):
        pos = nx.spring_layout(self.__graph)

        node_color = True
        node_size = True

        if self.__page_rank:
            node_color = [20000.0 * self.__graph.degree(v) for v in self.__graph]
            node_size = [v * 10000 for v in self.__page_rank.values()]

        nx.draw_networkx(self.__graph, pos=pos, with_labels=True, node_color=node_color, node_size=node_size,
                         labels=self.__labels)

        plt.show()

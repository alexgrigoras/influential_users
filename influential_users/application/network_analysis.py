import pickle

import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

from influential_users.application.message_logger import MessageLogger
from influential_users.application.plotly_display import visualize_graph_3d, visualize_graph

NETWORKS_FOLDER = '.networks'
IMAGES_FOLDER = '.images'
TEXT_EXTENSION = '.txt'
OBJECT_EXTENSION = '.pickle'
GRAPH_EXTENSION = '.gexf'
IMAGE_EXTENSION = '.png'
DOT_EXTENSION = '.dot'


class NetworkAnalysis:
    """

    """

    def __init__(self, file_name=None):
        """
        Class constructor
        """
        # logging module
        ml = MessageLogger('network_analysis')
        self.logger = ml.get_logger()

        # variables
        self.__graph = nx.empty_graph
        self.__labels = {}
        self.__rank = []
        self.file_name = file_name

    def set_file_name(self, file_name):
        """
        Sets the name of the file to read for input and also for exporting data to a specific format
        :param file_name: name of the file without extension
        """
        self.file_name = file_name

    def __get_graph_info(self):
        """
        Prints the graph information
        :return: returns the graph information
        """
        return nx.info(self.__graph)

    def export_to_gexf(self):
        """
        Export network to gexf format. A file name needs to be set before performing this operation
        """
        if not self.file_name:
            self.logger.critical("No file name was set")
            exit(0)

        nx.write_gexf(self.__graph, NETWORKS_FOLDER + "/" + self.file_name + GRAPH_EXTENSION)

    def export_to_dot(self):
        """
        Export network to gexf format. A file name needs to be set before performing this operation
        """
        if not self.file_name:
            self.logger.critical("No file name was set")
            exit(0)

        # write dot file to use with graphviz - run "dot -Tpng file_name.svg > file_name.svg"
        nx.nx_agraph.write_dot(self.__graph, NETWORKS_FOLDER + "/" + self.file_name + DOT_EXTENSION)

    def create_network(self):
        """
        Creates a network from the file with the edge-list.
        A file name needs to be set before performing this operation
        """
        if not self.file_name:
            self.logger.critical("No file name was set")
            exit(0)

        self.__graph = nx.read_edgelist(NETWORKS_FOLDER + "/" + self.file_name + TEXT_EXTENSION,
                                        create_using=nx.Graph(),
                                        edgetype=str, delimiter=" ")
        self.__labels = pickle.load(open(NETWORKS_FOLDER + "/" + self.file_name + OBJECT_EXTENSION, "rb"))

        print(self.__get_graph_info())

    def compute_page_rank(self):
        """
        Calculates the values of the nodes using page rank algorithm and prints them
        """
        self.__rank = nx.pagerank(self.__graph, alpha=0.9)
        self.__display_rank("PageRank")

    def compute_betweenness_centrality(self):
        """
        Calculates the values of the nodes using  algorithm and prints them
        """
        self.__rank = nx.betweenness_centrality(self.__graph, normalized=True, endpoints=True)
        self.__display_rank("Betweenness centrality")

    def __display_rank(self, algorithm_name):
        """
        Prints the first 5 nodes with the highest values
        :param algorithm_name: tha name of the algorithm used
        """
        values = sorted(self.__rank, key=self.__rank.get, reverse=True)[:5]
        print(algorithm_name + ":")
        for i, v in enumerate(values, start=1):
            print("\t" + str(i) + ". " + self.__labels[v])

    def __configure_display(self, title):
        plt.title(title)
        plt.figure(figsize=(30, 30))
        plt.axis('off')
        node_color = []
        node_size = []

        if self.__rank:
            node_color = [20000.0 * self.__graph.degree(v) for v in self.__graph]
            node_size = [v * 10000 for v in self.__rank.values()]

        return node_color, node_size

    def __draw(self):
        """
        Display the graph and
        """
        plt.savefig(IMAGES_FOLDER + "/" + self.file_name + IMAGE_EXTENSION)
        plt.show()

    def display_tree(self):
        """
        Display the created tree
        """
        node_color, node_size = self.__configure_display('Tree')
        pos = graphviz_layout(self.__graph, prog='dot')
        tree = nx.minimum_spanning_tree(self.__graph)

        nx.draw_networkx(tree, pos=pos, with_labels=False, node_color=node_color, node_size=node_size,
                         labels=self.__labels)
        self.__draw()

    def display_graph(self):
        """
        Display the created graph
        """
        if not self.file_name:
            self.logger.critical("No file name was set")
            exit(0)

        node_color, node_size = self.__configure_display('Graph')
        pos = nx.spring_layout(self.__graph)

        nx.draw_networkx(self.__graph, pos=pos, with_labels=True, node_color=node_color, node_size=node_size,
                         labels=self.__labels)
        self.__draw()

    def display_graphviz(self):
        """
        Display the created graph
        """
        if not self.file_name:
            self.logger.critical("No file name was set")
            exit(0)

        # node_color, node_size = self.__configure_display('Graph')
        # pos = nx.spring_layout(self.__graph)

        tree = nx.minimum_spanning_tree(self.__graph)
        G = nx.nx_agraph.to_agraph(tree)
        G.layout()
        G.draw('test_graph1.gif')

        # nx.draw_networkx(self.__graph, pos=pos, with_labels=True, node_color=node_color, node_size=node_size,
        #                 labels=self.__labels)\
        # self.__draw_graph()

    def display_plotly(self):
        node_sizes = self.get_node_sizes(self.__graph)
        # edge_weights = self.get_edge_weights(graph)
        node_ids = self.get_node_labels(self.__graph)
        node_labels = [self.__labels[n_id] for n_id in node_ids]
        edge_weights = None
        layout = "graphviz"
        # layout = "spring"
        filename = "outputs/" + layout + "3d.html"
        fig = visualize_graph_3d(self.__graph, node_labels, node_sizes, filename=filename, title="3D visualization")
        # visualize_graph(graph, node_labels, node_sizes, edge_weights, layout, filename="outputs/" + layout + ".html",
        #                title=layout)
        return fig

    @staticmethod
    def get_edge_weights(graph):
        weights = [graph[u][v]['weight'] for u, v in graph.edges()]
        return weights

    @staticmethod
    def get_node_sizes(graph):
        node_sizes = nx.get_node_attributes(graph, 'importance').values()
        return node_sizes

    @staticmethod
    def get_node_labels(graph):
        return graph.nodes()

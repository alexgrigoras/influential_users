import time

from influential_users.modules.message_logger import MessageLogger
from influential_users.modules.network_analysis import NetworkAnalysis
from influential_users.modules.youtube_api import YoutubeAPI
import dash
import dash_core_components as dcc
import dash_html_components as html


def main():
    # logging module
    ml = MessageLogger('main')
    logger = ml.get_logger()

    # modules
    crawler = YoutubeAPI()
    network = NetworkAnalysis()

    # input data
    keyword = "peter mckinnon"
    nr_videos = 3

    # beginning time
    start_time = time.time()

    # crawling data
    #results = crawler.search(keyword, nr_videos)
    #crawler.process_search_results(results)
    #crawler.process_tokens(100)
    #file_name = crawler.create_network("nxOHAKTVB7baOKsQgTtJIyGxcs8/40UhQ1chkJQqNBj-HYIF_o91Iak")
    #file_path = crawler.create_network("\"ksCrgYQhtFrXgbHAhi9Fo5t0C2I/EPvt4jK7PDLHJPZ17vxy9hpi5II\"")

    #crawler.get_channel_data()

    file_name = crawler.create_network("EAIvoD3gSIIyg260Gm4lZxzhZBs")
    #file_name = crawler.create_network(results[0]['_id'])

    # create users network
    network.set_file_name(file_name)
    network.create_network()
    network.compute_page_rank()
    #network.compute_betweenness_centrality()

    #network.display_tree()
    #network.display_graphviz()
    fig = network.display_plotly()
    #network.display_graph()
    #network.export_to_gexf()

    # end time
    end_time = time.time()
    execution_time = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
    logger.debug("Execution time: " + execution_time)

    app = dash.Dash()
    app.layout = html.Div([
        dcc.Graph(figure=fig)
    ])

    app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter

if __name__ == '__main__':
    main()

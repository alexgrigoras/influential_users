import time

from influential_users.modules.message_logger import MessageLogger
from influential_users.modules.network_analysis import NetworkAnalysis
from influential_users.modules.youtube_api import YoutubeAPI


def main():
    # logging module
    ml = MessageLogger('main')
    logger = ml.get_logger()

    # modules
    crawler = YoutubeAPI()
    network = NetworkAnalysis()

    # input data
    keyword = input('Enter a keyword: ')
    nr_videos_str = input('Enter the number of videos: ')
    nr_videos = 0

    try:
        nr_videos = int(nr_videos_str)
    except ValueError:
        print("Invalid number of videos")
        exit()

    # beginning time
    start_time = time.time()

    # crawling data
    crawler.search(keyword, nr_videos)
    crawler.process_results()
    crawler.process_tokens(nr_videos)
    file_name = crawler.create_users_network("\"ksCrgYQhtFrXgbHAhi9Fo5t0C2I/qAjSavC3x9fPWugAxzknLDt5TnM\"")
    # file_path = crawler.create_users_edge_list("\"ksCrgYQhtFrXgbHAhi9Fo5t0C2I/EPvt4jK7PDLHJPZ17vxy9hpi5II\"")

    # create users network
    network.set_file_name(file_name)
    network.create_network()
    network.compute_page_rank()
    #network.compute_betweenness_centrality()
    network.display_tree()
    #network.display_graph()
    #network.export_to_gexf()

    # end time
    end_time = time.time()
    execution_time = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
    logger.debug("Execution time: " + execution_time)


if __name__ == '__main__':
    main()

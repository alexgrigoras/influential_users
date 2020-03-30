import time
from application.modules.youtube_api import YoutubeAPI
from application.modules.network_analysis import NetworkAnalysis

if __name__ == '__main__':
    keyword = input('Enter a keyword: ')
    nr_videos_str = input('Enter the number of videos: ')
    nr_videos = 0

    try:
        nr_videos = int(nr_videos_str)
    except ValueError:
        print("Invalid number of videos")
        exit()

    crawler = YoutubeAPI()
    network = NetworkAnalysis()

    start_time = time.time()

    crawler.search(keyword, nr_videos)
    crawler.process_results()

    crawler.process_tokens(nr_videos)

    file_path = crawler.create_users_edge_list("\"ksCrgYQhtFrXgbHAhi9Fo5t0C2I/qAjSavC3x9fPWugAxzknLDt5TnM\"")

    network.create_network("data/network_hGRqbqLDkL")

    end_time = time.time()
    execution_time = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
    print("Execution time: " + execution_time)

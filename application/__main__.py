from application.modules.youtube_api import YoutubeAPI


if __name__ == '__main__':
    keyword = input('Enter a keyword: ')
    nr_videos = input('Enter the number of videos: ')

    crawler = YoutubeAPI()

    crawler.search(keyword, nr_videos)
    crawler.process_results()

    crawler.process_tokens(nr_videos)

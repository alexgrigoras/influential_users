import json
import math
import os
import pickle
from application.modules.database import Database
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
DEVELOPER_KEY = os.getenv('GOOGLE_DEV_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YoutubeAPI:
    def __init__(self):
        self.__auth_service = self.__authentication_service()
        self.__db = Database()
        self.__max_results = 0
        self.search_results = []
        self.channel_statistics = []
        self.videos = []
        self.video_statistics = []
        self.comments = []
        self.remaining_tokens = []

    def search(self, keyword, nr_results=50, order='relevance', page_token=None, search_type='keyword',
               location_radius='100km', content_type=None):
        print("Searching resources by keyword [" + keyword + "]:")

        if not keyword:
            print("Empty keyword")
            return

        nr_pages = 1
        self.__max_results = 50
        if 50 < nr_results < 1000:
            nr_pages = math.ceil(nr_results / 50)
        else:
            self.__max_results = nr_results

        if order not in ['date', 'rating', 'relevance', 'title', 'videoCount', 'viewCount']:
            print("Invalid order")
            return

        if content_type is None:
            content_type = ['video', 'channel', 'playlist']
            for ct in content_type:
                if ct not in ['video', 'channel', 'playlist']:
                    print("Invalid content type")
                    return
        content_str = ""
        for s in content_type:
            content_str += s + ','

        results = self.__db.get_search_results({
            'keyword': keyword,
            'selectedNrResults': nr_results,
            'order': order,
            'search_type': search_type,
            'location_radius': location_radius,
            'content_type': content_type
        })

        if results:
            print("Getting cached search with keyword: " + keyword)
            self.search_results = results.next()
        else:
            print("Requesting data from youtube api")

            if search_type is 'keyword':
                results, etag, total_results = self.__get_search_results(nr_pages, q=keyword, part='id,snippet',
                                                                         maxResults=self.__max_results, order=order,
                                                                         type=content_str)
            elif search_type is 'location':
                results, etag, total_results = self.__get_search_results(nr_pages, location=keyword, part='id,snippet',
                                                                         maxResults=self.__max_results, order=order,
                                                                         type=content_str)
            else:
                print("Invalid search parameters")
                return

            self.search_results.append({
                '_id': etag,
                'keyword': keyword,
                'totalResults': total_results,
                'selectedNrResults': nr_results,
                'order': order,
                'search_type': search_type,
                'location_radius': location_radius,
                'content_type': content_type,
                'results': results
            })

            self.__db.insert_search_results(self.search_results)

    def process_results(self):
        videos_list = []
        channels_list = []

        if not self.search_results:
            print("Search results are empty")
            return

        for item in self.search_results['results']:
            title = item['snippet']['title']
            description = item['snippet']['description']
            published_at = item['snippet']['publishedAt']
            kind = item['id']['kind']

            if kind == 'youtube#channel':
                print(" > Channel: " + title)

                channel_id = item['id']['channelId']
                channels_list.append(channel_id)

                playlists = self.__get_channel_playlists(
                    part='snippet',
                    channelId=channel_id,
                    maxResults=50
                )
                for pl in playlists:
                    self.__get_playlist_videos(
                        part='snippet',
                        playlistId=pl['_id'],
                        maxResults=50
                    )

                self.__db.insert_channel({
                    "_id": channel_id,
                    "title": title,
                    "description": description,
                    "publishedAt": published_at,
                    "statistics": [],
                    "playlists": playlists
                })

            if kind == 'youtube#playlist':
                print(" > Playlist: " + title)

                playlist_id = item['id']['playlistId']

                self.__get_playlist_videos(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50
                )

            elif kind == 'youtube#video':
                print(" > Video: " + title)

                video_id = item['id']['videoId']
                channel_id = item['snippet']['channelId']
                videos_list.append(video_id)

                self.__db.insert_video({
                    "_id": video_id,
                    "channelId": channel_id,
                    "title": title,
                    "description": description,
                    "publishedAt": published_at,
                    "statistics": [],
                    "comments": []
                })

                self.__get_video_comments(
                    part='snippet,replies',
                    videoId=video_id,
                    textFormat='plainText',
                    maxResults=100,
                    order='time'
                )

        videos_id_str = ""
        for vid in videos_list:
            videos_id_str += vid + ','
        self.__get_video_statistics(part='statistics', id=videos_id_str, maxResults=self.__max_results)

        channels_id_str = ""
        for cid in channels_list:
            channels_id_str += cid + ','
        self.__get_channel_statistics(part='statistics', id=channels_id_str, maxResults=50)

        self.__db.insert_remaining_tokens(self.remaining_tokens)

    def __get_search_results(self, nr_pages, **kwargs):
        index = 0
        results = []
        final_results = []
        temp_token = {}

        try:
            results = self.__auth_service.search().list(**kwargs).execute()
        except HttpError:
            print("HTTP error")

        if results:
            etag = results['etag']
            total_results = results['pageInfo']['totalResults']

        while results and index < nr_pages:
            final_results.extend(results['items'])

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    'type': 'search',
                    'last_token': results['nextPageToken']
                }
                try:
                    results = self.__auth_service.search().list(**kwargs).execute()
                    index += 1
                except HttpError:
                    print("HTTP error")
            else:
                break

        self.remaining_tokens.append(temp_token)

        return final_results, etag, total_results

    def __get_channel_statistics(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}

        try:
            results = self.__auth_service.channels().list(**kwargs).execute()
        except HttpError:
            print("HTTP error")
        while results:
            for item in results['items']:
                cid = item['id']
                statistics = {
                    'statistics': {
                        'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                        'subscriberCount': item['statistics']['subscriberCount'] if 'subscriberCount' in item[
                            'statistics'] else 0,
                        'videoCount': item['statistics']['videoCount'] if 'videoCount' in item['statistics'] else 0,
                        'commentCount': item['statistics']['commentCount'] if 'commentCount' in item['statistics'] else 0
                    }
                }
                self.__db.insert_video_statistics(cid, statistics)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    'type': 'channels',
                    'last_token': results['nextPageToken']
                }
                try:
                    results = self.__auth_service.channels().list(**kwargs).execute()
                except HttpError:
                    print("HTTP error")
            else:
                break

        self.remaining_tokens.append(temp_token)

    def __get_channel_playlists(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}

        try:
            results = self.__auth_service.playlists().list(**kwargs).execute()
        except HttpError:
            print("HTTP error")
        while results:
            for item in results['items']:
                playlists = {
                    '_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description']
                }
                final_results.append(playlists)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    'type': 'search',
                    'last_token': results['nextPageToken']
                }
                try:
                    results = self.__auth_service.playlists().list(**kwargs).execute()
                except HttpError:
                    print("HTTP error")
            else:
                break

        self.remaining_tokens.append(temp_token)

        return final_results

    def __get_playlist_videos(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}

        try:
            results = self.__auth_service.playlistItems().list(**kwargs).execute()
        except HttpError:
            print("HTTP error")
        while results:
            for item in results['items']:
                video = {
                    '_id': item['snippet']['resourceId']['videoId'],
                    'channelId': item['snippet']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'publishedAt': item['snippet']['publishedAt'],
                    'statistics': [],
                    'comments': []
                }
                self.__db.insert_video(video)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    'type': 'search',
                    'last_token': results['nextPageToken']
                }
                try:
                    results = self.__auth_service.playlistItems().list(**kwargs).execute()
                except HttpError:
                    print("HTTP error")
            else:
                break

        self.remaining_tokens.append(temp_token)

        return final_results

    def __get_video_statistics(self, **kwargs):
        results = []
        temp_token = {}

        try:
            results = self.__auth_service.videos().list(**kwargs).execute()
        except HttpError:
            print("HTTP error")
        while results:
            for item in results['items']:
                vid = item['id']
                statistics = {
                    'statistics': {
                        'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                        'likeCount': item['statistics']['likeCount'] if 'likeCount' in item['statistics'] else 0,
                        'dislikeCount': item['statistics']['dislikeCount'] if 'dislikeCount' in item['statistics'] else 0,
                        'favoriteCount': item['statistics']['favoriteCount'] if 'favoriteCount' in item[
                            'statistics'] else 0,
                        'commentCount': item['statistics']['commentCount'] if 'commentCount' in item['statistics'] else 0
                    }
                }
                self.__db.insert_video_statistics(vid, statistics)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    'type': 'search',
                    'last_token': results['nextPageToken']
                }
                try:
                    results = self.__auth_service.videos().list(**kwargs).execute()
                except HttpError:
                    print("HTTP error")
            else:
                break

        self.remaining_tokens.append(temp_token)

    def __get_video_comments(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}
        nr_pages = 20
        index = 0

        try:
            results = self.__auth_service.commentThreads().list(**kwargs).execute()
        except HttpError:
            print("HTTP error")
        while results and index < nr_pages:
            for item in results['items']:
                cid = item['id']
                self.__db.insert_comment(cid, {
                    'videoId': item['snippet']['topLevelComment']['snippet']['videoId'],
                    'authorName': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'authorId': item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                        if 'authorChannelId' in item['snippet']['topLevelComment']['snippet'] else "",
                    'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'likeCount': item['snippet']['topLevelComment']['snippet']['likeCount'],
                    'publishedAt': item['snippet']['topLevelComment']['snippet']['publishedAt']
                })
                if 'replies' in item:
                    for r_item in item['replies']['comments']:
                        cid = item['id']
                        self.__db.insert_comment(cid, {
                            'videoId': item['snippet']['topLevelComment']['snippet']['videoId'],
                            'authorName': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            'authorId': item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                            if 'authorChannelId' in item['snippet']['topLevelComment']['snippet'] else "",
                            'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                            'likeCount': item['snippet']['topLevelComment']['snippet']['likeCount'],
                            'publishedAt': item['snippet']['topLevelComment']['snippet']['publishedAt']
                        })
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    'type': 'search',
                    'last_token': results['nextPageToken']
                }
                try:
                    results = self.__auth_service.commentThreads().list(**kwargs).execute()
                    index += 1
                except HttpError:
                    print("HTTP error")
            else:
                break

        self.remaining_tokens.append(temp_token)

        return final_results

    @staticmethod
    def __authentication_service():
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    @staticmethod
    def __write_json_to_file(data, file_name):
        json_data = json.dumps(data, indent=4)
        f = open("../data/" + file_name + ".json", "w")
        f.write(json_data)
        f.close()

    @staticmethod
    def __read_cache(keyword):
        path = "../data/cache/" + keyword + ".pickle"
        if os.path.isfile(path):
            with open(path, "rb") as f:
                try:
                    print("Using cached search result for keyword: " + keyword)
                    return pickle.load(f)
                except Exception as e:
                    print(e)
                    return None
        else:
            return None

    @staticmethod
    def __write_cache(keyword, data):
        path = "../data/cache/" + keyword
        os.makedirs(path)
        extension = ".pickle"
        with open(path + extension, "w+") as f:
            pickle.dump(data, f)
        return data


if __name__ == '__main__':
    # keyword = input('Enter a keyword: ')
    search_keyword = 'dji'

    nr_videos = 10

    api = YoutubeAPI()

    api.search(search_keyword, nr_videos)
    api.process_results()

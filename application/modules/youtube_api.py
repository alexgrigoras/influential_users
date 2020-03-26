import os
import math
import json
import pickle

from dotenv import load_dotenv
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

load_dotenv()
DEVELOPER_KEY = os.getenv('GOOGLE_DEV_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YoutubeAPI:
    def __init__(self):
        self.__auth_service = self.__authentication_service()
        self.channels = []
        self.channel_statistics = []
        self.videos = []
        self.video_statistics = []
        self.comments = []

    def search(self, **kwargs):
        print("Searching videos by keyword [" + kwargs.get("k") + "]:")

        keyword = ""

        if "k" in kwargs.keys():
            keyword = kwargs.get("k")
        elif "l" in kwargs.keys():
            search_location = kwargs.get("l")
        else:
            print("Invalid search parameters")
            return

        nr_pages = 1
        max_results = 50
        if "nr" in kwargs.keys():
            nr_of_results = kwargs.get("nr")
            if nr_of_results > 50:
                nr_pages = math.ceil(nr_of_results / 50)
            else:
                max_results = nr_of_results

        if "order" in kwargs.keys():
            order = kwargs.get("order")
        else:
            order = "relevance"

        results = self.__read_cache(keyword)

        if results is None:
            results = self.__get_results(nr_pages, q=keyword, part='id,snippet', eventType='completed',
                                         type='video', maxResults=max_results, order=order)
            self.__write_cache(keyword, results)

        videos_list = []
        channels_list = []

        for item in results:
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

                playlist_videos = []
                for pl in playlists:
                    playlist_videos = self.__get_playlist_videos(
                        part='snippet',
                        playlistId=pl['id'],
                        maxResults=50
                    )
                self.videos.extend(playlist_videos)

                self.channels.append({
                    "_id": channel_id,
                    "title": title,
                    "description": description,
                    "publishedAt": published_at,
                    "playlists": playlists
                })

            elif kind == 'youtube#video':
                print(" > Video: " + title)

                video_id = item['id']['videoId']
                channel_id = item['snippet']['channelId']

                videos_list.append(video_id)

                self.videos.append({
                    "_id": video_id,
                    "channelId": channel_id,
                    "title": title,
                    "description": description,
                    "publishedAt": published_at,
                })

                self.comments = self.__get_video_comments(
                    part='snippet,replies',
                    videoId=video_id,
                    textFormat='plainText',
                    maxResults=100,
                    order='time'
                )

        videos_id_str = ""
        for vid in videos_list:
            videos_id_str += vid + ','
        self.video_statistics = self.__get_video_statistics(part='statistics', id=videos_id_str, maxResults=max_results)

        channels_id_str = ""
        for cid in channels_list:
            channels_id_str += cid + ','
        self.channel_statistics = self.__get_channel_statistics(part='statistics', id=channels_id_str, maxResults=50)

        channels_id_str = ""
        for cid in channels_list:
            channels_id_str += cid + ','
        self.channel_statistics = self.__get_channel_statistics(part='statistics', id=channels_id_str, maxResults=50)

        self.__write_json_to_file(self.channels, "channels")
        self.__write_json_to_file(self.channel_statistics, "channelStatistics")
        self.__write_json_to_file(self.videos, "videos")
        self.__write_json_to_file(self.video_statistics, "videoStatistics")
        self.__write_json_to_file(self.comments, "comments")

    def __get_results(self, nr_pages, **kwargs):
        final_results = []
        index = 0

        results = []
        try:
            results = self.__auth_service.search().list(**kwargs).execute()
        except HttpError:
            print("HTTP error - invalid filter parameter")
        while results and index < nr_pages:
            final_results.extend(results['items'])
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.__auth_service.search().list(**kwargs).execute()
                index += 1
            else:
                break

        return final_results

    def __get_channel_statistics(self, **kwargs):
        final_results = []

        results = []
        try:
            results = self.__auth_service.channels().list(**kwargs).execute()
        except HttpError:
            print("HTTP error - invalid filter parameter")
        while results:
            for item in results['items']:
                details = {
                    '_id': item['id'],
                    'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                    'subscriberCount': item['statistics']['subscriberCount'] if 'subscriberCount' in item['statistics'] else 0,
                    'videoCount': item['statistics']['videoCount'] if 'videoCount' in item['statistics'] else 0,
                    'commentCount': item['statistics']['commentCount'] if 'commentCount' in item['statistics'] else 0
                }
                final_results.append(details)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.__auth_service.channels().list(**kwargs).execute()
            else:
                break

        return final_results

    def __get_channel_playlists(self, **kwargs):
        final_results = []

        results = []
        try:
            results = self.__auth_service.playlists().list(**kwargs).execute()
        except HttpError:
            print("HTTP error - invalid filter parameter")
        while results:
            for item in results['items']:
                details = {
                    '_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description']
                }
                final_results.append(details)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.__auth_service.playlists().list(**kwargs).execute()
            else:
                break

        return final_results

    def __get_playlist_videos(self, **kwargs):
        final_results = []

        results = []
        try:
            results = self.__auth_service.playlistItems().list(**kwargs).execute()
        except HttpError:
            print("HTTP error - invalid filter parameter")
        while results:
            for item in results['items']:
                details = {
                    '_id': item['snippet']['resourceId']['videoId'],
                    'channelId': item['snippet']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'publishedAt': item['snippet']['publishedAt']
                }
                final_results.append(details)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.__auth_service.playlistItems().list(**kwargs).execute()
            else:
                break

        return final_results

    def __get_video_statistics(self, **kwargs):
        final_results = []

        results = []
        try:
            results = self.__auth_service.videos().list(**kwargs).execute()
        except HttpError:
            print("HTTP error - invalid filter parameter")
        while results:
            for item in results['items']:
                details = {
                    '_id': item['id'],
                    'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                    'likeCount': item['statistics']['likeCount'] if 'likeCount' in item['statistics'] else 0,
                    'dislikeCount': item['statistics']['dislikeCount'] if 'dislikeCount' in item['statistics'] else 0,
                    'favoriteCount': item['statistics']['favoriteCount'] if 'favoriteCount' in item['statistics'] else 0,
                    'commentCount': item['statistics']['commentCount'] if 'commentCount' in item['statistics'] else 0
                }
                final_results.append(details)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.__auth_service.videos().list(**kwargs).execute()
            else:
                break

        return final_results

    def __get_video_comments(self, **kwargs):
        comments = []
        try:
            results = self.__auth_service.commentThreads().list(**kwargs).execute()
        except HttpError:
            print("Cannot download comments!")
            results = []

        nr_pages = 10
        index = 0
        while results and index < nr_pages:
            for item in results['items']:
                comments.append({
                    '_id': item['id'],
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
                        comments.append({
                            '_id': r_item['id'],
                            'videoId': r_item['snippet']['videoId'],
                            'authorName': r_item['snippet']['authorDisplayName'],
                            'authorId': r_item['snippet']['authorChannelId']['value'],
                            'text': r_item['snippet']['textDisplay'],
                            'likeCount': r_item['snippet']['likeCount'],
                            'publishedAt': r_item['snippet']['publishedAt']
                        })
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.__auth_service.commentThreads().list(**kwargs).execute()
                index += 1
            else:
                break

        return comments

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
        path = "../data/cache/" + keyword + ".pickle"
        with open(path, "wb") as f:
            pickle.dump(data, f)
        return data


if __name__ == '__main__':
    # keyword = input('Enter a keyword: ')
    search_keyword = "linus tech tips"

    nr_results = 5

    api = YoutubeAPI()

    api.search(k=search_keyword, nr=nr_results, order='relevance')
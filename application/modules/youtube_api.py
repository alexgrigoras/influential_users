import csv
import os
import math
import json
import itertools
from dotenv import load_dotenv

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

"""
Taken from https://python.gotrained.com/youtube-api-extracting-comments/
"""

load_dotenv()
DEVELOPER_KEY = os.getenv('GOOGLE_DEV_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YoutubeAPI:
    def __init__(self):
        self.auth_service = self.__authentication_service()
        self.channels = []
        self.videos = []
        self.comments = []

    @staticmethod
    def __authentication_service():
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    @staticmethod
    def __write_json_to_file(data, file_name):
        json_data = json.dumps(data, indent=4)
        f = open("../data/" + file_name + ".json", "w")
        f.write(json_data)
        f.close()

    def __get_video_comments(self, **kwargs):
        comments = []
        try:
            results = self.auth_service.commentThreads().list(**kwargs).execute()
        except HttpError:
            print("Cannot download comments!")
            results = []

        while results:
            for item in results['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)

            # Check if another page exists
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.auth_service.commentThreads().list(**kwargs).execute()
            else:
                break

        return comments

    def __get_video_details(self, **kwargs):
        final_results = []

        results = self.auth_service.videos().list(**kwargs).execute()

        while results:
            for item in results['items']:
                details = {
                    'video_id': item['id'],
                    'view_count': item['statistics']['viewCount'],
                    'like_count': item['statistics']['likeCount'],
                    'dislike_count': item['statistics']['dislikeCount'],
                    'favorite_count': item['statistics']['favoriteCount'],
                    'comment_count': item['statistics']['commentCount']
                }

                final_results.append(details)

            # Check if another page exists
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.auth_service.videos().list(**kwargs).execute()
            else:
                break

        return final_results

    def __get_videos(self, nr_pages, **kwargs):
        final_results = []
        index = 0

        results = self.auth_service.search().list(**kwargs).execute()

        while results and index < nr_pages:
            final_results.extend(results['items'])

            # Check if another page exists
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.auth_service.search().list(**kwargs).execute()
                index += 1
            else:
                break

        return final_results

    def search_videos(self, **kwargs):
        print("Searching videos by keyword [" + kwargs.get("k") + "]:")

        search_keyword = ""

        if "k" in kwargs.keys():
            search_keyword = kwargs.get("k")
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

        results = self.__get_videos(nr_pages, q=search_keyword, part='id,snippet', eventType='completed', type='video',
                                    maxResults=max_results, order=order)

        videos_list = []

        for item in results:
            title = item['snippet']['title']
            description = item['snippet']['description']
            published_at = item['snippet']['publishedAt']
            kind = item['id']['kind']

            if kind == 'youtube#channel':
                print(" > Channel: " + title)

                channel_id = item['id']['channelId']
                self.channels.append({
                    "id": channel_id,
                    "title": title,
                    "description": description,
                    "published_at": published_at
                })
            elif kind == 'youtube#video':
                print(" > Video: " + title)

                video_id = item['id']['videoId']
                channel_id = item['snippet']['channelId']

                videos_list.append(video_id)

                self.videos.append({
                    "id": video_id,
                    "channel_id": channel_id,
                    "title": title,
                    "description": description,
                    "published_at": published_at,
                })

                comments = self.__get_video_comments(part='snippet,replies', videoId=video_id, textFormat='plainText',
                                                     maxResults=100, order='time')
                for comment in comments:
                    self.comments.append({
                        "video_id": video_id,
                        "comment": comment
                    })

        videos_id_str = ""
        for vid in videos_list:
            videos_id_str += vid + ','
        details = self.__get_video_details(part='statistics', id=videos_id_str, maxResults=max_results)

        self.__write_json_to_file(self.channels, "channels")
        self.__write_json_to_file(self.videos, "videos")
        self.__write_json_to_file(self.comments, "comments")


if __name__ == '__main__':
    keyword = input('Enter a keyword: ')

    nr_results = 5

    api = YoutubeAPI()

    api.search_videos(k=keyword, nr=nr_results, order='relevance')

import math
import os

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from application.modules.mongodb import MongoDB

load_dotenv()
DEVELOPER_KEY = os.getenv('GOOGLE_DEV_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YoutubeAPI():
    def __init__(self):
        self.__db = MongoDB()
        self.__max_results = 0
        self.search_results = []

        self.__get_authentication_service()

    def search(self, keyword, nr_results=50, order='relevance', page_token="", search_type='keyword',
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

        if search_type not in ['keyword', 'location']:
            print("Invalid search type")
            return

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

        search_query = {
            'keyword': keyword,
            'pageToken': page_token,
            'selectedNrResults': nr_results,
            'order': order,
            'search_type': search_type,
            'location_radius': location_radius,
            'content_type': content_type
        }

        self.search_results = self.__check_cache(search_query)

        if not self.search_results:
            print("Requesting data from youtube api")

            if search_type is 'keyword':
                results, etag, total_results = self.__get_search_results(nr_pages, q=keyword, part='id,snippet',
                                                                         maxResults=self.__max_results, order=order,
                                                                         type=content_str, pageToken=page_token)
            elif search_type is 'location':
                results, etag, total_results = self.__get_search_results(nr_pages, location=keyword, part='id,snippet',
                                                                         maxResults=self.__max_results, order=order,
                                                                         type=content_str, pageToken=page_token,
                                                                         locationRadius=location_radius)
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

            self.__write_cache()

    def process_results(self):
        videos_list = []
        channels_list = []

        if not self.search_results:
            print("Search results are empty")
            return

        for item in self.search_results[0]['results']:
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
                    "statistics": []
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

    def __get_search_results(self, nr_pages, **kwargs):
        index = 0
        results = []
        final_results = []
        temp_token = {}
        etag = ""
        total_results = 0

        try:
            results = self.__service.search().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))

        if results:
            etag = results['etag']
            total_results = results['pageInfo']['totalResults']

        while results and index < nr_pages:
            final_results.extend(results['items'])

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    '_id': results['nextPageToken'],
                    'keyword': kwargs['q'],
                    'type': 'search',
                    'query': kwargs
                }
                try:
                    results = self.__service.search().list(**kwargs).execute()
                    index += 1
                except HttpError as e:
                    print("HTTP error: " + str(e))
            else:
                break

        if temp_token:
            self.__db.insert_remaining_token(temp_token)

        return final_results, etag, total_results

    def __get_channel_statistics(self, **kwargs):
        results = []
        temp_token = {}

        try:
            results = self.__service.channels().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
        while results:
            for item in results['items']:
                cid = item['id']
                statistics = {
                    'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                    'subscriberCount': item['statistics']['subscriberCount'] if 'subscriberCount' in item[
                        'statistics'] else 0,
                    'videoCount': item['statistics']['videoCount'] if 'videoCount' in item['statistics'] else 0,
                    'commentCount': item['statistics']['commentCount'] if 'commentCount' in item[
                        'statistics'] else 0
                }
                self.__db.insert_video_statistics(cid, statistics)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    '_id': results['nextPageToken'],
                    'type': 'channel_statistics',
                    'query': kwargs
                }
                try:
                    results = self.__service.channels().list(**kwargs).execute()
                except HttpError as e:
                    print("HTTP error: " + str(e))
            else:
                break

        if temp_token:
            self.__db.insert_remaining_token(temp_token)

    def __get_channel_playlists(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}

        try:
            results = self.__service.playlists().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
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
                    '_id': results['nextPageToken'],
                    'type': 'channel_playlists',
                    'query': kwargs
                }
                try:
                    results = self.__service.playlists().list(**kwargs).execute()
                except HttpError as e:
                    print("HTTP error: " + str(e))
            else:
                break

        if temp_token:
            self.__db.insert_remaining_token(temp_token)

        return final_results

    def __get_playlist_videos(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}

        try:
            results = self.__service.playlistItems().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
        while results:
            for item in results['items']:
                video = {
                    '_id': item['snippet']['resourceId']['videoId'],
                    'channelId': item['snippet']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'publishedAt': item['snippet']['publishedAt'],
                    'statistics': [],
                }
                self.__db.insert_video(video)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    '_id': results['nextPageToken'],
                    'type': 'playlist_videos',
                    'query': kwargs
                }
                try:
                    results = self.__service.playlistItems().list(**kwargs).execute()
                except HttpError as e:
                    print("HTTP error: " + str(e))
            else:
                break

        if temp_token:
            self.__db.insert_remaining_token(temp_token)

        return final_results

    def __get_video_statistics(self, **kwargs):
        results = []
        temp_token = {}

        try:
            results = self.__service.videos().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
        while results:
            for item in results['items']:
                vid = item['id']
                statistics= {
                    'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                    'likeCount': item['statistics']['likeCount'] if 'likeCount' in item['statistics'] else 0,
                    'dislikeCount': item['statistics']['dislikeCount'] if 'dislikeCount' in item[
                        'statistics'] else 0,
                    'favoriteCount': item['statistics']['favoriteCount'] if 'favoriteCount' in item[
                        'statistics'] else 0,
                    'commentCount': item['statistics']['commentCount'] if 'commentCount' in item[
                        'statistics'] else 0
                }
                self.__db.insert_video_statistics(vid, statistics)

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    '_id': results['nextPageToken'],
                    'type': 'video_statistics',
                    'query': kwargs
                }
                try:
                    results = self.__service.videos().list(**kwargs).execute()
                except HttpError as e:
                    print("HTTP error: " + str(e))
            else:
                break

        if temp_token:
            self.__db.insert_remaining_token(temp_token)

    def __get_video_comments(self, **kwargs):
        results = []
        final_results = []
        temp_token = {}
        nr_pages = 50
        index = 0

        try:
            results = self.__service.commentThreads().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
        while results and index < nr_pages:
            for item in results['items']:
                cid = item['id']
                self.__db.insert_comment({
                    '_id': item['id'],
                    'videoId': item['snippet']['topLevelComment']['snippet']['videoId'],
                    'authorName': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'authorId': item['snippet']['topLevelComment']['snippet']['authorChannelId']['value']
                        if 'authorChannelId' in item['snippet']['topLevelComment']['snippet'] else "",
                    'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'likeCount': item['snippet']['topLevelComment']['snippet']['likeCount'],
                    'publishedAt': item['snippet']['topLevelComment']['snippet']['publishedAt'],
                    'replies': []
                })
                if 'replies' in item:
                    for r_item in item['replies']['comments']:
                        self.__db.insert_comment_reply(cid, {
                            '_id': r_item['id'],
                            'videoId': r_item['snippet']['videoId'],
                            'authorName': r_item['snippet']['authorDisplayName'],
                            'authorId': r_item['snippet']['authorChannelId']['value']
                                if 'authorChannelId' in r_item['snippet'] else "",
                            'text': r_item['snippet']['textDisplay'],
                            'likeCount': r_item['snippet']['likeCount'],
                            'publishedAt': r_item['snippet']['publishedAt']
                        })
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                temp_token = {
                    '_id': results['nextPageToken'],
                    'type': 'video_comments',
                    'query': kwargs
                }
                try:
                    results = self.__service.commentThreads().list(**kwargs).execute()
                    index += 1
                except HttpError as e:
                    print("HTTP error: " + str(e))
            else:
                break

        if temp_token:
            self.__db.insert_remaining_token(temp_token)

        return final_results

    def __get_authentication_service(self):
        self.__service = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    def __check_cache(self, query):
        results = self.__db.get_search_results(query)

        if results:
            print("Getting cached search with keyword: " + query['keyword'])
            return results.next()
        else:
            return []

    def __write_cache(self):
        self.__db.insert_search_results(self.search_results)

    def process_tokens(self, nr_results, content_type=None, location_radius=None, order=None):
        tokens = self.__db.get_tokens()
        if tokens:
            print("Processing remaining page tokens")
            for t in tokens:
                token_type = t['type']
                args = t['query']
                token_id = t['_id']
                args['page_token'] = token_id

                if token_type is "search":
                    print("search")
                    keyword = t['keyword']
                    if 'q' in t['query']:
                        self.search(keyword, nr_results, location_radius=location_radius, order=order,
                                    search_type='keyword', page_token=token_id, content_type=content_type)
                    elif 'location' in t['query']:
                        self.search(keyword, nr_results, location_radius=location_radius, order=order,
                                    search_type='location', page_token=token_id, content_type=content_type)

                elif token_type is 'channel_statistics':
                    print("channel_statistics")
                    self.__get_channel_statistics(**args)

                elif token_type is 'channel_playlists':
                    print("channel_playlists")
                    self.__get_channel_playlists(**args)

                elif token_type is 'playlist_videos':
                    print("playlist_videos")
                    self.__get_playlist_videos(**args)

                elif token_type is 'video_statistics':
                    print("video_statistics")
                    self.__get_video_statistics(**args)

                elif token_type is 'video_comments':
                    print("video_comments")
                    self.__get_video_comments(**args)

                self.__db.remove_token(token_id)

import math
import os
import pickle
import random
import string
from datetime import datetime

import httplib2
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from influential_users.modules.message_logger import MessageLogger
from influential_users.modules.mongodb import MongoDB

load_dotenv()
DEVELOPER_KEY = os.getenv('GOOGLE_DEV_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

STRING_LENGTH = 10
NETWORKS_FOLDER = '.networks'
TEXT_EXTENSION = '.txt'
OBJECT_EXTENSION = '.pickle'


class YoutubeAPI:
    """

    """

    """ Init """

    def __init__(self):
        """

        """

        # logging module
        ml = MessageLogger('youtube_api')
        self.logger = ml.get_logger()

        self.__db = MongoDB()  # mongodb driver
        self.__max_results = 0  # the maximum number of results
        self.__get_authentication_service()  # get the authentication service for youtube api

    """ Get data from Youtube API"""

    def search(self, keyword, nr_results=50, order='relevance', page_token="", search_type='keyword',
               location_radius='100km', content_type=None):
        """

        :param keyword:
        :param nr_results:
        :param order:
        :param page_token:
        :param search_type:
        :param location_radius:
        :param content_type:
        :return:
        """

        print("Searching resources by keyword [" + keyword + "]:")

        if not keyword:
            print("Empty keyword")
            return False

        nr_pages = 1
        self.__max_results = 50
        if 50 < nr_results < 10000:
            nr_pages = math.ceil(nr_results / 50)
        else:
            self.__max_results = nr_results

        if search_type not in ['keyword', 'location']:
            print("Invalid search type")
            return False

        if order not in ['date', 'rating', 'relevance', 'title', 'videoCount', 'viewCount']:
            print("Invalid order")
            return False

        if content_type is None:
            content_type = ['video', 'channel', 'playlist']
            for ct in content_type:
                if ct not in ['video', 'channel', 'playlist']:
                    print("Invalid content type")
                    return False
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

        search_results = self.__check_search_cache(search_query)

        if not search_results:
            print("Requesting .networks from youtube api")

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
                return False

            if results is False:
                print("Data cannot be obtained")
                return False

            search_results.append({
                '_id': etag,
                'keyword': keyword,
                'totalResults': total_results,
                'selectedNrResults': nr_results,
                'order': order,
                'search_type': search_type,
                'location_radius': location_radius,
                'content_type': content_type,
                "retrieval date": datetime.utcnow(),
                'results': results
            })

            self.__write_search_cache(search_results)

        return search_results

    def __get_search_results(self, nr_pages, **kwargs):
        """

        :param nr_pages:
        :param kwargs:
        :return:
        """

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
            return

        if results:
            etag = results['etag']
            etag = etag.replace("\"", "")
            total_results = results['pageInfo']['totalResults']

        while results and index < nr_pages:
            final_results.extend(results['items'])

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                try:
                    results = self.__service.search().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'keyword': kwargs['q'],
                        'type': 'search',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                    index += 1
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return final_results, etag, total_results

    def get_channel_statistics(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        temp_token = {}

        try:
            results = self.__service.channels().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
            return False
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
                try:
                    results = self.__service.channels().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'type': 'channel_statistics',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return True

    def get_channel_playlists(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        final_results = []
        temp_token = {}

        try:
            results = self.__service.playlists().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
            return False
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
                try:
                    results = self.__service.playlists().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'type': 'channel_playlists',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return final_results

    def get_playlist_videos(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        final_results = []
        temp_token = {}

        try:
            results = self.__service.playlistItems().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
            return False
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
                try:
                    results = self.__service.playlistItems().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'type': 'playlist_videos',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return final_results

    def get_video_statistics(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        temp_token = {}

        try:
            results = self.__service.videos().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
            return False
        while results:
            for item in results['items']:
                vid = item['id']
                statistics = {
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
                try:
                    results = self.__service.videos().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'type': 'video_statistics',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return True

    def get_video_comments(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        final_results = []
        temp_token = {}
        nr_pages = 50
        index = 0

        try:
            results = self.__service.commentThreads().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
            return False
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
                try:
                    results = self.__service.commentThreads().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'type': 'video_comments',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                    index += 1
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return final_results

    def get_user_channel(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        temp_token = {}

        try:
            results = self.__service.channels().list(**kwargs).execute()
        except HttpError as e:
            print("HTTP error: " + str(e))
            return False
        while results:
            for item in results['items']:
                self.__db.insert_channel({
                    "_id": item['id'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'],
                    "publishedAt": item['snippet']['publishedAt'],
                    "retrieval date": datetime.utcnow(),
                    "statistics": {
                        'viewCount': item['statistics']['viewCount'] if 'viewCount' in item['statistics'] else 0,
                        'subscriberCount': item['statistics']['subscriberCount'] if 'subscriberCount' in item[
                            'statistics'] else 0,
                        'videoCount': item['statistics']['videoCount'] if 'videoCount' in item['statistics'] else 0,
                        'commentCount': item['statistics']['commentCount'] if 'commentCount' in item[
                            'statistics'] else 0
                    }
                })

            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                try:
                    results = self.__service.channels().list(**kwargs).execute()
                    temp_token = {
                        '_id': results['nextPageToken'],
                        'type': 'channel',
                        "retrieval date": datetime.utcnow(),
                        'query': kwargs
                    }
                except HttpError as e:
                    print("HTTP error: " + str(e))
                    return False
            else:
                break

        if temp_token:
            self.__db.insert_token(temp_token)

        return True

    """ Process extracted data """

    def process_search_results(self, search_results):
        """

        :param search_results:
        :return:
        """

        videos_list = []
        channels_list = []

        if not search_results:
            print("Search results are empty")
            return

        for item in search_results[0]['results']:
            title = item['snippet']['title']
            description = item['snippet']['description']
            published_at = item['snippet']['publishedAt']
            kind = item['id']['kind']

            if kind == 'youtube#channel':
                print(" > Channel: " + title)

                channel_id = item['id']['channelId']
                channels_list.append(channel_id)

                playlists = self.get_channel_playlists(
                    part='snippet',
                    channelId=channel_id,
                    maxResults=50
                )
                if playlists is False:
                    return
                for pl in playlists:
                    self.get_playlist_videos(
                        part='snippet',
                        playlistId=pl['_id'],
                        maxResults=50
                    )

                self.__db.insert_channel({
                    "_id": channel_id,
                    "title": title,
                    "description": description,
                    "publishedAt": published_at,
                    "retrieval date": datetime.utcnow(),
                    "playlists": playlists
                })

            if kind == 'youtube#playlist':
                print(" > Playlist: " + title)

                playlist_id = item['id']['playlistId']

                self.get_playlist_videos(
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
                    "retrieval date": datetime.utcnow()
                })

                self.get_video_comments(
                    part='snippet,replies',
                    videoId=video_id,
                    textFormat='plainText',
                    maxResults=100,
                    order='relevance'
                )

        if videos_list:
            videos_id_str = ','.join(videos_list)
            self.get_video_statistics(part='statistics', id=videos_id_str, maxResults=self.__max_results)

        if channels_list:
            channels_id_str = ','.join(channels_list)
            self.get_channel_statistics(part='statistics', id=channels_id_str, maxResults=50)

    def process_tokens(self, nr_results, content_type=None, location_radius=None, order="relevance"):
        """

        :param nr_results:
        :param content_type:
        :param location_radius:
        :param order:
        :return:
        """

        self.__max_results = 50

        tokens = self.__db.get_tokens()

        if tokens and tokens.count() > 0:
            print("Processing remaining page tokens:")
            for t in tokens:
                token_type = t['type']
                args = t['query']
                token_id = t['_id']
                args['pageToken'] = token_id
                result_success = False

                print(" > " + token_type + " token [" + token_id + "]")

                if token_type == "search":
                    keyword = t['keyword']
                    if 'order' in t['query']:
                        order = t['query']['order']
                    if 'q' in t['query']:
                        result_success = self.search(keyword, nr_results, location_radius=location_radius, order=order,
                                                     search_type='keyword', page_token=token_id,
                                                     content_type=content_type)
                    elif 'location' in t['query']:
                        result_success = self.search(keyword, nr_results, location_radius=location_radius, order=order,
                                                     search_type='location', page_token=token_id,
                                                     content_type=content_type)

                elif token_type == 'channel_statistics':
                    result_success = self.get_channel_statistics(**args)

                elif token_type == 'channel_playlists':
                    result_success = self.get_channel_playlists(**args)

                elif token_type == 'playlist_videos':
                    result_success = self.get_playlist_videos(**args)

                elif token_type == 'video_statistics':
                    result_success = self.get_video_statistics(**args)

                elif token_type == 'video_comments':
                    result_success = self.get_video_comments(**args)

                else:
                    pass

                if result_success is not False:
                    print(" > Removing token [" + token_id + "]")
                    self.__db.remove_token(token_id)
        else:
            print("! No remaining tokens")

    def create_users_network(self, search_id):
        """
        Gets data from database and creates a file with the users edge-list
        :param search_id: id (etag) of the search result
        :return: name of the generated file
        """

        videos_list = []
        channels_list = []
        channel_names = {}
        missing_channels = []
        video_channel = {}

        # create file for network and open it for appending data
        file_name = "network_" + self.__random_string(STRING_LENGTH)
        path = NETWORKS_FOLDER + "/"
        while os.path.exists(path + file_name + ".*"):
            file_name = "network_" + self.__random_string(STRING_LENGTH)
        self.logger.info("File name: " + file_name)
        f = open(path + file_name + TEXT_EXTENSION, "a")

        # getting videos list from search
        results = self.__db.get_search_results({'_id': search_id}, {'results': 1})
        if results:
            res = results.next()
            for vid in res['results']:
                if vid["id"]["kind"] == "youtube#video":
                    videos_list.append(vid["id"]["videoId"])
                    channels_list.append(vid["snippet"]["channelId"])
                    video_channel[vid["id"]["videoId"]] = vid["snippet"]["channelId"]
        else:
            self.logger.error("No results for search [" + search_id + "] in database")
            return False

        # checking if channel id from videos exist and make a list with missing channels
        for channel in channels_list:
            channel_result = self.__db.get_channel({'_id': channel}, {'title': 1})
            if channel_result is None:
                missing_channels.append(channel)
            else:
                title = channel_result.next()["title"]
                channel_names[channel] = title

        # get channels list
        if missing_channels:
            print("Getting channel details from Youtube Api")
            channels_id_str = ','.join(missing_channels)
            result_validation = self.get_user_channel(part='snippet,statistics', id=channels_id_str, maxResults=50)

            if result_validation is True:
                # checking if channel id from videos exist
                for channel in channels_list:
                    channel_result = self.__db.get_channel({'_id': channel}, {'title': 1})
                    if channel_result is None:
                        print("Channels is missing: " + channel)
                        return
                    else:
                        title = channel_result.next()["title"]
                        channel_names[channel] = title

        # getting users from comments
        comment_limit = {
            "_id": 0,
            'authorName': 1,
            'authorId': 1,
            'replies': 1
        }
        for vid in videos_list:
            channel_id = video_channel[vid]
            comments = self.__db.get_comments({'videoId': vid}, comment_limit)
            if comments:
                for com in comments:
                    f.write(channel_id + " " + com["authorId"] + "\n")
                    channel_names[com["authorId"]] = com["authorName"]
                    if "replies" in com:
                        for rep in com['replies']:
                            # f.write(ch_id + "," + rep["authorId"] + "\n")
                            f.write(com["authorId"] + " " + rep["authorId"] + "\n")
                            channel_names[rep["authorId"]] = rep["authorName"]
            else:
                channel_names.pop(channel_id)

        # export data to
        pickle.dump(channel_names, open(path + file_name + OBJECT_EXTENSION, "wb"))

        # close file
        f.close()

        return file_name

    """ Authentication for Youtube API """

    def __get_authentication_service(self):
        """

        :return:
        """

        http = httplib2.Http(cache=".cache")
        self.__service = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=http, developerKey=DEVELOPER_KEY,
                               cache_discovery=True)

    """ Search results cache """

    def __check_search_cache(self, query):
        """

        :param query:
        :return:
        """

        results = self.__db.get_search_results(query)
        if results:
            print("Getting cached search with keyword: " + query['keyword'])
            return results.next()
        else:
            return []

    def __write_search_cache(self, search_results):
        """

        :param search_results:
        :return:
        """
        self.__db.insert_search_results(search_results)

    """ Other methods """

    @staticmethod
    def __random_string(string_length):
        """
        Generate a random string with the combination of lowercase and uppercase letters
        :param string_length: the length of the string that is generated
        :return: the generated string
        """

        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(string_length))

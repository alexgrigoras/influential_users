import csv
import os
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

    @staticmethod
    def __authentication_service():
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    def get_video_comments(self, **kwargs):
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

    @staticmethod
    def __write_to_csv(comments):
        with open('../data/comments.csv', 'w') as comments_file:
            comments_writer = csv.writer(comments_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            comments_writer.writerow(['Video ID', 'Title', 'Comment'])
            for row in comments:
                # convert the tuple to a list and write to the output file
                comments_writer.writerow(list(row))

    def get_videos(self, **kwargs):
        final_results = []
        results = self.auth_service.search().list(**kwargs).execute()

        index = 0
        max_pages = 5

        while results and index < max_pages:
            final_results.extend(results['items'])

            # Check if another page exists
            if 'nextPageToken' in results:
                kwargs['pageToken'] = results['nextPageToken']
                results = self.auth_service.search().list(**kwargs).execute()
                index += 1
            else:
                break

        return final_results

    def search_videos_by_keyword(self, **kwargs):
        print("Searching videos:")
        results = self.get_videos(**kwargs)
        final_result = []
        for item in results:
            title = item['snippet']['title']
            video_id = item['id']['videoId']
            print(" > " + title)
            comments = self.get_video_comments(part='snippet', videoId=video_id, textFormat='plainText', maxResults=100)
            # make a tuple consisting of the video id, title, comment and add the result to
            # the final list
            final_result.extend([(video_id, title, comment) for comment in comments])

        self.__write_to_csv(final_result)


if __name__ == '__main__':
    keyword = input('Enter a keyword: ')

    api = YoutubeAPI()

    api.search_videos_by_keyword(q=keyword, part='id,snippet', eventType='completed', type='video')

import pymongo
import json

from pymongo import errors

DATABASE_NAME = "influential_users"


class Database:
    def __init__(self):
        self.__mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

        self.__db = self.__mongo_client[DATABASE_NAME]

        self.__search_results_col = self.__db['searchResults']
        self.__channels_col = self.__db['channels']
        self.__videos_col = self.__db['videos']
        self.__tokens_col = self.__db['tokens']

    @staticmethod
    def read_json(path):
        with open('path') as json_file:
            data = json.load(json_file)

        return data

    def insert_search_results(self, data):
        try:
            self.__search_results_col.insert_many(data)
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")

    def get_search_results(self, query):
        if self.__search_results_col.count_documents(query) > 0:
            return self.__search_results_col.find(query)
        else:
            return None

    def insert_channel(self, data):
        try:
            self.__channels_col.insert_one(data)
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")

    def insert_channel_statistics(self, id, data):
        try:
            self.__channels_col.update_one(
                {'_id': id },
                {'$push': { 'statistics': data } }
            )
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")

    def insert_video(self, data):
        try:
            self.__videos_col.insert_one(data)
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.WriteError:
            print("Bulk write error")

    def insert_videos(self, data):
        try:
            self.__videos_col.insert_many(data)
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")

    def insert_video_statistics(self, id, data):
        try:
            self.__videos_col.update_one(
                {'_id': id },
                {'$push': { 'statistics': data } }
            )
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")

    def insert_comment(self, id, data):
        try:
            self.__videos_col.update_one(
                {'_id': id },
                {'$push': { 'comments': data } }
            )
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")

    def insert_remaining_tokens(self, data):
        try:
            self.__tokens_col.insert_many(data)
        except errors.DuplicateKeyError:
            print("Duplicate key")
        except errors.BulkWriteError:
            print("Bulk write error")


if __name__ == '__main__':
    db = Database()
    db.insert_comment("-2ERtbK8jCU", {
        'text': "test_comment"
    })

import pymongo
from pymongo import errors

DATABASE_NAME = "influential_users"


class MongoDB():
    def __init__(self):
        self.__mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

        self.__db = self.__mongo_client[DATABASE_NAME]

        self.__search_results_col = self.__db['searchResults']
        self.__channels_col = self.__db['channels']
        self.__videos_col = self.__db['videos']
        self.__comments_col = self.__db['comments']
        self.__tokens_col = self.__db['tokens']

    def insert_search_results(self, data):
        try:
            self.__search_results_col.insert_many(data)
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def get_search_results(self, query):
        if self.__search_results_col.count_documents(query) > 0:
            return self.__search_results_col.find(query)
        else:
            return None

    def insert_channel(self, data):
        try:
            self.__channels_col.insert_one(data)
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def insert_channel_statistics(self, id, data):
        try:
            self.__channels_col.update_one(
                {'_id': id},
                {'$set': {'statistics': data}}
            )
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def insert_video(self, data):
        try:
            self.__videos_col.insert_one(data)
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.WriteError:
            #print("Bulk write error")
            pass

    def insert_video_statistics(self, id, data):
        try:
            self.__videos_col.update_one(
                {'_id': id},
                {'$addToSet': {'statistics': data}}
            )
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def insert_comment(self, data):
        try:
            self.__comments_col.insert_one(data)
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def insert_comment_reply(self, id, data):
        try:
            self.__comments_col.update_one(
                {'_id': id},
                {'$addToSet': {'replies': data}}
            )
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def insert_remaining_token(self, data):
        try:
            self.__tokens_col.insert_one(data)
        except errors.DuplicateKeyError:
            #print("Duplicate key")
            pass
        except errors.BulkWriteError:
            #print("Bulk write error")
            pass

    def get_tokens(self):
        tokens = None

        try:
            tokens = self.__tokens_col.find()
        except errors.CursorNotFound:
            print("Cursor not found")

        return tokens

    def remove_token(self, id):
        try:
            self.__tokens_col.delete_one({'_id': id})
        except errors.InvalidId:
            print("Invalid id")

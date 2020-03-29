import pymongo
from pymongo import errors

DATABASE_NAME = "influential_users"
SEARCH_RESULTS_COLLECTION = "search_results"
CHANNELS_COLLECTION = "channels"
VIDEOS_COLLECTION = "videos"
COMMENTS_COLLECTION = "comments"
TOKENS_COLLECTION = "tokens"


class MongoDB:
    def __init__(self):
        self.__mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

        self.__db = self.__mongo_client[DATABASE_NAME]

        self.__search_results_col = self.__db[SEARCH_RESULTS_COLLECTION]
        self.__channels_col = self.__db[CHANNELS_COLLECTION]
        self.__videos_col = self.__db[VIDEOS_COLLECTION]
        self.__comments_col = self.__db[COMMENTS_COLLECTION]
        self.__tokens_col = self.__db[TOKENS_COLLECTION]

    def insert_search_results(self, data):
        try:
            self.__search_results_col.insert_many(data)
        except errors.DuplicateKeyError:
            # print("Duplicate key")
            pass
        except errors.BulkWriteError:
            # print("Bulk write error")
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
            # print("Duplicate key")
            pass
        except errors.BulkWriteError:
            # print("Bulk write error")
            pass

    def insert_channel_statistics(self, channel_id, statistics):
        try:
            self.__channels_col.update_one(
                {'_id': channel_id},
                {'$addToSet': {'statistics': statistics}}
            )
        except errors.DuplicateKeyError:
            # print("Duplicate key")
            pass
        except errors.BulkWriteError:
            # print("Bulk write error")
            pass

    def insert_video(self, data):
        try:
            self.__videos_col.insert_one(data)
        except errors.DuplicateKeyError as e:
            print("Duplicate key: " + str(e))
            pass
        except errors.WriteError as e:
            print("Bulk write error: " + str(e))
            pass

    def insert_video_statistics(self, video_id, data):
        try:
            self.__videos_col.update_one(
                {'_id': video_id},
                {'$set': {'statistics': data}}
            )
        except errors.DuplicateKeyError:
            print("Duplicate key")
            pass
        except errors.BulkWriteError:
            print("Bulk write error")
            pass

    def insert_comment(self, data):
        try:
            self.__comments_col.insert_one(data)
        except errors.DuplicateKeyError:
            # print("Duplicate key")
            pass
        except errors.BulkWriteError:
            # print("Bulk write error")
            pass

    def insert_comment_reply(self, comment_id, replies):
        try:
            self.__comments_col.update_one(
                {'_id': comment_id},
                {'$addToSet': {'replies': replies}}
            )
        except errors.DuplicateKeyError:
            # print("Duplicate key")
            pass
        except errors.BulkWriteError:
            # print("Bulk write error")
            pass

    def insert_token(self, data):
        try:
            self.__tokens_col.insert_one(data)
        except errors.DuplicateKeyError:
            # print("Duplicate key")
            pass
        except errors.BulkWriteError:
            # print("Bulk write error")
            pass

    def get_tokens(self):
        tokens = None

        try:
            tokens = self.__tokens_col.find()
        except errors.CursorNotFound:
            print("Cursor not found")

        return tokens

    def remove_token(self, token_id):
        try:
            self.__tokens_col.delete_one({'_id': token_id})
        except errors.InvalidId:
            print("Invalid id")

import pymongo
from pymongo import errors

from influential_users.modules.message_logger import MessageLogger

DATABASE_NAME = "influential_users"
SEARCH_RESULTS_COLLECTION = "search_results"
CHANNELS_COLLECTION = "channels"
PLAYLISTS_COLLECTION = "playlists"
VIDEOS_COLLECTION = "videos"
COMMENTS_COLLECTION = "comments"
TOKENS_COLLECTION = "tokens"


class MongoDB:
    """

    """

    """ Init """

    def __init__(self):
        """
        Init method for creating the database connection
        """

        # logging module
        ml = MessageLogger('mongodb')
        self.logger = ml.get_logger()

        # connect to database
        try:
            self.__mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
            self.__mongo_client.server_info()
        except errors.ConnectionFailure as e:
            self.logger.critical("MongoDB database: " + str(e))
            exit(1)
        self.__db = self.__mongo_client[DATABASE_NAME]  # database: DATABASE_NAME
        self.__search_results_col = self.__db[SEARCH_RESULTS_COLLECTION]  # collection: SEARCH_RESULTS_COLLECTION
        self.__channels_col = self.__db[CHANNELS_COLLECTION]  # collection: CHANNELS_COLLECTION
        self.__playlists_col = self.__db[PLAYLISTS_COLLECTION]  # collection: PLAYLISTS_COLLECTION
        self.__videos_col = self.__db[VIDEOS_COLLECTION]  # collection: VIDEOS_COLLECTION
        self.__comments_col = self.__db[COMMENTS_COLLECTION]  # collection: COMMENTS_COLLECTION
        self.__tokens_col = self.__db[TOKENS_COLLECTION]  # collection: TOKENS_COLLECTION

    """ Search Results """

    def insert_search_results(self, query):
        """

        :param query:
        :return:
        """
        try:
            self.__search_results_col.insert_many(query)
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def get_search_results(self, query, limit=None):
        """

        :param query:
        :param limit:
        :return:
        """
        if self.__search_results_col.count_documents(query) > 0:
            return self.__search_results_col.find(query, limit)
        else:
            return None

    """ Channels """

    def insert_channel(self, data):
        """

        :param data:
        :return:
        """
        try:
            self.__channels_col.insert_one(data)
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def insert_channel_statistics(self, channel_id, statistics):
        """

        :param channel_id:
        :param statistics:
        :return:
        """
        try:
            self.__channels_col.update_one(
                {'_id': channel_id},
                {'$addToSet': {'statistics': statistics}}
            )
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def get_channel(self, query, limit=None):
        """

        :param query:
        :param limit:
        :return:
        """
        if self.__channels_col.count_documents(query) > 0:
            return self.__channels_col.find(query, limit)
        else:
            return None

    """ Playlists """

    def insert_playlist(self, data):
        """

        :param data:
        :return:
        """
        try:
            self.__playlists_col.insert_one(data)
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    """ Videos """

    def insert_video(self, data):
        """

        :param data:
        :return:
        """
        try:
            self.__videos_col.insert_one(data)
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def insert_video_statistics(self, video_id, data):
        """

        :param video_id:
        :param data:
        :return:
        """
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

    """ Comments """

    def insert_comment(self, data):
        """

        :param data:
        :return:
        """
        try:
            self.__comments_col.insert_one(data)
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def insert_comment_reply(self, comment_id, replies):
        """

        :param comment_id:
        :param replies:
        :return:
        """
        try:
            self.__comments_col.update_one(
                {'_id': comment_id},
                {'$addToSet': {'replies': replies}}
            )
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def get_comments(self, query, limit=None):
        """

        :param query:
        :param limit:
        :return:
        """
        if self.__comments_col.count_documents(query) > 0:
            return self.__comments_col.find(query, limit)
        else:
            return None

    """ Tokens """

    def insert_token(self, data):
        """

        :param data:
        :return:
        """
        try:
            self.__tokens_col.insert_one(data)
        except errors.DuplicateKeyError as e:
            self.logger.info("Duplicate key: " + str(e))
        except errors.BulkWriteError as e:
            self.logger.error("Bulk write error: " + str(e))

    def get_tokens(self):
        """

        :return:
        """
        tokens = None

        try:
            tokens = self.__tokens_col.find()
        except errors.CursorNotFound as e:
            self.logger.error("Cursor not found: " + str(e))

        return tokens

    def remove_token(self, token_id):
        """

        :param token_id:
        :return:
        """
        try:
            self.__tokens_col.delete_one({'_id': token_id})
        except errors.InvalidId as e:
            self.logger.error("Invalid id: " + str(e))

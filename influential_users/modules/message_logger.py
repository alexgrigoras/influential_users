import logging


class MessageLogger:
    """
    Message logger class that logs the data to the console
    """

    def __init__(self, module_name):
        """
        Class constructor - creates a message logger for the module
        :param module_name: the name of the module
        """
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """
        Return the logger object that can be used for logging messages
        :return: logging object
        """
        return self.logger

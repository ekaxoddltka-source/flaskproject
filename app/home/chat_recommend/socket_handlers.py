# app/home/chat_recommend/socket_handlers.py
from flask_socketio import Namespace, emit
import logging

logger = logging.getLogger(__name__)

class ChatRecommendNamespace(Namespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_request_topic(self, data):
        pass


def init_socket_handlers(socketio):
    pass

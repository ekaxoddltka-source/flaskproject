# app/home/chat_recommend/__init__.py
"""
chat_recommend 패키지 초기화용.
앱이 생성될 때 init_app(app, socketio)를 한 번 호출하면
스케줄러 시작 / 필요한 의존성 연결을 여기서 처리합니다.
"""

from . import db, keywords, recommend, scheduler, socket_handlers
import logging
logger = logging.getLogger(__name__)

def init_app(app, socketio):
    """
    앱 시작 시 한 번 호출.
    """
    # app.extensions에 모듈 저장
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['chat_recommend'] = {
        'db': db,
        'keywords': keywords,
        'recommend': recommend,
        'socket_handlers': socket_handlers
    }

    socket_handlers.init_socket_handlers(socketio)

    # scheduler start
    scheduler.start(socketio, app)  # 🔥 app 추가

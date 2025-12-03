# app/__init__.py
import os
from flask import Flask
from flask_socketio import SocketIO
import pymysql
from dotenv import load_dotenv

# -------------------------------------
# SocketIO 초기화
# -------------------------------------
socketio = SocketIO(cors_allowed_origins="*", manage_session=True)

# -------------------------------------
# 환경변수 로드
# -------------------------------------
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
dotenv_path = os.path.join(basedir, 'gemini_API.env')

def load_env():
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"DEBUG: Loaded GEMINI_API_KEY: {os.environ.get('GEMINI_API_KEY', 'MISSING')[:5]}...")
    else:
        print(f"DEBUG: ERROR! .env file NOT FOUND at: {dotenv_path}")

load_env()

# -------------------------------------
# Flask 앱 생성
# -------------------------------------
def create_app():
    app = Flask(__name__)
    
    # 기본 설정
    app.config.update(
        SECRET_KEY='aezen',
        UPLOAD_FOLDER=os.path.join(app.root_path, 'uploads'),
        MYSQL_HOST="192.168.60.136",
        MYSQL_USER="jwh",
        MYSQL_PASSWORD="ezen",
        MYSQL_DB="aezen",
        MYSQL_CURSORCLASS="DictCursor"
    )

    # DB 연결 함수
    def get_db_connection():
        return pymysql.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            db=app.config["MYSQL_DB"],
            cursorclass=pymysql.cursors.DictCursor
        )
    app.get_db_connection = get_db_connection

    # SocketIO 앱 등록
    socketio.init_app(app)

    # 블루프린트 등록
    register_blueprints(app)

    # WebSocket 이벤트 등록
    register_socketio_events()

    # chat_recommend 초기화
    from app.home.chat_recommend import init_app as chat_recommend_init
    chat_recommend_init(app, socketio)

    return app

# -------------------------------------
# 블루프린트 등록 함수
# -------------------------------------
def register_blueprints(app):
    from app.home.routes import bp as home_bp
    from app.account.routes import bp as account_bp
    from app.mypage.routes import bp as mypage_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(mypage_bp)

# -------------------------------------
# SocketIO 이벤트 등록 함수
# -------------------------------------
def register_socketio_events():
    from app.home import events as home_events
    from app.mypage import events as mypage_events

    # 홈(Global Chat)
    socketio.on_event("connect", home_events.handle_connect)
    socketio.on_event("send_message", home_events.handle_message)
    socketio.on_event("disconnect", home_events.handle_disconnect)

    # DM
    socketio.on_event("join_dm", mypage_events.join_dm)
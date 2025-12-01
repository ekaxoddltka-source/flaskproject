# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
import pymysql
import os
from dotenv import load_dotenv

socketio = SocketIO(cors_allowed_origins="*", manage_session=True)

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
dotenv_path = os.path.join(basedir, 'gemini_API.env')

# 🌟 파일이 존재하는지 확인 후 로드 (디버깅에도 도움)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"DEBUG: ERROR! .env file NOT FOUND at: {dotenv_path}")

# load_dotenv() 이후에 키 값 확인 (추가 디버깅)
print(f"DEBUG: Key Loaded in __init__.py: {os.environ.get('GEMINI_API_KEY', 'MISSING')[:5]}...")


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'aezen'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

    # -------------------------------------
    # MySQL 설정
    # -------------------------------------
    app.config["MYSQL_HOST"] = "192.168.60.136"
    app.config["MYSQL_USER"] = "jwh"
    app.config["MYSQL_PASSWORD"] = "ezen"
    app.config["MYSQL_DB"] = "aezen"
    app.config["MYSQL_CURSORCLASS"] = "DictCursor"

    def get_db_connection():
        return pymysql.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            db=app.config["MYSQL_DB"],
            cursorclass=pymysql.cursors.DictCursor
        )

    app.get_db_connection = get_db_connection

    socketio.init_app(app)

    # -------------------------------------
    # 블루프린트 등록
    # -------------------------------------
    from app.home.routes import bp as home_bp
    from app.account.routes import bp as account_bp
    from app.mypage.routes import bp as mypage_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(mypage_bp)

    # -------------------------------------
    # 🔥 WebSocket 이벤트 등록
    # -------------------------------------
    from app.home import events as home_events
    from app.mypage import events as mypage_events

    # ⭐ 홈(Global Chat)
    socketio.on_event("connect", home_events.handle_connect)
    socketio.on_event("send_message", home_events.handle_message)
    socketio.on_event("disconnect", home_events.handle_disconnect)

    # ⭐ DM
    socketio.on_event("join_dm", mypage_events.join_dm)

    return app

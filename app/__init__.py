# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
import pymysql
import os

socketio = SocketIO(cors_allowed_origins="*", manage_session=True)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'aezen'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

    # -------------------------------------
    # MySQL 설정
    # -------------------------------------
    app.config["MYSQL_HOST"] = "192.168.60.187"
    app.config["MYSQL_USER"] = "jwh"
    app.config["MYSQL_PASSWORD"] = "ezen"
    app.config["MYSQL_DB"] = "aezen"
    app.config["MYSQL_CURSORCLASS"] = "DictCursor"

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

    # -------------------------------------
    # SocketIO 초기화
    # -------------------------------------
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
    # 🔥 소켓 이벤트 등록
    # -------------------------------------
    # Global Chat
    from app.home import events as home_events

    # DM Chat (mypage)
    from app.mypage import events as mypage_events

    socketio.on_event("join_dm", mypage_events.join_dm)
    # send_dm_message는 emit 보내기만 하는 함수라 등록 불필요

    return app

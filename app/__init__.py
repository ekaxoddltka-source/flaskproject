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
    # 🔥 MySQL 기본 설정 (pymysql 사용)
    # -------------------------------------
    app.config["MYSQL_HOST"] = "localhost"
    app.config["MYSQL_USER"] = "root"
    app.config["MYSQL_PASSWORD"] = "ezen"
    app.config["MYSQL_DB"] = "aezen"
    app.config["MYSQL_CURSORCLASS"] = "DictCursor"

    # DB 커넥터 함수
    def get_db_connection():
        return pymysql.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            db=app.config["MYSQL_DB"],
            cursorclass=pymysql.cursors.DictCursor
        )

    # Flask app 에 등록
    app.get_db_connection = get_db_connection
    socketio.init_app(app)

    # -------------------------------------
    # 블루프린트 등록
    # -------------------------------------
    from app.home.routes import bp as home_bp
    app.register_blueprint(home_bp)

    from app.account.routes import bp as account_bp
    app.register_blueprint(account_bp)

    from app.mypage.routes import bp as mypage_bp
    app.register_blueprint(mypage_bp)

    # 웹소켓 이벤트 등록
    from app.home import events

    return app

# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'aezen'

    # 🔹 home 블루프린트 등록
    from app.home.routes import bp as home_bp
    app.register_blueprint(home_bp)

    # (필요하다면 다른 블루프린트도 등록)
    # from app.mypage.routes import bp as mypage_bp
    # app.register_blueprint(mypage_bp, url_prefix="/mypage")

    from app.account.routes import bp as account_bp
    app.register_blueprint(account_bp)

    from app.mypage.routes import bp as mypage_bp
    app.register_blueprint(mypage_bp)

    return app

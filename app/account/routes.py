# app/account/routes.py
from flask import Blueprint, render_template, request, redirect, session, flash
from config import SIDEBAR_CONFIG
from datetime import datetime
import pymysql

bp = Blueprint(
    'account',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/account/static'
)

def get_db_connection():
    return pymysql.connect(
        host='192.168.60.187',
        user='jwh',
        password='ezen',
        db='aezen',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# ------------- account 관련 라우트 영역 -------------------------

@bp.route("/login", methods=["POST"])
def login():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        id = request.form["username"]
        password = request.form["password"]

        # withdraw 조건 없이 먼저 조회
        sql = "SELECT * FROM user WHERE id=%s AND password=%s"
        cursor.execute(sql, (id, password))
        user = cursor.fetchone()

        # 아이디 또는 비밀번호 틀림
        if not user:
            return """
            <script>
                alert('아이디 또는 비밀번호가 틀렸습니다.');
                history.back();
            </script>
            """

        # 탈퇴한 회원
        if user.get("withdraw") == 1:
            return """
            <script>
                alert('탈퇴한 회원입니다.');
                history.back();
            </script>
            """

        # 정상 로그인 (성공 alert 없음)
        user.pop('password', None)
        session["user"] = user

        update_sql = "UPDATE user SET last_login_at=%s WHERE id=%s"
        cursor.execute(update_sql, (datetime.now(), user["id"]))
        conn.commit()

        return redirect("/")

    finally:
        cursor.close()
        conn.close()
    
@bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("로그아웃 되었습니다.")
    return redirect("/")

@bp.route('/join-agree')
def join_agree():
    return render_template(
    'join_agree.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/join-info')
def join_info():
    return render_template(
    'join_info.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/join-find')
def join_find():
    return render_template(
    'join_find.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)
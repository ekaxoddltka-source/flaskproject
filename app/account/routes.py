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
        host='localhost',
        user='root',
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

        #user 테이블에서 검색
        sql = "SELECT * FROM user WHERE id=%s AND password=%s"
        cursor.execute(sql, (id, password))
        user = cursor.fetchone()

        if user:
            #비밀번호는 세션에 저장하면 안됨
            if 'password' in user:
                user.pop('password')

            #유저 정보 전체를 세션에 저장
            session["user"] = user

            #로그인 시간 업데이트
            update_sql = "UPDATE user SET last_login_at=%s WHERE id=%s"
            cursor.execute(update_sql, (datetime.now(), user["id"]))
            conn.commit()

            flash("로그인 성공")
            return redirect("/")
        
        else:
            flash("로그인 실패: 아이디 또는 비밀번호가 틀렸습니다.")
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
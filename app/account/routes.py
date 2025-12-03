# app/account/routes.py
from flask import Blueprint, render_template, request, redirect, session, flash, current_app, jsonify
from config import SIDEBAR_CONFIG
from datetime import datetime
import pymysql
from .dao.user_dao import UserDao
from app.account.utils.mail import send_email
from app.account.dao.user_dao import UserDao
import random, string

bp = Blueprint(
    'account',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/account/static'
)

# ------------- account 관련 라우트 영역 -------------------------

@bp.route("/login", methods=["POST"])
def login():
    conn = current_app.get_db_connection()
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

@bp.route('/join-find')
def join_find():
    return render_template(
    'join_find.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/step2', methods=['POST'])
def process_agree():
    # 1. 필수 약관 동의 여부 확인
    terms_agreed = request.form.get('agree-terms')
    privacy_agreed = request.form.get('agree-privacy')

    # 필수 약관 동의가 누락된 경우
    if not terms_agreed or not privacy_agreed:
        flash("필수 약관에 동의해야 다음 단계로 진행할 수 있습니다.", "error")
        return redirect('/join-agree')

    # 2. 약관 동의 정보 세션에 저장 (✅ 수정됨: 빈 딕셔너리가 아니라 실제 값을 넣어야 함)
    session['join_agreement'] = {
        'agree-terms': terms_agreed,
        'agree-privacy': privacy_agreed,
        'agree-marketing': request.form.get('agree-marketing', 'off') # 선택 약관
    }

    # 3. 다음 페이지로 리다이렉트
    return redirect('/join-info')

@bp.route('/join-info')
def join_info():
    
    return render_template(
    'join_info.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/join', methods=['POST'])
def join():
    userid = request.form.get("userid")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm-password")
    name = request.form.get("name")
    nickname = request.form.get("nickname")
    email = request.form.get("email")

    # 선택된 interests / skills
    interests = request.form.getlist("interests[]")
    skills = request.form.getlist("skills[]")

    # 비밀번호 확인
    if password != confirm_password:
        flash("비밀번호가 일치하지 않습니다.", "error")
        return redirect("/join-info")

    user_dao = UserDao()
    user_data = {
        "id": userid,
        "password": password,
        "name": name,
        "nick": nickname,
        "email": email
    }

    # 유저 + user_attributes 통합 insert
    result = user_dao.insert_user(user_data, interests=interests, skills=skills)
    if not result:
        flash("회원가입 중 오류가 발생했습니다.", "error")
        return redirect("/join-info")

    flash("회원가입이 완료되었습니다!", "success")
    return redirect("/")




@bp.route("/check-duplicate", methods=["POST"])
def check_duplicate():
    field = request.form.get("field")
    value = request.form.get("value")
    if not field or not value:
        return {"status": "error", "message": "값이 없습니다."}

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        sql_map = {
            "userid": "SELECT id FROM user WHERE id=%s",
            "nickname": "SELECT nick FROM user WHERE nick=%s",
            "email": "SELECT email FROM user WHERE email=%s"
        }

        friendly_names = {
            "userid": "ID",
            "nickname": "닉네임",
            "email": "이메일"
        }

        sql = sql_map.get(field)
        if not sql:
            return {"status": "error", "message": "잘못된 필드입니다."}
        
        friendly = friendly_names.get(field, field)

        cursor.execute(sql, (value,))
        exists = cursor.fetchone()
        if exists:
            return {"status": "exists", "message": f"{friendly} 이미 사용중입니다."}
        else:
            return {"status": "ok", "message": f"{friendly} 사용 가능"}

    finally:
        cursor.close()
        conn.close()




    bp = Blueprint('account', __name__, url_prefix='/')

# -----------------------------------
# 🔹 아이디 찾기 - 인증코드 전송
# -----------------------------------
@bp.route('/send-id-code', methods=['POST'])
def send_id_code():
    name = request.form.get('name')
    email = request.form.get('email')

    user = UserDao.get_user_by_name_email(name, email)
    if not user:
        return jsonify(success=False, msg="일치하는 회원이 없습니다.")

    code = ''.join(random.choices(string.digits, k=6))

    session['find_id_code'] = code
    session['find_id_userid'] = user['id']  # user.id

    send_email(email, "아이디 찾기 인증코드", f"인증코드: {code}")

    return jsonify(success=True, msg="인증코드를 이메일로 전송했습니다.")


# -----------------------------------
# 🔹 아이디 찾기 - 최종 확인
# -----------------------------------
@bp.route('/find-id', methods=['POST'])
def find_id():
    name = request.form.get('name-id')
    email = request.form.get('email-id')
    code = request.form.get('code-id')

    if code != session.get('find_id_code'):
        return "<script>alert('인증코드가 일치하지 않습니다.'); history.back();</script>"

    userid = session.get('find_id_userid')

    return f"""
    <script>
    alert("{name}님의 ID는 '{userid}' 입니다.");
    window.location.href='/join-find';
    </script>
    """


# -----------------------------------
# 🔹 비밀번호 찾기 - 임시 비밀번호 발송 (테스트용, 해시 없이)
# -----------------------------------
@bp.route('/find-password', methods=['POST'])
def find_password():
    userid = request.form.get('userid-pw')
    name = request.form.get('name-pw')
    email = request.form.get('email-pw')

    user = UserDao.get_user_by_all(userid, name, email)
    if not user:
        return "<script>alert('입력 정보가 일치하지 않습니다.'); history.back();</script>"

    # 🔹 임시 비밀번호 생성
    temp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # 🔹 DB에 그대로 저장
    UserDao.update_password(userid, temp_pw)

    # 🔹 이메일로 임시 비밀번호 전송
    send_email(email, "임시 비밀번호 안내", f"임시 비밀번호: {temp_pw}")

    return """
    <script>
    alert("임시 비밀번호를 이메일로 전송했습니다.");
    window.location.href='/join-find';
    </script>
    """
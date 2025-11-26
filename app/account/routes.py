# app/account/routes.py
from flask import Blueprint, render_template, request, redirect, session, flash
from config import SIDEBAR_CONFIG
from datetime import datetime
import pymysql
from .dao.user_dao import UserDao
from app.database import get_db_connection

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
    # ⚠️ 만약 약관 동의 없이 이 페이지에 직접 접근했다면, 약관 페이지로 돌려보내는 로직을 추가해야 합니다.
    if 'join_agreement' not in session:
        flash("회원가입 절차를 다시 시작해주세요.", "warning")
        return redirect('/join-agree')
        
    return render_template(
    'join_info.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)



@bp.route('/join', methods=['POST'])
def join():
    # 1. 약관 동의 정보 확인
    agreement_data = session.pop('join_agreement', None)
    if not agreement_data:
        flash("약관 동의 정보가 누락되어 회원가입을 완료할 수 없습니다.", "error")
        return redirect('/join-agree')

    # 2. 폼 데이터 수집
    user_data = {
        'id': request.form['id'],
        'password': request.form['password'], # ⚠️ 실제 서비스에서는 비밀번호를 해시(Hash) 처리해야 합니다!
        'email': request.form['email'],
        'nickname': request.form.get('nickname'),
        # ... 추가적인 가입 정보
    }
    
    # 3. DAO 객체 생성 및 DB에 삽입
    user_dao = UserDao()
    
    # 💡 ID 중복 검사 (프론트에서도 하지만 서버에서도 다시 검사)
    if user_dao.check_id_duplicate(user_data['id']):
        flash("이미 존재하는 아이디입니다.", "warning")
        # 다시 회원정보 입력 페이지로 돌아가되, 기존 입력값은 유지하도록 처리할 수 있습니다.
        return redirect('/join-info') 

    # 4. 최종 사용자 정보 삽입
    # user_data에 agreement_data를 통합하여 DB에 저장해야 할 수도 있습니다 (별도 테이블 또는 컬럼 필요)
    
    if user_dao.insert_user(user_data):
        flash("회원가입이 성공적으로 완료되었습니다!", "success")
        return redirect('/login') # 로그인 페이지로 이동
    else:
        flash("회원가입 중 데이터베이스 오류가 발생했습니다.", "error")
        return redirect('/join-info')
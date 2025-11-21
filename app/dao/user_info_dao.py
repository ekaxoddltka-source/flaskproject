# app/dao/user_info_dao.py

class UserInfoDao:
    def __init__(self, db_conn_func):
        """
        db_conn_func = lambda: current_app.get_db_connection()
        """
        self.db_conn_func = db_conn_func

    # ---------------------------------------------------
    # 1) 유저 상세 정보 가져오기
    # ---------------------------------------------------
    def get_user_by_id(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT id, nick, email, profile, withdraw
            FROM user
            WHERE id = %s
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row

    # ---------------------------------------------------
    # 2) 닉네임 중복 체크
    # ---------------------------------------------------
    def check_nickname_exists(self, nickname):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT id FROM user
            WHERE nick = %s
        """

        cur.execute(sql, (nickname,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row is not None

    # ---------------------------------------------------
    # 3) 이메일 중복 체크
    # ---------------------------------------------------
    def check_email_exists(self, email):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT id FROM user
            WHERE email = %s
        """

        cur.execute(sql, (email,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row is not None

    # ---------------------------------------------------
    # 4) 비밀번호 변경
    # ---------------------------------------------------
    def update_password(self, user_id, new_password):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE user
            SET pw = %s
            WHERE id = %s
        """

        cur.execute(sql, (new_password, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # ---------------------------------------------------
    # 5) 닉네임 + 이메일 수정
    # ---------------------------------------------------
    def update_user_info(self, user_id, new_nick, new_email):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE user
            SET nick = %s, email = %s
            WHERE id = %s
        """

        cur.execute(sql, (new_nick, new_email, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # ---------------------------------------------------
    # 6) 회원 탈퇴 처리 (withdraw = 1 로 변경)
    # ---------------------------------------------------
    def withdraw_user(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE user
            SET withdraw = 1
            WHERE id = %s
        """

        cur.execute(sql, (user_id,))
        conn.commit()

        cur.close()
        conn.close()
        return True

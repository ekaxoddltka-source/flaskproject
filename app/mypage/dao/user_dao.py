# app/dao/user_dao.py
class UserDao:
    def __init__(self, db_conn_func):
        """
        db_conn_func : app.get_db_connection 같은 DB 연결 함수
        """
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) ID로 유저 정보 조회
    # -----------------------------------------------------
    def get_user_by_id(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                id,
                password,
                nick,
                email,
                icon,
                background_img,
                created_at
            FROM user
            WHERE id = %s
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row

    # -----------------------------------------------------
    # 2) 로그인 시 비밀번호 확인용
    # -----------------------------------------------------
    def check_login(self, user_id, password):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT id, password, nick
            FROM user
            WHERE id = %s
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row

  

    # -----------------------------------------------------
    # 3) 배경이미지 / 아이콘 설정 변경
    # -----------------------------------------------------
    def update_profile_item(self, user_id, icon=None, bg=None):
        conn = self.db_conn_func()
        cur = conn.cursor()

        if icon:
            sql = "UPDATE user SET profile_icon=%s WHERE id=%s"
            cur.execute(sql, (icon, user_id))

        if bg:
            sql = "UPDATE user SET background_img=%s WHERE id=%s"
            cur.execute(sql, (bg, user_id))

        conn.commit()
        cur.close()
        conn.close()
        return True

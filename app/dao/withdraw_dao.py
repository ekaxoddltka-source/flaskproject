# app/dao/withdraw_dao.py

class WithdrawDao:
    def __init__(self, db_conn_func):
        """db_conn_func = lambda: current_app.get_db_connection()"""
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 유저 존재 여부 확인
    # -----------------------------------------------------
    def verify_user(self, user_id, pw):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT id
            FROM user
            WHERE id = %s AND pw = %s AND withdraw = 0
        """
        cur.execute(sql, (user_id, pw))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row is not None

    # -----------------------------------------------------
    # 2) 회원 탈퇴 처리
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # 3) 탈퇴 여부 확인 (로그인 차단용)
    # -----------------------------------------------------
    def is_withdrawn(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT withdraw 
            FROM user
            WHERE id = %s
        """
        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row and row["withdraw"] == 1

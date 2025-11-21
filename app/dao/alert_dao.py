# app/dao/alert_dao.py

class AlertDao:
    def __init__(self, db_conn_func):
        """db_conn_func = lambda: current_app.get_db_connection()"""
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 알림 목록 불러오기
    # -----------------------------------------------------
    def get_alerts(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                noti_no,
                noti_type,
                noti_message,
                related_board_no,
                created_at,
                is_read
            FROM notification
            WHERE id = %s AND deleted = 0
            ORDER BY created_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 2) 읽지 않은 알림 개수
    # -----------------------------------------------------
    def count_unread(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT COUNT(*) AS cnt 
            FROM notification
            WHERE id = %s AND is_read = 0 AND deleted = 0
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row["cnt"]

    # -----------------------------------------------------
    # 3) 알림 읽음 처리
    # -----------------------------------------------------
    def mark_as_read(self, noti_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE notification
            SET is_read = 1
            WHERE noti_no = %s
        """

        cur.execute(sql, (noti_no,))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 4) 알림 개별 삭제
    # -----------------------------------------------------
    def delete_alert(self, noti_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE notification
            SET deleted = 1
            WHERE noti_no = %s
        """

        cur.execute(sql, (noti_no,))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 5) 알림 여러 개 삭제
    # -----------------------------------------------------
    def delete_alert_list(self, noti_list):
        if not noti_list:
            return False

        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = f"""
            UPDATE notification
            SET deleted = 1
            WHERE noti_no IN ({",".join(["%s"] * len(noti_list))})
        """

        cur.execute(sql, tuple(noti_list))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 6) 알림 생성
    # -----------------------------------------------------
    def create_alert(self, user_id, msg, noti_type, related_board_no=None):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            INSERT INTO notification 
            (id, noti_message, noti_type, related_board_no)
            VALUES (%s, %s, %s, %s)
        """

        cur.execute(sql, (user_id, msg, noti_type, related_board_no))
        conn.commit()

        noti_no = cur.lastrowid

        cur.close()
        conn.close()
        return noti_no

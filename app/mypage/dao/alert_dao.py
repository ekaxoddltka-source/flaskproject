class AlertDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # 1) 해당 유저가 받은 알림 목록
    def get_alert_list(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                alert_no,
                id AS sender_id,
                alert_id AS receiver_id,
                alert_type,
                alert_content,
                alerted_at,
                target_board_no,
                target_comment_answer_no
            FROM alert
            WHERE alert_id = %s
            ORDER BY alerted_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # 2) 개별 알림 삭제
    def delete_alert(self, alert_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            DELETE FROM alert
            WHERE alert_no = %s AND alert_id = %s
        """

        cur.execute(sql, (alert_no, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # 3) 전체 알림 삭제
    def delete_all_alerts(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            DELETE FROM alert
            WHERE alert_id = %s
        """

        cur.execute(sql, (user_id,))
        conn.commit()

        cur.close()
        conn.close()
        return True

import pymysql

class AlertDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 알림 생성 (댓글, 좋아요, 팔로우, 포인트, 채택 등 공통)
    # -----------------------------------------------------
    def create_alert(self, sender_id, receiver_id, alert_type, alert_content,
                     target_board_no=None, target_comment_answer_no=None):
        """
        sender_id : 알림을 발생시킨 사람 (alert.alert_id)
        receiver_id : 알림을 받는 사람 (alert.id)
        """
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            INSERT INTO alert (
                id,                 -- 알림 받는 사람
                alert_id,           -- 알림 발생시킨 사람
                alert_type,
                alert_content,
                alerted_at,
                target_board_no,
                target_comment_answer_no
            )
            VALUES (%s, %s, %s, %s, NOW(), %s, %s)
        """

        cur.execute(sql, (
            receiver_id,
            sender_id,
            alert_type,
            alert_content,
            target_board_no,
            target_comment_answer_no
        ))

        conn.commit()
        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 2) 해당 유저가 "받은" 알림 목록 (최신순)
    # -----------------------------------------------------
    def get_alert_list(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                alert_no,
                id AS receiver_id,          -- 알림 받는 사람
                alert_id AS sender_id,      -- 알림 보낸 사람
                alert_type,
                alert_content,
                alerted_at,
                target_board_no,
                target_comment_answer_no
            FROM alert
            WHERE id = %s                  -- 내가 받은 알림
            ORDER BY alerted_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 3) 알림 목록 페이징 조회 (인피니티 스크롤)
    # -----------------------------------------------------
    def get_alert_page(self, user_id, offset, limit):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                alert_no,
                id AS receiver_id,
                alert_id AS sender_id,
                alert_type,
                alert_content,
                alerted_at,
                target_board_no,
                target_comment_answer_no
            FROM alert
            WHERE id = %s                  -- 내가 받은 알림
            ORDER BY alerted_at DESC
            LIMIT %s OFFSET %s
        """

        cur.execute(sql, (user_id, limit, offset))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 4) 개별 알림 삭제 (내가 받은 알림 중 하나만)
    # -----------------------------------------------------
    def delete_alert(self, alert_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            DELETE FROM alert
            WHERE alert_no = %s AND id = %s
        """

        cur.execute(sql, (alert_no, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 5) 내가 받은 알림 전체 삭제
    # -----------------------------------------------------
    def delete_all_alerts(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            DELETE FROM alert
            WHERE id = %s
        """

        cur.execute(sql, (user_id,))
        conn.commit()

        cur.close()
        conn.close()
        return True

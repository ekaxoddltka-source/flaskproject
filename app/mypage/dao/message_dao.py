# app/dao/message_dao.py

class MessageDao:
    def __init__(self, db_conn_func):
        """db_conn_func = lambda: current_app.get_db_connection()"""
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 받은 메시지 목록
    # -----------------------------------------------------
    def get_received_messages(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                msg_no,
                sender_id,
                msg_content,
                msg_created_at,
                msg_read
            FROM message
            WHERE receiver_id = %s
              AND deleted_by_receiver = 0
            ORDER BY msg_created_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 2) 보낸 메시지 목록
    # -----------------------------------------------------
    def get_sent_messages(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                msg_no,
                receiver_id,
                msg_content,
                msg_created_at,
                msg_read
            FROM message
            WHERE sender_id = %s
              AND deleted_by_sender = 0
            ORDER BY msg_created_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 3) 메시지 상세 조회
    # -----------------------------------------------------
    def get_message_detail(self, msg_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT *
            FROM message
            WHERE msg_no = %s
              AND (sender_id = %s OR receiver_id = %s)
        """

        cur.execute(sql, (msg_no, user_id, user_id))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row

    # -----------------------------------------------------
    # 4) 메시지 보내기
    # -----------------------------------------------------
    def send_message(self, sender_id, receiver_id, content):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            INSERT INTO message (sender_id, receiver_id, msg_content)
            VALUES (%s, %s, %s)
        """

        cur.execute(sql, (sender_id, receiver_id, content))
        conn.commit()
        msg_no = cur.lastrowid

        cur.close()
        conn.close()
        return msg_no

    # -----------------------------------------------------
    # 5) 메시지 읽음 처리
    # -----------------------------------------------------
    def mark_as_read(self, msg_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE message
            SET msg_read = 1
            WHERE msg_no = %s
        """

        cur.execute(sql, (msg_no,))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 6) 메시지 삭제 처리 (소프트 딜리트)
    # -----------------------------------------------------
    def delete_message(self, msg_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        # 내가 보낸 메시지이면 sender delete
        sql_sender = """
            UPDATE message
            SET deleted_by_sender = 1
            WHERE msg_no = %s AND sender_id = %s
        """

        cur.execute(sql_sender, (msg_no, user_id))

        # 내가 받은 메시지이면 receiver delete
        sql_receiver = """
            UPDATE message
            SET deleted_by_receiver = 1
            WHERE msg_no = %s AND receiver_id = %s
        """

        cur.execute(sql_receiver, (msg_no, user_id))

        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 7) 읽지 않은 메세지 카운트
    # -----------------------------------------------------
    def count_unread_messages(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT COUNT(*) AS cnt
            FROM message
            WHERE receiver_id = %s
              AND msg_read = 0
              AND deleted_by_receiver = 0
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row["cnt"]

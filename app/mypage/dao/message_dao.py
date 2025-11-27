# app/mypage/dao/message_dao.py

class MessageDao:
    def __init__(self, db_conn_func):
        """db_conn_func = get_db_connection"""
        self.db_conn_func = db_conn_func

    # ============================================
    # 1) 유저가 참여한 대화방 목록 (미리보기용)
    #    - room_no
    #    - 상대 id / 닉네임
    #    - 마지막 메시지 내용/시간
    #    - 마지막 메시지 보낸 사람 (direction용)
    #    - 안 읽은 메시지 개수
    # ============================================
    def get_rooms_for_user(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        SELECT
            r.room_no,
            CASE
                WHEN r.user_id_a = %s THEN r.user_id_b
                ELSE r.user_id_a
            END AS partner_id,
            u.nick AS partner_nick,
            lm.message_content AS last_message_content,
            lm.message_sent_at AS last_message_sent_at,
            lm.sender_id AS last_sender_id,
            COALESCE(unread.cnt, 0) AS unread_count
        FROM message_room r
        JOIN user u
          ON u.id = CASE
                       WHEN r.user_id_a = %s THEN r.user_id_b
                       ELSE r.user_id_a
                    END
        LEFT JOIN (
            -- 각 room 별 마지막 메시지 1건
            SELECT m1.*
            FROM message m1
            JOIN (
                SELECT room_no, MAX(message_sent_at) AS max_time
                FROM message
                WHERE message_deleted = 0
                GROUP BY room_no
            ) last
              ON last.room_no = m1.room_no
             AND last.max_time = m1.message_sent_at
            WHERE m1.message_deleted = 0
        ) lm
          ON lm.room_no = r.room_no
        LEFT JOIN (
            -- 각 room 별 안 읽은 메시지 수
            SELECT room_no, COUNT(*) AS cnt
            FROM message
            WHERE receiver_id = %s
              AND read_at IS NULL
              AND message_deleted = 0
            GROUP BY room_no
        ) unread
          ON unread.room_no = r.room_no
        WHERE r.user_id_a = %s OR r.user_id_b = %s
        ORDER BY COALESCE(lm.message_sent_at, r.last_message_at) DESC
        """

        cur.execute(sql, (user_id, user_id, user_id, user_id, user_id))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # ============================================
    # 2) 특정 대화방(room_no)의 메시지 목록
    # ============================================
    def get_room_messages(self, room_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        SELECT
            message_no,
            room_no,
            sender_id,
            receiver_id,
            message_content,
            message_sent_at,
            read_at
        FROM message
        WHERE room_no = %s
          AND message_deleted = 0
          AND (sender_id = %s OR receiver_id = %s)
        ORDER BY message_sent_at ASC
        """
        cur.execute(sql, (room_no, user_id, user_id))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # ============================================
    # 3) 대화방 메시지들을 '읽음' 처리
    # ============================================
    def mark_room_as_read(self, room_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        UPDATE message
        SET read_at = NOW()
        WHERE room_no = %s
          AND receiver_id = %s
          AND read_at IS NULL
          AND message_deleted = 0
        """
        cur.execute(sql, (room_no, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # ============================================
    # 4) 메시지 전송
    # ============================================
    def send_message(self, room_no, sender_id, receiver_id, content):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        INSERT INTO message (room_no, sender_id, receiver_id, message_content)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(sql, (room_no, sender_id, receiver_id, content))
        conn.commit()
        message_no = cur.lastrowid

        # 대화방 마지막 메시지 시간 갱신
        sql2 = """
        UPDATE message_room
        SET last_message_at = NOW()
        WHERE room_no = %s
        """
        cur.execute(sql2, (room_no,))
        conn.commit()

        cur.close()
        conn.close()
        return message_no

    # ============================================
    # 5) (없으면) 대화방 생성 후 room_no 반환
    # ============================================
    def create_or_get_room(self, user_id, partner_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        # 기존 방 검색 (양쪽 순서 모두)
        sql_select = """
        SELECT room_no
        FROM message_room
        WHERE (user_id_a = %s AND user_id_b = %s)
           OR (user_id_a = %s AND user_id_b = %s)
        """
        cur.execute(sql_select, (user_id, partner_id, partner_id, user_id))
        row = cur.fetchone()

        if row:
            room_no = row["room_no"]
        else:
            # 없으면 새로 생성 (user_id_a = 나, user_id_b = 상대)
            sql_insert = """
            INSERT INTO message_room (user_id_a, user_id_b)
            VALUES (%s, %s)
            """
            cur.execute(sql_insert, (user_id, partner_id))
            conn.commit()
            room_no = cur.lastrowid

        cur.close()
        conn.close()
        return room_no

    # ============================================
    # 6) 대화방 삭제 (해당 유저 입장에서 - 실제로는 해당 방 전체 메시지 삭제)
    # ============================================
    def delete_room_for_user(self, room_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        UPDATE message
        SET message_deleted = 1
        WHERE room_no = %s
          AND (sender_id = %s OR receiver_id = %s)
        """
        cur.execute(sql, (room_no, user_id, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # ============================================
    # 7) 안 읽은 메시지 개수
    # ============================================
    def count_unread_messages(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        SELECT COUNT(*) AS cnt
        FROM message
        WHERE receiver_id = %s
          AND read_at IS NULL
          AND message_deleted = 0
        """
        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row["cnt"]

        # ============================================
    # 8) 특정 room_no의 상대방 정보 가져오기
    #    - 현재 로그인 유저(user_id)를 기준으로 상대방 결정
    # ============================================
    def get_room_info(self, room_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        SELECT 
            r.room_no,
            CASE
                WHEN r.user_id_a = %s THEN r.user_id_b
                ELSE r.user_id_a
            END AS partner_id,
            u.nick AS partner_nick
        FROM message_room r
        JOIN user u
            ON u.id = CASE
                        WHEN r.user_id_a = %s THEN r.user_id_b
                        ELSE r.user_id_a
                     END
        WHERE r.room_no = %s
          AND (r.user_id_a = %s OR r.user_id_b = %s)
        """

        cur.execute(sql, (user_id, user_id, room_no, user_id, user_id))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row

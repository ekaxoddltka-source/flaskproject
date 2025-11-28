class UserItemDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # 1) 유저가 특정 아이템을 보유 중인지 확인
    def has_item(self, user_id, item_no):
        conn = self.db_conn_func()
        cur = conn.cursor()
        sql = "SELECT 1 FROM user_item WHERE user_id=%s AND item_no=%s"
        cur.execute(sql, (user_id, item_no))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row is not None

    # 2) 아이템 획득
    def add_item(self, user_id, item_no):
        conn = self.db_conn_func()
        cur = conn.cursor()
        sql = "INSERT INTO user_item (user_id, item_no) VALUES (%s, %s)"
        cur.execute(sql, (user_id, item_no))
        conn.commit()
        cur.close()
        conn.close()
        return True

    # 3) 특정 타입 전체 해제
    def unequip_type(self, user_id, item_type):
        conn = self.db_conn_func()
        cur = conn.cursor()
        sql = """
        UPDATE user_item ui
        JOIN item i ON ui.item_no = i.item_no
        SET ui.is_equipped = 0
        WHERE ui.user_id = %s AND i.item_type = %s
        """
        cur.execute(sql, (user_id, item_type))
        conn.commit()
        cur.close()
        conn.close()
        return True

    # 4) 특정 아이템 장착
    def equip_item(self, user_id, item_no):
        conn = self.db_conn_func()
        cur = conn.cursor()
        sql = """
        UPDATE user_item
        SET is_equipped = 1
        WHERE user_id = %s AND item_no = %s
        """
        cur.execute(sql, (user_id, item_no))
        conn.commit()
        cur.close()
        conn.close()
        return True

    # 5) 특정 아이템 해제
    def unequip_item(self, user_id, item_no):
        conn = self.db_conn_func()
        cur = conn.cursor()
        sql = """
        UPDATE user_item
        SET is_equipped = 0
        WHERE user_id = %s AND item_no = %s
        """
        cur.execute(sql, (user_id, item_no))
        conn.commit()
        cur.close()
        conn.close()
        return True

    # 6) user 테이블의 프로필 정보 업데이트
    def update_user_profile(self, user_id, item_type, item_img):
        conn = self.db_conn_func()
        cur = conn.cursor()

        if item_type == "icon":
            sql = "UPDATE user SET icon = %s WHERE id = %s"
        elif item_type == "background":
            sql = "UPDATE user SET background_img = %s WHERE id = %s"
        elif item_type == "insignia":
            sql = "UPDATE user SET insignia = %s WHERE id = %s"
        else:
            cur.close()
            conn.close()
            return False

        cur.execute(sql, (item_img, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True

    # 7) 유저가 가진 아이템 목록
    def get_user_items(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()
        sql = """
        SELECT 
            ui.item_no,
            ui.is_equipped,
            i.item_name,
            i.item_type,
            i.item_price,
            i.item_img
        FROM user_item ui
        JOIN item i ON ui.item_no = i.item_no
        WHERE ui.user_id = %s
        ORDER BY ui.acquired_at DESC
        """
        cur.execute(sql, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    
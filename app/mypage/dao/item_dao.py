class ItemDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # 전체 아이템 목록
    def get_all_items(self):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        SELECT 
            item_no, item_name, item_type, item_price, item_img
        FROM item
        ORDER BY item_no ASC
        """
        cur.execute(sql)
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # 단일 아이템 조회 (장착 API가 사용)
    def get_item(self, item_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
        SELECT 
            item_no, item_name, item_type, item_price, item_img
        FROM item
        WHERE item_no = %s
        """
        cur.execute(sql, (item_no,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row


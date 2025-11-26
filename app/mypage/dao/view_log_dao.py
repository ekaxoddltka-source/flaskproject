import pymysql

class ViewLogDao:
    def __init__(self, get_conn):
        self.get_conn = get_conn

    def insert_view_log(self, user_id, board_no):
        conn = self.get_conn()
        cur = conn.cursor()
        sql = "INSERT INTO board_view_log (user_id, board_no) VALUES (%s, %s)"
        cur.execute(sql, (user_id, board_no))
        conn.commit()
        cur.close()
        conn.close()
        return True

    def get_viewed_board_nos(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT board_no FROM board_view_log WHERE user_id=%s ORDER BY viewed_at DESC"
        cur.execute(sql, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r["board_no"] for r in rows]

    def get_viewed_posts(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT b.board_no, b.board_title, b.board_content,
                   b.board_category, b.id AS writer_id, b.board_created_at
            FROM board_view_log v
            JOIN board b ON v.board_no = b.board_no
            WHERE v.user_id = %s
              AND b.board_deleted = 0
            ORDER BY v.viewed_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    def get_viewed_tags(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT t.tag_name
            FROM board_view_log v
            JOIN tag_board tb ON v.board_no = tb.board_no
            JOIN tag t ON tb.tag_no = t.tag_no
            WHERE v.user_id = %s
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return [r["tag_name"] for r in rows]

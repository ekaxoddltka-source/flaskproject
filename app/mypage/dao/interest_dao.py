import pymysql

class InterestDao:
    def __init__(self, get_conn):
        self.get_conn = get_conn

    # ------------------------------------------------------------
    # 1. 내가 작성한 게시글
    # ------------------------------------------------------------
    def get_written_posts(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT board_no, board_title, board_content, board_category
            FROM board
            WHERE id = %s
              AND board_deleted = 0
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        # rows 는 이미 dict 리스트
        return list(rows)

    # ------------------------------------------------------------
    # 2. 내가 작성한 댓글/답변
    # ------------------------------------------------------------
    def get_written_comments(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT comment_answer_content
            FROM comment_answer
            WHERE id = %s
              AND comment_answer_type IN (1, 2)
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return list(rows)

    # ------------------------------------------------------------
    # 3. 내가 작성한 게시글 태그
    # ------------------------------------------------------------
    def get_written_tags(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT t.tag_name
            FROM board b
            JOIN tag_board tb ON b.board_no = tb.board_no
            JOIN tag t ON tb.tag_no = t.tag_no
            WHERE b.id = %s
              AND b.board_deleted = 0
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return [r["tag_name"] for r in rows]

    # ------------------------------------------------------------
    # 4. 내가 조회한 게시글
    # ------------------------------------------------------------
    def get_viewed_posts(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT b.board_no, b.board_title, b.board_content, b.board_category
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

        return list(rows)

    # ------------------------------------------------------------
    # 5. 내가 조회한 태그
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # 6. 내가 조회한 댓글/답변
    # ------------------------------------------------------------
    def get_viewed_comments(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT ca.comment_answer_content
            FROM board_view_log v
            JOIN comment_answer ca ON v.board_no = ca.board_no
            WHERE v.user_id = %s
              AND ca.comment_answer_type IN (1, 2)
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return list(rows)

    # ------------------------------------------------------------
    # 7. 텍스트 전체
    # ------------------------------------------------------------
    def get_all_text_sources(self, user_id):
        return {
            "written_posts": self.get_written_posts(user_id),
            "viewed_posts": self.get_viewed_posts(user_id),
            "written_comments": self.get_written_comments(user_id),
            "viewed_comments": self.get_viewed_comments(user_id)
        }

    # ------------------------------------------------------------
    # 8. 태그 전체
    # ------------------------------------------------------------
    def get_all_tags(self, user_id):
        return {
            "written_tags": self.get_written_tags(user_id),
            "viewed_tags": self.get_viewed_tags(user_id)
        }
    
    # ------------------------------------------------------------
    # 9. 추천용 후보 게시글 (내가 쓴 글 제외, 삭제 안 된 글)
    # ------------------------------------------------------------
    def get_recommend_candidates(self, user_id, limit=100):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                b.board_no,
                b.board_title,
                b.board_content,
                b.board_category
            FROM board b
            WHERE b.board_deleted = 0
              AND b.id <> %s      -- 내가 쓴 글은 제외
            ORDER BY b.board_created_at DESC
            LIMIT %s
        """
        cur.execute(sql, (user_id, limit))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return list(rows)

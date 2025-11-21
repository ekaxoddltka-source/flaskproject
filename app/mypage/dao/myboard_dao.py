# app/dao/myboard_dao.py

class MyBoardDao:
    def __init__(self, db_conn_func):
        """
        db_conn_func: app.get_db_connection
        """
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 특정 유저가 작성한 게시글 목록 가져오기
    # -----------------------------------------------------
    def get_user_posts(self, user_id, limit=20, offset=0):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                b.board_no,
                b.board_title,
                b.board_content,
                b.board_category,
                b.hit,
                b.board_like,
                b.board_dislike,
                b.board_created_at,
                b.board_updated_at
            FROM board b
            WHERE b.id = %s AND b.board_deleted = 0
            ORDER BY b.board_no DESC
            LIMIT %s OFFSET %s
        """

        cur.execute(sql, (user_id, limit, offset))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 2) 특정 게시글의 상세 정보 불러오기
    # -----------------------------------------------------
    def get_post_detail(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                b.*, u.nick AS writer_nick, u.id AS writer_id
            FROM board b
            LEFT JOIN user u ON b.id = u.id
            WHERE b.board_no = %s AND b.board_deleted = 0
        """

        cur.execute(sql, (board_no,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row

    # -----------------------------------------------------
    # 3) 게시글의 첨부 파일 목록 가져오기
    # -----------------------------------------------------
    def get_post_files(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                file_no,
                logical_file_name,
                physical_file_name,
                file_ext,
                file_size
            FROM file
            WHERE board_no = %s
        """

        cur.execute(sql, (board_no,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 4) 게시글의 태그 목록 가져오기
    # -----------------------------------------------------
    def get_post_tags(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT t.tag_name
            FROM tag_board tb
            JOIN tag t ON t.tag_no = tb.tag_no
            WHERE tb.board_no = %s
        """

        cur.execute(sql, (board_no,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 5) 게시글의 댓글 / 답변 가져오기
    # -----------------------------------------------------
    def get_post_comments(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 
                c.comment_answer_no,
                c.comment_answer_content,
                c.comment_answer_type,
                c.comment_like_count,
                c.comment_dislike_count,
                c.comment_answer_at,
                u.nick AS commenter_nick,
                u.id AS commenter_id
            FROM comment_answer c
            LEFT JOIN user u ON c.id = u.id
            WHERE c.board_no = %s
            ORDER BY c.comment_answer_no ASC
        """

        cur.execute(sql, (board_no,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 6) 게시글 삭제 (soft delete)
    # -----------------------------------------------------
    def delete_post(self, board_no, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            UPDATE board
            SET board_deleted = 1
            WHERE board_no = %s AND id = %s
        """

        cur.execute(sql, (board_no, user_id))
        conn.commit()

        cur.close()
        conn.close()
        return True

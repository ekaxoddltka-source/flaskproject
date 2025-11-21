# app/dao/mypage_posts_dao.py
import pymysql

class MyPagePostsDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 내 게시글 목록 (좋아요/싫어요 포함)
    # -----------------------------------------------------
    def get_my_posts(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                board_no,
                board_title,
                board_content,
                board_category,
                hit,
                board_like,
                board_dislike,
                board_created_at,
                board_updated_at,
                id AS writer_id
            FROM board
            WHERE id = %s AND board_deleted = 0
            ORDER BY board_no DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 2) 게시글 상세 조회
    # -----------------------------------------------------
    def get_post_detail(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                b.*, 
                u.nick AS writer_nick,
                u.id AS writer_id
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
    # 3) 파일 목록
    # -----------------------------------------------------
    def get_files_by_board(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                file_no,
                logical_file_name,
                physical_file_name,
                file_size,
                file_ext
            FROM file
            WHERE board_no = %s
        """

        cur.execute(sql, (board_no,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 4) 태그 목록
    # -----------------------------------------------------
    def get_tags_by_board(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT t.tag_name
            FROM tag t
            JOIN tag_board tb ON t.tag_no = tb.tag_no
            WHERE tb.board_no = %s
        """

        cur.execute(sql, (board_no,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 5) 댓글 목록
    # -----------------------------------------------------
    def get_comments_by_board(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

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

    # -----------------------------------------------------
    # 7) 전체 게시글 정보 조립 (완성형)
    # -----------------------------------------------------
    def get_my_posts_full(self, user_id):
        posts = self.get_my_posts(user_id)

        for p in posts:
            board_no = p["board_no"]
            p["files"] = self.get_files_by_board(board_no)
            p["tags"] = self.get_tags_by_board(board_no)
            p["comments"] = self.get_comments_by_board(board_no)

            # 좋아요 / 싫어요는 이미 p 안의 컬럼으로 존재
            p["like_count"] = p["board_like"]
            p["dislike_count"] = p["board_dislike"]

        return posts

# app/dao/mypage_posts_dao.py
import pymysql

class MyPagePostsDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    def get_my_posts_light(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                board_no,
                board_title,
                board_category,
                hit,
                board_like,
                board_dislike,
                board_created_at
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
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT
                b.board_no,
                b.board_title,
                b.board_category,
                b.hit,
                b.board_content,
                b.board_like,
                b.board_dislike,
                b.board_created_at,
                b.id AS writer_id,
                u.nick AS writer_nick,

                f.file_no,
                f.logical_file_name,
                f.physical_file_name,
                f.file_size,
                f.file_ext,

                t.tag_no,
                t.tag_name,

                c.comment_answer_no,
                c.comment_answer_content,
                c.comment_answer_type,
                c.comment_like_count,
                c.comment_dislike_count,
                c.comment_answer_at,
                cu.nick AS commenter_nick,
                cu.id AS commenter_id

            FROM board b
            LEFT JOIN user u ON b.id = u.id

            LEFT JOIN file f
                ON f.board_no = b.board_no

            LEFT JOIN tag_board tb
                ON tb.board_no = b.board_no
            LEFT JOIN tag t
                ON t.tag_no = tb.tag_no

            LEFT JOIN comment_answer c
                ON c.board_no = b.board_no
            LEFT JOIN user cu
                ON cu.id = c.id

            WHERE b.id = %s AND b.board_deleted = 0
            ORDER BY b.board_no DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        posts_map = {}

        for row in rows:
            bn = row["board_no"]

            if bn not in posts_map:
                posts_map[bn] = {
                    "board_no": bn,
                    "board_title": row["board_title"],
                    "board_category": row["board_category"],
                    "board_content": row["board_content"],
                    "hit": row["hit"],
                    "board_like": row["board_like"],
                    "board_dislike": row["board_dislike"],
                    "board_created_at": row["board_created_at"],
                    "writer_id": row["writer_id"],
                    "writer_nick": row["writer_nick"],
                    "files": [],
                    "tags": [],
                    "comments": [],
                }

            p = posts_map[bn]

            # 파일
            if row["file_no"] is not None:
                p["files"].append({
                    "file_no": row["file_no"],
                    "logical_file_name": row["logical_file_name"],
                    "physical_file_name": row["physical_file_name"],
                    "file_size": row["file_size"],
                    "file_ext": row["file_ext"],
                })

            # 태그
            if row["tag_no"] is not None:
                p["tags"].append({
                    "tag_no": row["tag_no"],
                    "tag_name": row["tag_name"],
                })

            # 댓글
            if row["comment_answer_no"] is not None:
                p["comments"].append({
                    "comment_answer_no": row["comment_answer_no"],
                    "comment_answer_content": row["comment_answer_content"],
                    "comment_answer_type": row["comment_answer_type"],
                    "comment_like_count": row["comment_like_count"],
                    "comment_dislike_count": row["comment_dislike_count"],
                    "comment_answer_at": row["comment_answer_at"],
                    "commenter_nick": row["commenter_nick"],
                    "commenter_id": row["commenter_id"],
                })

        return list(posts_map.values())
    def add_like(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            UPDATE board
            SET board_like = board_like + 1
            WHERE board_no = %s
        """
        cur.execute(sql, (board_no,))
        
        # 업데이트 후 최신값 조회
        cur.execute("""
            SELECT board_like, board_dislike
            FROM board
            WHERE board_no = %s
        """, (board_no,))
        
        row = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        return row


    def add_dislike(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            UPDATE board
            SET board_dislike = board_dislike + 1
            WHERE board_no = %s
        """
        cur.execute(sql, (board_no,))

        # 업데이트 후 최신값 조회
        cur.execute("""
            SELECT board_like, board_dislike
            FROM board
            WHERE board_no = %s
        """, (board_no,))
        
        row = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        return row
        
    def update_like(self, board_no, amount):
        conn = self.db_conn_func()
        cur = conn.cursor()
        cur.execute(
            "UPDATE board SET board_like = board_like + %s WHERE board_no = %s",
            (amount, board_no)
        )
        conn.commit()
        cur.close()
        conn.close()

    def update_dislike(self, board_no, amount):
        conn = self.db_conn_func()
        cur = conn.cursor()
        cur.execute(
            "UPDATE board SET board_dislike = board_dislike + %s WHERE board_no = %s",
            (amount, board_no)
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_like_dislike(self, board_no):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(
            "SELECT board_like, board_dislike FROM board WHERE board_no = %s",
            (board_no,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

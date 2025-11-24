# app/dao/follow_dao.py

import pymysql

class FollowDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 내가 팔로우한 사람 목록 (팔로잉)
    # -----------------------------------------------------
    def get_following_list(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                f.followed_id AS user_id,
                u.nick AS nickname,
                f.follow_started_at AS followed_at
            FROM follow f
            JOIN user u ON f.followed_id = u.id
            WHERE f.following_id = %s
            ORDER BY f.follow_started_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows


    # -----------------------------------------------------
    # 2) 나를 팔로우한 사람 목록 (팔로워)
    # -----------------------------------------------------
    def get_follower_list(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                f.following_id AS user_id,
                u.nick AS nickname,
                f.follow_started_at AS followed_at
            FROM follow f
            JOIN user u ON f.following_id = u.id
            WHERE f.followed_id = %s
            ORDER BY f.follow_started_at DESC
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows


    # -----------------------------------------------------
    # 3) 팔로우 하기
    # -----------------------------------------------------
    def follow(self, user_id, target_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        check_sql = """
            SELECT 1 FROM follow
            WHERE following_id=%s AND followed_id=%s
        """
        cur.execute(check_sql, (user_id, target_id))
        exists = cur.fetchone()

        if exists:
            cur.close()
            conn.close()
            return False

        sql = """
            INSERT INTO follow (following_id, followed_id)
            VALUES (%s, %s)
        """
        cur.execute(sql, (user_id, target_id))
        conn.commit()

        cur.close()
        conn.close()
        return True


    # -----------------------------------------------------
    # 4) 언팔로우
    # -----------------------------------------------------
    def unfollow(self, user_id, target_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            DELETE FROM follow
            WHERE following_id=%s AND followed_id=%s
        """
        cur.execute(sql, (user_id, target_id))
        conn.commit()

        cur.close()
        conn.close()
        return True


    # -----------------------------------------------------
    # 5) 내가 특정 유저를 팔로우 중인지
    # -----------------------------------------------------
    def is_following(self, user_id, target_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT 1 FROM follow
            WHERE following_id=%s AND followed_id=%s
        """
        cur.execute(sql, (user_id, target_id))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row is not None


    # -----------------------------------------------------
    # 6) 팔로잉 count
    # -----------------------------------------------------
    def count_following(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT COUNT(*) AS cnt FROM follow WHERE following_id=%s"
        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row["cnt"]


    # -----------------------------------------------------
    # 7) 팔로워 count
    # -----------------------------------------------------
    def count_follower(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT COUNT(*) AS cnt FROM follow WHERE followed_id=%s"
        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        return row["cnt"]


    # -----------------------------------------------------
    # 8) 팔로우한 사람들의 user_id 목록만 가져오기
    # -----------------------------------------------------
    def get_following_ids(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT followed_id FROM follow WHERE following_id=%s"
        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return [row["followed_id"] for row in rows]


    # -----------------------------------------------------
    # 9) 팔로우한 사람들의 최신 게시글 가져오기
    # -----------------------------------------------------
    def get_following_posts(self, user_id, limit=20):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
            SELECT 
                b.board_no,
                b.board_title,
                b.board_content,
                b.board_created_at,
                b.id AS writer_id,
                u.nick AS writer_nick
            FROM board b
            JOIN follow f ON b.id = f.followed_id
            JOIN user u ON b.id = u.id
            WHERE f.following_id = %s AND b.board_deleted = 0
            ORDER BY b.board_created_at DESC
            LIMIT %s
        """

        cur.execute(sql, (user_id, limit))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

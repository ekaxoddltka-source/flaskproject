# app/dao/point_dao.py
import pymysql
class PointDao:
    def __init__(self, db_conn_func):
        self.db_conn_func = db_conn_func

    # ======================================================
    # 공통: user.user_current_point 업데이트 함수
    # ======================================================
    def _update_user_current_point(self, cur, user_id, diff_amount):
        sql = """
            UPDATE user
            SET user_current_point = user_current_point + %s
            WHERE id = %s
        """
        cur.execute(sql, (diff_amount, user_id))

    # ======================================================
    # 1) 포인트 내역 조회
    # ======================================================
    def get_point_history(self, user_id, order="latest"):
        conn = self.db_conn_func()
        cur = conn.cursor()

        order_sql = {
            "latest": "ORDER BY point_created_at DESC",
            "oldest": "ORDER BY point_created_at ASC",
            "high": "ORDER BY point_amount DESC",
            "low": "ORDER BY point_amount ASC"
        }

        sql = f"""
            SELECT 
                point_no,
                id,
                point_amount,
                point_type,
                point_reason,
                point_created_at,
                board_no
            FROM point
            WHERE id = %s
            {order_sql.get(order, order_sql['latest'])}
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # ======================================================
    # 2) 포인트 적립
    # ======================================================
    def add_point(self, user_id, amount, reason, board_no=None):
        conn = self.db_conn_func()
        cur = conn.cursor()

        # 1) 내역 추가
        sql = """
            INSERT INTO point (id, point_amount, point_type, point_reason, board_no)
            VALUES (%s, %s, 2, %s, %s)
        """
        cur.execute(sql, (user_id, amount, reason, board_no))

        # 2) 유저 현재 포인트 업데이트
        self._update_user_current_point(cur, user_id, amount)

        conn.commit()
        cur.close()
        conn.close()
        return True

    # ======================================================
    # 3) 포인트 사용 (차감)
    # ======================================================
    def use_point(self, user_id, amount, reason, board_no=None):
        conn = self.db_conn_func()
        cur = conn.cursor()

        amount = abs(amount)   # 안전하게 절대값

        # 1) 내역 추가 (음수로 저장)
        sql = """
            INSERT INTO point (id, point_amount, point_type, point_reason, board_no)
            VALUES (%s, %s, 1, %s, %s)
        """
        cur.execute(sql, (user_id, -amount, reason, board_no))

        # 2) 현재 포인트 차감
        self._update_user_current_point(cur, user_id, -amount)

        conn.commit()
        cur.close()
        conn.close()
        return True

    # ======================================================
    # 4) DB의 누적 포인트 다시 재계산(필요하면)
    # ======================================================
    def recalc_total_point(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT SUM(point_amount) AS total
            FROM point
            WHERE id = %s
        """
        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        total = row["total"] if row["total"] else 0

        # user 테이블 업데이트
        sql2 = """
            UPDATE user
            SET user_current_point = %s
            WHERE id = %s
        """
        cur.execute(sql2, (total, user_id))

        conn.commit()
        cur.close()
        conn.close()
        return total
    # ======================================================
    # 5) 현재 유저 포인트 조회 (user.user_current_point 사용)
    # ======================================================
    def get_total_point(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT user_current_point
            FROM user
            WHERE id = %s
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        return row["user_current_point"] if row else 0
    def get_point_history_page(self, user_id, order="latest", offset=0, limit=20):
        conn = self.db_conn_func()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        order_sql = {
            "latest": "ORDER BY point_created_at DESC",
            "oldest": "ORDER BY point_created_at ASC",
            "high": "ORDER BY point_amount DESC",
            "low": "ORDER BY point_amount ASC"
        }

        sql = f"""
            SELECT 
                point_no,
                id,
                point_amount,
                point_type,
                point_reason,
                point_created_at,
                board_no
            FROM point
            WHERE id = %s
            {order_sql.get(order, order_sql["latest"])}
            LIMIT %s OFFSET %s
        """

        cur.execute(sql, (user_id, limit, offset))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

# app/dao/point_dao.py

class PointDao:
    def __init__(self, db_conn_func):
        """db_conn_func = lambda: current_app.get_db_connection()"""
        self.db_conn_func = db_conn_func

    # -----------------------------------------------------
    # 1) 포인트 전체 내역 조회
    # -----------------------------------------------------
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
                point_desc,
                total_point,
                point_created_at
            FROM point_history
            WHERE id = %s
            {order_sql.get(order, order_sql['latest'])}
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()
        return rows

    # -----------------------------------------------------
    # 2) 포인트 추가 (적립)
    # -----------------------------------------------------
    def add_point(self, user_id, amount, point_type, desc):
        conn = self.db_conn_func()
        cur = conn.cursor()

        # 현재 누적 포인트 조회
        total_sql = """
            SELECT total_point 
            FROM point_history
            WHERE id = %s
            ORDER BY point_no DESC LIMIT 1
        """

        cur.execute(total_sql, (user_id,))
        last = cur.fetchone()

        last_total = last["total_point"] if last else 0
        new_total = last_total + amount

        # 새로운 내역 저장
        sql = """
            INSERT INTO point_history 
            (id, point_amount, point_type, point_desc, total_point)
            VALUES (%s, %s, %s, %s, %s)
        """

        cur.execute(sql, (user_id, amount, point_type, desc, new_total))
        conn.commit()

        cur.close()
        conn.close()
        return True

    # -----------------------------------------------------
    # 3) 포인트 사용 (차감)
    # -----------------------------------------------------
    def use_point(self, user_id, amount, desc):
        return self.add_point(user_id, -abs(amount), "사용", desc)

    # -----------------------------------------------------
    # 4) 누적 포인트 조회
    # -----------------------------------------------------
    def get_total_point(self, user_id):
        conn = self.db_conn_func()
        cur = conn.cursor()

        sql = """
            SELECT total_point
            FROM point_history
            WHERE id = %s
            ORDER BY point_no DESC LIMIT 1
        """

        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        return row["total_point"] if row else 0


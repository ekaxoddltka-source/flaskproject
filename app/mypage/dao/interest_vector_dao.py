import json
import numpy as np
import pymysql


class InterestVectorDao:
    def __init__(self, get_conn):
        """
        get_conn: callable -> DB connection
        """
        self.get_conn = get_conn

    # ------------------------------
    # 벡터 + 키워드 저장
    # ------------------------------
    def save_vector(self, user_id, vector, top_keywords=None):
        conn = self.get_conn()
        cur = conn.cursor()

        vector_json = json.dumps(
            np.asarray(vector, dtype=float).tolist()
        )

        sql = """
            INSERT INTO user_interest_vector (user_id, vector_json, top_keywords)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                vector_json = VALUES(vector_json),
                top_keywords = VALUES(top_keywords)
        """
        cur.execute(sql, (user_id, vector_json, top_keywords))
        conn.commit()

        cur.close()
        conn.close()

    # ------------------------------
    # 벡터 불러오기
    # ------------------------------
    def load_vector(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute(
            "SELECT vector_json FROM user_interest_vector WHERE user_id=%s",
            (user_id,)
        )
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row or not row.get("vector_json"):
            return None

        return np.array(json.loads(row["vector_json"]), dtype=float)

    # ------------------------------
    # 저장된 키워드 조회
    # ------------------------------
    def load_top_keywords(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute(
            "SELECT top_keywords FROM user_interest_vector WHERE user_id=%s",
            (user_id,)
        )
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row or not row.get("top_keywords"):
            return []

        return [kw.strip() for kw in row["top_keywords"].split(",")]

    # ------------------------------
    # 삭제
    # ------------------------------
    def delete_vector(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM user_interest_vector WHERE user_id=%s",
            (user_id,)
        )
        conn.commit()

        cur.close()
        conn.close()

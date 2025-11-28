import json
import numpy as np
import pymysql

class InterestVectorDao:
    def __init__(self, get_conn):
        self.get_conn = get_conn

    # 벡터 저장
    def save_vector(self, user_id, vector):
        conn = self.get_conn()
        cur = conn.cursor()

        sql = """
            INSERT INTO user_interest_vector (user_id, vector_json)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE vector_json = VALUES(vector_json)
        """

        vector_json = json.dumps(vector.tolist())
        cur.execute(sql, (user_id, vector_json))
        conn.commit()

        cur.close()
        conn.close()

    # 벡터 불러오기
    def load_vector(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT vector_json FROM user_interest_vector WHERE user_id = %s"
        cur.execute(sql, (user_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return None
        
        return np.array(json.loads(row["vector_json"]))

import pymysql

class InterestKeywordDao:
    def __init__(self, get_conn):
        self.get_conn = get_conn

    # ------------------------------------------------------------
    # 키워드 점수 증가/감소
    # ------------------------------------------------------------
    def add_score(self, user_id, keyword, delta):
        conn = self.get_conn()
        cur = conn.cursor()

        sql = """
        INSERT INTO user_interest_keyword (user_id, keyword, score, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            score = score + VALUES(score),
            updated_at = NOW()
        """

        cur.execute(sql, (user_id, keyword, delta))
        conn.commit()

        cur.close()
        conn.close()

    # ------------------------------------------------------------
    # 특정 사용자의 키워드 점수 조회
    # { "python": 4.0, "react": -2.0, ... }
    # ------------------------------------------------------------
    def get_scores_map(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        SELECT keyword, score
        FROM user_interest_keyword
        WHERE user_id = %s
        """

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return {r["keyword"]: r["score"] for r in rows}

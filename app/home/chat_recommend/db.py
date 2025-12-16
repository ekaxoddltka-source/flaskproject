# app/home/chat_recommend/db.py
import pymysql
from datetime import datetime, timedelta

def get_top_posts_last_3_days(app, limit=10):
    """
    최근 14일간 게시글 중 board_category 2,3에 해당하며
    조회수(hit) + 추천수(board_like)가 높은 TOP 10을 가져오는 함수.
    """
    three_days_ago = datetime.now() - timedelta(days=14)

    query = """
        SELECT 
            board_no,
            id,
            board_title,
            board_content,
            board_category,
            hit,
            board_like,
            board_created_at
        FROM board
        WHERE board_deleted = 0
          AND board_created_at >= %s
          AND board_category IN (2, 3)
        ORDER BY (hit + board_like) DESC
        LIMIT %s
    """

    conn = app.get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(query, (three_days_ago, limit))
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()
from flask import session, current_app
from flask_socketio import emit
from .. import socketio
import pymysql
from datetime import datetime

user_count = 0

@socketio.on('connect')
def handle_connect(auth=None):
    global user_count
    user = session.get('user')

    conn = current_app.get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, chat_content, chat_created_at
                FROM chat
                ORDER BY chat_no DESC
                LIMIT 30
            """)
            recent_msgs = cursor.fetchall()
    finally:
        conn.close()

    safe_msgs = []
    for msg in recent_msgs:
        safe_msgs.append({
            "id": msg["id"],
            "chat_content": msg["chat_content"],
            "chat_created_at": (
                msg["chat_created_at"].strftime('%H:%M')
                if isinstance(msg["chat_created_at"], datetime)
                else str(msg["chat_created_at"])
            )
        })
    safe_msgs.reverse()

    # 로그인 여부를 클라이언트로 함께 전달
    emit('load_recent_messages', {
        'messages': safe_msgs,
        'canChat': bool(user)
    })

    if user:
        global user_count
        user_count += 1
        emit('update_user_count', user_count, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    user = session.get('user')
    if not user:
        # 로그인 안 됐으면 무시
        return

    message = data.get('message')
    if not message:
        return

    user_id = user['id']
    now = datetime.now()

    conn = current_app.get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat (id, chat_content, chat_created_at) VALUES (%s, %s, %s)",
                (user_id, message, now)
            )
            conn.commit()
    finally:
        conn.close()

    emit('receive_message', {
        'id': user_id,
        'chat_content': message,
        'chat_created_at': now.strftime('%H:%M')
    }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect(*args, **kwargs):
    user = session.get('user')
    if not user:
        return

    global user_count
    user_count -= 1
    emit('update_user_count', user_count, broadcast=True)

from app.home.chat_recommend.recommend import build_chat_topic

TOP_N = 3
all_keywords = []
current_idx = 0

@socketio.on("request_topic")
def handle_request_topic():
    global all_keywords, current_idx  # ← 전역 변수임을 명시

    topic_text, full_keywords = build_chat_topic(current_app)
    
    if all_keywords != full_keywords:
        all_keywords = full_keywords
        current_idx = 0

    if not all_keywords:
        topics_to_emit = []
    else:
        topics_to_emit = [
            all_keywords[(current_idx + i) % len(all_keywords)]
            for i in range(TOP_N)
        ]

    socketio.emit(
        "recommend_topic",
        {"topics": topics_to_emit},
        namespace='/'
    )

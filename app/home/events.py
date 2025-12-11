from flask import session, current_app
from flask_socketio import emit
from .. import socketio
import pymysql
from datetime import datetime
from app.filters.slang_filter import mask_slang

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

    # 화면에는 마스킹 후 전송
    safe_msgs = []
    for msg in recent_msgs:
        safe_msgs.append({
            "id": msg["id"],
            "chat_content": mask_slang(msg["chat_content"]),
            "chat_created_at": (
                msg["chat_created_at"].strftime('%H:%M')
                if isinstance(msg["chat_created_at"], datetime)
                else str(msg["chat_created_at"])
            )
        })

    safe_msgs.reverse()

    emit('load_recent_messages', {
        'messages': safe_msgs,
        'canChat': bool(user)
    })

    if user:
        user_count += 1
        emit('update_user_count', user_count, broadcast=True)



@socketio.on('send_message')
def handle_message(data):
    user = session.get('user')
    if not user:
        return

    message = data.get('message')
    if not message:
        return

    user_id = user['id']
    now = datetime.now()

    # DB에는 원본 저장
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

    # 사용자 화면에는 마스킹된 내용만 브로드캐스트
    safe_text = mask_slang(message)

    emit("receive_message", {
        "id": user_id,
        "chat_content": safe_text,
        "chat_created_at": now.strftime("%H:%M")
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
    global all_keywords, current_idx

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

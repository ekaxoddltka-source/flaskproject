from flask import session, current_app
from flask_socketio import emit
from .. import socketio
import pymysql
from datetime import datetime

user_count = 0

@socketio.on('connect')
def handle_connect(*args, **kwargs):  # *args, **kwargs로 모든 인자 수용
    global user_count
    user = session.get('user')
    if not user:
        return False

    user_count += 1
    emit('update_user_count', user_count, broadcast=True)

    # 직전 5개 메시지 DB에서 불러오기
    conn = current_app.get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
            SELECT id, chat_content, chat_created_at
            FROM chat
            ORDER BY chat_no DESC
            LIMIT 5
            """
            cursor.execute(sql)
            recent_msgs = cursor.fetchall()
    finally:
        conn.close()

    recent_msgs.reverse()
    emit('load_recent_messages', recent_msgs)

@socketio.on('disconnect')
def handle_disconnect(*args, **kwargs):
    global user_count
    user = session.get('user')
    if not user:
        return

    user_count -= 1
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

    conn = current_app.get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO chat (id, chat_content, chat_created_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, message, now))
            conn.commit()
    finally:
        conn.close()

    emit('receive_message', {
        'id': user_id,
        'chat_content': message,
        'chat_created_at': now.strftime('%Y-%m-%d %H:%M:%S')
    }, broadcast=True)

from flask_socketio import join_room, emit
from flask import session
from app import socketio   # 정상 import (맨 위에서 1번만)

# 유저 접속 → 개인 방에 join
@socketio.on("join_dm")
def join_dm():
    user_id = session.get("user", {}).get("id")
    if not user_id:
        return
    join_room(str(user_id))
    print(f"[DM] User joined room {user_id}")

# 1:1 메시지 서버 → 특정 유저에게 전달
def send_dm_message(receiver_id, payload):
    socketio.emit("dm_receive", payload, room=str(receiver_id))

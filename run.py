# run.py
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(
        app, 
        host='0.0.0.0',  # 모든 인터페이스에서 접속 허용
        port=5000,
        debug=True,
        use_reloader=False  # ⚡ 반드시 추가! reloader로 인한 WebSocket 문제 방지
    )
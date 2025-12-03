# app/home/chat_recommend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
scheduler = BackgroundScheduler()

all_keywords = []
current_idx = 0
TOP_N = 3  # 한 번에 보여줄 키워드 수

def _run_recommend_task(socketio, app):
    global all_keywords, current_idx
    with app.app_context():
        try:
            posts = current_app.extensions['chat_recommend']['db'].get_top_posts_last_3_days(app, limit=10)
            if not posts:
                return

            keywords_module = current_app.extensions['chat_recommend']['keywords']
            extracted = keywords_module.extract_keywords_from_posts(posts, top_n=5)

            recommend_module = current_app.extensions['chat_recommend']['recommend']
            full_keywords = recommend_module.generate_topics(extracted)

            # 처음 실행이거나 키워드가 바뀌었으면 초기화
            if all_keywords != full_keywords:
                all_keywords = full_keywords
                current_idx = 0

            if len(all_keywords) == 0:
                topics_to_emit = []
            else:
                topics_to_emit = []
                for i in range(TOP_N):
                    topics_to_emit.append(all_keywords[(current_idx + i) % len(all_keywords)])
                current_idx = (current_idx + TOP_N) % len(all_keywords)

            socketio.emit(
                "recommend_topic",
                {"timestamp": datetime.now().isoformat(), "topics": topics_to_emit},
                namespace='/'
            )

            #logger.info(f"[Scheduler] 추천 주제 emit 완료: {topics_to_emit}")

        except Exception as e:
            logger.error(f"[Scheduler] 추천 생성 중 오류: {e}", exc_info=True)


def start(socketio, app):
    logger.info("[Scheduler] 스케줄러 시작")
    
    scheduler.add_job(
        _run_recommend_task,
        "interval",
        seconds=3600,
        args=[socketio, app],
        id="chat_recommend_job",
        replace_existing=True
    )
    
    scheduler.start()

    # 앱 시작 시 즉시 한 번 실행
    _run_recommend_task(socketio, app)

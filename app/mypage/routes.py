from flask import (
    Blueprint, render_template, request,
    jsonify, session, redirect, url_for, current_app
)
from config import SIDEBAR_CONFIG
from datetime import datetime
from app.mypage.events import send_dm_message
from app.filters.slang_filter import mask_slang
from app.filters.tech_translate import KOREAN_TO_ENGLISH


import json
import pymysql
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from app.mypage.services.interest_vector_service import InterestVectorService
from posts_data.aezen_recommender import load_model





# ------------------------------------------------------------
# DAO import
# ------------------------------------------------------------
from app.mypage.dao.user_dao import UserDao
from app.mypage.dao.alert_dao import AlertDao
from app.mypage.dao.follow_dao import FollowDao
from app.mypage.dao.message_dao import MessageDao
from app.mypage.dao.mypage_posts_dao import MyPagePostsDao
from app.mypage.dao.point_dao import PointDao
from app.mypage.dao.user_info_dao import UserInfoDao
from app.mypage.dao.withdraw_dao import WithdrawDao
from app.mypage.dao.item_dao import ItemDao
from app.mypage.dao.user_item_dao import UserItemDao
from app.mypage.dao.view_log_dao import ViewLogDao
from app.mypage.dao.interest_dao import InterestDao
from app.mypage.dao.interest_vector_dao import InterestVectorDao
from app.mypage.dao.interest_keyword_dao import InterestKeywordDao
from app.mypage.services.keyword_service import KeywordService
# ------------------------------------------------------------
# Blueprint & DAO 객체
# ------------------------------------------------------------
bp = Blueprint(
    "mypage",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/mypage/static"
)
bp.add_app_template_filter(mask_slang, "mask_slang")

# DAO 객체
user_dao = UserDao(lambda: current_app.get_db_connection())
alert_dao = AlertDao(lambda: current_app.get_db_connection())
follow_dao = FollowDao(lambda: current_app.get_db_connection())
message_dao = MessageDao(lambda: current_app.get_db_connection())
posts_dao = MyPagePostsDao(lambda: current_app.get_db_connection())
point_dao = PointDao(lambda: current_app.get_db_connection())
user_info_dao = UserInfoDao(lambda: current_app.get_db_connection())
withdraw_dao = WithdrawDao(lambda: current_app.get_db_connection())
item_dao = ItemDao(lambda: current_app.get_db_connection())
user_item_dao = UserItemDao(lambda: current_app.get_db_connection())
view_log_dao = ViewLogDao(lambda: current_app.get_db_connection())
interest_dao = InterestDao(lambda: current_app.get_db_connection())


def get_interest_vector_dao():
    return InterestVectorDao(
        lambda: current_app.get_db_connection()
    )

_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model
# ------------------------------------------------------------
# 공통 함수
# ------------------------------------------------------------
def get_logged_user():
    return session.get("user")


def require_login_js():
    return """
        <script>
            alert("로그인이 필요합니다.");
            window.location.href = "/";
        </script>
    """


# ------------------------------------------------------------
# 1. 마이페이지 글 목록
# ------------------------------------------------------------
@bp.route("/mypage-posts")
def mypage_posts():
    page = 1
    per_page = 10
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    offset = (page - 1) * per_page

    login_user_id = session.get("user", {}).get("id")
    if not login_user_id:
        return redirect("/")

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND id = %s"
        params_filter = [login_user_id]

        category_map = {
            "자유": 1, "Q&A": 2, "코딩테스트": 3,
            "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6
        }
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        else:
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            format_strings = ','.join(['%s'] * len(board_nos))
            sql = f"""
                SELECT
                    board.board_no AS board_no,
                    board.id AS writer_id,
                    user.nick AS writer_nick,
                    user.icon AS writer_icon,
                    board.board_title,
                    board.board_content,
                    board.board_category,
                    board.hit,
                    board.board_like,
                    board.board_dislike,
                    board.board_created_at,
                    board.board_updated_at,
                    board.board_deleted,
                    comment_answer.comment_answer_no,
                    comment_answer.comment_answer_content,
                    comment_answer.comment_answer_type,
                    comment_answer.comment_like_count,
                    comment_answer.comment_dislike_count,
                    comment_answer.comment_answer_at,
                    comment_answer.comment_answer_updated_at,
                    comment_answer.answer_accepted,
                    comment_user.id AS commenter_id,
                    comment_user.nick AS commenter_nick,
                    file.file_no,
                    file.logical_file_name,
                    file.physical_file_name,
                    file.file_size,
                    file.file_ext,
                    tag.tag_name
                FROM board
                LEFT JOIN user ON board.id = user.id
                LEFT JOIN file ON board.board_no = file.board_no
                LEFT JOIN tag_board ON tag_board.board_no = board.board_no
                LEFT JOIN tag ON tag.tag_no = tag_board.tag_no
                LEFT JOIN comment_answer ON board.board_no = comment_answer.board_no
                LEFT JOIN user AS comment_user ON comment_answer.id = comment_user.id
                WHERE board.board_no IN ({format_strings})
            """
            cursor.execute(sql, tuple(board_nos))
            rows = cursor.fetchall()

            board_map = {}
            for row in rows:
                bno = row["board_no"]
                if bno not in board_map:
                    board_map[bno] = {
                        "boardNo": bno,
                        "id": row["writer_id"],
                        "nick": row["writer_nick"],
                        "icon": row["writer_icon"],
                        "boardTitle": row["board_title"],
                        "boardContent": row["board_content"],
                        "boardCategory": row["board_category"],
                        "hit": row["hit"],
                        "boardLike": row["board_like"],
                        "boardDislike": row["board_dislike"],
                        "boardCreatedAt": row["board_created_at"],
                        "boardUpdatedAt": row["board_updated_at"],
                        "board_deleted": row["board_deleted"],
                        "comments": [],
                        "files": [],
                        "tags": []
                    }
                post = board_map[bno]
                if row.get("file_no") and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
                    post["files"].append({
                        "fileNo": row["file_no"],
                        "logicalFileName": row["logical_file_name"],
                        "physicalFileName": row["physical_file_name"],
                        "fileSize": row["file_size"],
                        "fileExt": row["file_ext"]
                    })
                if row.get("tag_name") and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
                    post["tags"].append({"tagName": row["tag_name"]})
                if row.get("comment_answer_no") and not any(
                    c["commentAnswerNo"] == row["comment_answer_no"]
                    for c in post["comments"]
                ):
                    post["comments"].append({
                        "commentAnswerNo": row["comment_answer_no"],
                        "boardNo": bno,
                        "commenterId": row["commenter_id"],
                        "commenterNick": row["commenter_nick"],
                        "commentAnswerContent": row["comment_answer_content"],
                        "commentLikeCount": row["comment_like_count"],
                        "commentDislikeCount": row["comment_dislike_count"],
                        "commentAnswerAt": row["comment_answer_at"],
                        "commentAnswerUpdatedAt": row["comment_answer_updated_at"],
                        "commentAnswerType": row["comment_answer_type"],
                        "answerAccepted": row["answer_accepted"]
                    })

            boardList = [board_map[b] for b in board_nos if b in board_map]

    finally:
        cursor.close()
        conn.close()

    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순"],
        "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }

    return render_template(
        'mypage-posts.html',
        boardList=boardList,
        show_writeBtn=True,
        show_notice_buttons=True,
        notice_buttons=notice_buttons,
        active="mypage",
        sidebar=SIDEBAR_CONFIG["default"],
        top_filter=top_filter,
        feed_filter=feed_filter,
        login_user_id=login_user_id,
        current_bg=session["user"].get("background_img") or None
    )


@bp.route("/mypage-posts/load")
def mypage_posts_load():
    login_user_id = session.get("user", {}).get("id")
    if not login_user_id:
        return redirect("/")

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    tag_name = request.args.get('tag_name')
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND id = %s"
        params_filter = [login_user_id]

        category_map = {
            "자유": 1, "Q&A": 2, "코딩테스트": 3,
            "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6
        }
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        current_route = request.referrer or ""
        if "/info" in current_route:
            board_filter_sql += " AND board_category = 4"
        elif "/terms" in current_route:
            board_filter_sql += " AND board_category = 5"
        elif "/privacy" in current_route:
            board_filter_sql += " AND board_category = 6"

        if tag_name:
            board_filter_sql += """
                AND board_no IN (
                    SELECT tb.board_no
                    FROM tag_board tb
                    JOIN tag t ON tb.tag_no = t.tag_no
                    WHERE t.tag_name = %s
                )
            """
            params_filter.append(tag_name)

        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        else:
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        cursor.execute(f"{board_filter_sql} {order_clause}", tuple(params_filter))
        all_board_rows = cursor.fetchall()
        all_board_nos = [r['board_no'] for r in all_board_rows]
        board_nos = all_board_nos[offset:offset + per_page]

        if not board_nos:
            return jsonify([])

        format_strings = ','.join(['%s'] * len(board_nos))
        sql = f"""
            SELECT
                board.board_no AS board_no,
                board.id AS writer_id,
                user.nick AS writer_nick,
                user.icon AS writer_icon,
                board.board_title,
                board.board_content,
                board.board_category,
                board.hit,
                board.board_like,
                board.board_dislike,
                board.board_created_at,
                board.board_updated_at,
                board.board_deleted,
                comment_answer.comment_answer_no,
                comment_answer.comment_answer_content,
                comment_answer.comment_answer_type,
                comment_answer.comment_like_count,
                comment_answer.comment_dislike_count,
                comment_answer.comment_answer_at,
                comment_answer.comment_answer_updated_at,
                comment_answer.answer_accepted,
                comment_user.id AS commenter_id,
                comment_user.nick AS commenter_nick,
                file.file_no,
                file.logical_file_name,
                file.physical_file_name,
                file.file_size,
                file.file_ext,
                tag.tag_name
            FROM board
            LEFT JOIN user ON board.id = user.id
            LEFT JOIN file ON board.board_no = file.board_no
            LEFT JOIN tag_board ON tag_board.board_no = board.board_no
            LEFT JOIN tag ON tag.tag_no = tag_board.tag_no
            LEFT JOIN comment_answer ON board.board_no = comment_answer.board_no
            LEFT JOIN user AS comment_user ON comment_answer.id = comment_user.id
            WHERE board.board_no IN ({format_strings})
        """
        cursor.execute(sql, tuple(board_nos))
        rows = cursor.fetchall()

        board_map = {}
        for row in rows:
            bno = row["board_no"]
            if bno not in board_map:
                board_map[bno] = {
                    "boardNo": bno,
                    "id": row["writer_id"],
                    "nick": row["writer_nick"],
                    "icon": row["writer_icon"],
                    "boardTitle": row["board_title"],
                    "boardContent": row["board_content"],
                    "boardCategory": row["board_category"],
                    "hit": row["hit"],
                    "boardLike": row["board_like"],
                    "boardDislike": row["board_dislike"],
                    "boardCreatedAt": row["board_created_at"],
                    "boardUpdatedAt": row["board_updated_at"],
                    "board_deleted": row["board_deleted"],
                    "comments": [],
                    "files": [],
                    "tags": []
                }
            post = board_map[bno]
            if row.get("file_no") and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
                post["files"].append({
                    "fileNo": row["file_no"],
                    "logicalFileName": row["logical_file_name"],
                    "physicalFileName": row["physical_file_name"],
                    "fileSize": row["file_size"],
                    "fileExt": row["file_ext"]
                })
            if row.get("tag_name") and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
                post["tags"].append({"tagName": row["tag_name"]})
            if row.get("comment_answer_no") and not any(
                c["commentAnswerNo"] == row["comment_answer_no"]
                for c in post["comments"]
            ):
                post["comments"].append({
                    "commentAnswerNo": row["comment_answer_no"],
                    "boardNo": bno,
                    "commenterId": row["commenter_id"],
                    "commenterNick": row["commenter_nick"],
                    "commentAnswerContent": row["comment_answer_content"],
                    "commentLikeCount": row["comment_like_count"],
                    "commentDislikeCount": row["comment_dislike_count"],
                    "commentAnswerAt": row["comment_answer_at"],
                    "commentAnswerUpdatedAt": row["comment_answer_updated_at"],
                    "commentAnswerType": row["comment_answer_type"],
                    "answerAccepted": row["answer_accepted"]
                })

        boardList = [board_map[b] for b in board_nos if b in board_map]

        return jsonify(boardList)

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# 2. 게시글 상세 API
# ------------------------------------------------------------
@bp.route("/api/mypage/post/<int:board_no>")
def api_mypage_post_detail(board_no):
    print("🔥 ENTER mypage_board_detail", board_no)
    return {
        "post": posts_dao.get_post_detail(board_no),
        "files": posts_dao.get_files_by_board(board_no),
        "tags": posts_dao.get_tags_by_board(board_no),
        "comments": posts_dao.get_comments_by_board(board_no)
    }


@bp.route("/api/log/view", methods=["POST"])
def api_log_view():
    user = session.get("user")
    if not user:
        return jsonify({"success": False}), 403

    data = request.get_json()
    board_no = data.get("board_no")
    if not board_no:
        return jsonify({"success": False}), 400

    user_id = user["id"]

    # 1️⃣ 조회 로그
    view_log_dao.insert_view_log(user_id, board_no)

    # 2️⃣ 게시글 텍스트
    post = interest_dao.get_post_with_tags(board_no)
    if not post:
        return jsonify({"success": True})

    text = f"{post['board_title']} {post['board_content']} {' '.join(post['tags'])}"

    # 3️⃣ 벡터 업데이트
    model = get_model()
    post_vec = model.encode(text)

    vector_dao = get_interest_vector_dao()
    user_vec = vector_dao.load_vector(user_id)

    if user_vec is None:
        user_vec = post_vec * 0.05
    else:
        user_vec = user_vec + (post_vec * 0.05)

    InterestVectorService(vector_dao).save_vector_with_keywords(
        user_id, user_vec
    )

    # 4️⃣ 키워드 점수 업데이트
    keyword_counter = KeywordService._extract_from_text(text)
    keyword_dao = InterestKeywordDao(
        lambda: current_app.get_db_connection()
    )

    for kw, score in keyword_counter.items():
        keyword_dao.add_score(
            user_id=user_id,
            keyword=kw,
            delta=score * 1.0
        )

    print("🔥 INTEREST UPDATED:", board_no)

    return jsonify({"success": True})



@bp.route("/board/<int:board_no>")
def mypage_board_detail(board_no):
    post_detail = posts_dao.get_post_detail(board_no)
    files = posts_dao.get_files_by_board(board_no)
    tags = posts_dao.get_tags_by_board(board_no)
    comments = posts_dao.get_comments_by_board(board_no)

    for f in files:
        if "file_ext" in f and "fileExt" not in f:
            f["fileExt"] = f["file_ext"]
        if f.get("fileExt") is None:
            f["fileExt"] = ""

    if not post_detail:
        return "<script>alert('게시글을 찾을 수 없습니다.'); history.back();</script>"

    boardList = [{
        "boardNo": post_detail["board_no"],
        "id": post_detail["id"],
        "nick": post_detail["writer_nick"],
        "boardTitle": post_detail["board_title"],
        "boardContent": post_detail["board_content"],
        "boardCategory": post_detail["board_category"],
        "hit": post_detail["hit"],
        "boardLike": post_detail["board_like"],
        "boardDislike": post_detail["board_dislike"],
        "boardCreatedAt": post_detail["board_created_at"],
        "boardUpdatedAt": post_detail["board_updated_at"],
        "board_deleted": post_detail["board_deleted"],
        "files": files,
        "tags": tags,
        "comments": comments
    }]

    login_user_id = session.get("user", {}).get("id")

    # -------------------------------------------------
    # 유저 벡터 + 키워드 반영 (HOME / JS 수정 없음)
    # -------------------------------------------------
    user = session.get("user")
    if user:
        user_id = user["id"]

        post = interest_dao.get_post_with_tags(board_no)
        if post:
            text = f"{post['board_title']} {post['board_content']} {' '.join(post['tags'])}"

            # 1️⃣ 벡터 반영
            model = get_model()
            post_vec = model.encode(text)

            interest_vector_dao = get_interest_vector_dao()
            user_vec = interest_vector_dao.load_vector(user_id)

            if user_vec is None:
                user_vec = post_vec * 0.05
            else:
                user_vec = user_vec + (post_vec * 0.05)

            InterestVectorService(interest_vector_dao) \
                .save_vector_with_keywords(user_id, user_vec)

            # 2️⃣ 키워드 점수 반영 (🔥 핵심)
            from app.mypage.services.keyword_service import KeywordService
            from app.mypage.dao.interest_keyword_dao import InterestKeywordDao

            keyword_counter = KeywordService._extract_from_text(text)

            if keyword_counter:
                keyword_dao = InterestKeywordDao(
                    lambda: current_app.get_db_connection()
                )

                for kw, score in keyword_counter.items():
                    keyword_dao.add_score(
                        user_id=user_id,
                        keyword=kw,
                        delta=score * 1.0  # ← 가중치 1
                    )

    return render_template(
        "home.html",
        boardList=boardList,
        show_writeBtn=False,
        show_notice_buttons=False,
        sidebar=SIDEBAR_CONFIG["default"],
        active="chat",
        login_user_id=login_user_id
    )

# ------------------------------------------------------------
# 3. 관심사 페이지
# ------------------------------------------------------------
# ------------------------------------------------------------
# 3. 관심사 페이지
# ------------------------------------------------------------
@bp.route("/mypage-interest")
def mypage_interest():
    user = session.get("user")
    if not user:
        return require_login_js()

    user_id = user["id"]

    interest_vector_dao = get_interest_vector_dao()
    keyword_dao = InterestKeywordDao(
        lambda: current_app.get_db_connection()
    )

    # --------------------------------------------------
    # 1️⃣ DB 조회 (계산 ❌)
    # --------------------------------------------------
    user_vector = interest_vector_dao.load_vector(user_id)
    scores_map = keyword_dao.get_scores_map(user_id)  # {kw: score}

    # TOP 5 키워드
    sorted_keywords = sorted(
        scores_map.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    top5_labels = [k for k, _ in sorted_keywords]
    top5_values = [v for _, v in sorted_keywords]

    # --------------------------------------------------
    # 벡터 없으면 빈 상태
    # --------------------------------------------------
    if user_vector is None:
        return render_template(
            "mypage-interest.html",
            sidebar=SIDEBAR_CONFIG["default"],
            active="mypage",
            radar_labels=["No Data"],
            radar_values=[0],
            recommended_articles=[],
            top5_labels=top5_labels or ["No Data"],
            top5_values=[1] * len(top5_labels) if top5_labels else [0],
            current_bg=session["user"].get("background_img") or None
        )

    # --------------------------------------------------
    # 2️⃣ 레이더 그래프 (가벼운 계산만)
    # --------------------------------------------------
    from app.mypage.utils.tech_category import TECH_CATEGORY

    radar_labels = list(TECH_CATEGORY.keys())
    radar_values = []

    for category, keywords in TECH_CATEGORY.items():
        score = sum(scores_map.get(kw, 0) for kw in keywords)
        radar_values.append(round(score, 2))

    # 🔒 값이 전부 0이거나 비어 있을 경우 안전 처리
    if not radar_values or max(radar_values) == 0:
        radar_values = [0] * len(radar_labels)
    else:
        max_val = max(radar_values)
        radar_values = [round(v / max_val, 3) for v in radar_values]


    # --------------------------------------------------
    # 3️⃣ AI 추천 글 (벡터만 사용)
    # --------------------------------------------------
    from app.mypage.services.post_recommender import PostRecommender

    recommended_articles = PostRecommender.recommend(
        user_vector=user_vector,
        top_n=5
    )

    # --------------------------------------------------
    # 렌더링
    # --------------------------------------------------
    return render_template(
        "mypage-interest.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        radar_labels=radar_labels,
        radar_values=radar_values,
        recommended_articles=recommended_articles,
        top5_labels=top5_labels or ["No Data"],
        top5_values=top5_values or [0],
        current_bg=session["user"].get("background_img") or None
    )





# ------------------------------------------------------------
# 관심 피드백 — 유저 벡터 조정
# ------------------------------------------------------------
@bp.route("/mypage-interest/feedback", methods=["POST"])
def mypage_interest_feedback():
    user = session.get("user")
    if not user:
        return jsonify(ok=False), 401
    interest_vector_dao = get_interest_vector_dao()

    user_id = user["id"]
    data = request.get_json() or {}

    board_no = data.get("board_no")
    action = data.get("action")  # "like" or "dislike"

    if not board_no or action not in ("like", "dislike"):
        return jsonify(ok=False, error="invalid_params"), 400

    post = interest_dao.get_post_with_tags(board_no)
    if not post:
        return jsonify(ok=False, error="post_not_found"), 404

    text = f"{post['board_title']} {post['board_content']} {' '.join(post['tags'])}"

    model = get_model()
    post_vec = model.encode(text)

    user_vec = interest_vector_dao.load_vector(user_id)
    if user_vec is None:
        user_vec = np.zeros_like(post_vec)

    if action == "like":
        user_vec = user_vec + (post_vec * 0.2)
    else:
        user_vec = user_vec - (post_vec * 0.3)

    service = InterestVectorService(interest_vector_dao)
    service.save_vector_with_keywords(user_id, user_vec)


    return jsonify(ok=True)


# ------------------------------------------------------------
# 4. 광고 추천
# ------------------------------------------------------------
def get_rotating_category():
    categories = [0, 1, 2]  # 인프런, 교보, 원티드
    now = datetime.now()
    index = (now.minute // 10) % len(categories)
    return categories[index]


@bp.route("/api/recommend_ads")
def api_recommend_ads():
    user = session.get("user")
    if not user:
        return jsonify([])

    user_id = user["id"]
    interest_vector_dao = get_interest_vector_dao()

    user_vec = interest_vector_dao.load_vector(user_id)

    if user_vec is None:
        conn = current_app.get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT value FROM user_attributes WHERE user_id=%s", (user_id,))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if rows:
            text = " ".join([r["value"] for r in rows]).strip()
            if text:
                model = get_model()
                user_vec = model.encode(text)
                service = InterestVectorService(interest_vector_dao)
                service.save_vector_with_keywords(user_id, user_vec)


        if user_vec is None:
            return jsonify([])

    user_vec = np.array(user_vec, dtype=float)

    category = get_rotating_category()

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT ad_id, ad_title, ad_image_url, landing_url, ad_embedding
        FROM ad
        WHERE is_active=1 
          AND ad_embedding IS NOT NULL
          AND ad_category=%s
    """, (category,))

    ads = cursor.fetchall()

    cursor.close()
    conn.close()

    if not ads:
        return jsonify([])

    result = []
    for ad in ads:
        try:
            ad_vec = np.array(json.loads(ad["ad_embedding"]))
        except Exception:
            continue

        sim = float(cosine_similarity([user_vec], [ad_vec])[0][0])

        result.append({
            "ad_id": ad["ad_id"],
            "title": ad["ad_title"],
            "image": ad["ad_image_url"],
            "url": ad["landing_url"],
            "score": sim
        })

    result.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(result[:3])


@bp.route("/api/ad/view", methods=["POST"])
def api_ad_view():
    data = request.get_json() or {}
    ad_id = data.get("ad_id")

    if not ad_id:
        return jsonify(success=False, msg="ad_id 없음"), 400

    conn = current_app.get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO ad_stats (ad_id, views, clicks)
            VALUES (%s, 1, 0)
            ON DUPLICATE KEY UPDATE views = views + 1
        """, (ad_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify(success=True)


@bp.route("/api/ad/click", methods=["POST"])
def api_ad_click():
    user = session.get("user")
    if not user:
        return jsonify(success=False, msg="로그인 필요"), 403

    data = request.get_json() or {}
    ad_id = data.get("ad_id")

    if not ad_id:
        return jsonify(success=False, msg="ad_id 없음"), 400

    user_id = user["id"]

    conn = current_app.get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO ad_click_log (user_id, ad_id)
            VALUES (%s, %s)
        """, (user_id, ad_id))

        cursor.execute("""
            INSERT INTO ad_stats (ad_id, views, clicks)
            VALUES (%s, 0, 1)
            ON DUPLICATE KEY UPDATE clicks = clicks + 1
        """, (ad_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify(success=True)


# ------------------------------------------------------------
# 5. 아이템 관리 페이지 (인피니티 스크롤 포함)
# ------------------------------------------------------------
@bp.route('/mypage-items')
def mypage_items():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    items = user_item_dao.get_user_items_page(user_id, offset=0, limit=12)

    return render_template(
        'mypage-items.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        items=items
    )


@bp.route("/api/mypage/item/equip", methods=["POST"])
def api_item_equip():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    user_id = user["id"]
    item_no = request.json.get("item_no")

    item = item_dao.get_item(item_no)
    if not item:
        return jsonify({"success": False, "msg": "아이템 없음"}), 400

    item_type = item["item_type"]
    item_img = item["item_img"]

    user_item_dao.unequip_type(user_id, item_type)
    user_item_dao.equip_item(user_id, item_no)
    user_item_dao.update_user_profile(user_id, item_type, item_img)

    if item_type == "background":
        session["user"]["background_img"] = item_img
    elif item_type == "icon":
        session["user"]["icon"] = item_img
    elif item_type == "insignia":
        session["user"]["insignia"] = item_img

    session.modified = True

    return jsonify({
        "success": True,
        "item_type": item_type,
        "item_img": item_img
    })


@bp.route("/api/mypage/item/unequip", methods=["POST"])
def api_item_unequip():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    request_data = request.get_json() or {}
    item_no = request_data.get("item_no")

    if not item_no:
        return jsonify({"success": False, "msg": "item_no 없음"}), 400

    user_id = user["id"]

    item = item_dao.get_item(item_no)
    if not item:
        return jsonify({"success": False, "msg": "아이템 없음"}), 400

    item_type = item["item_type"]

    user_item_dao.unequip_item(user_id, item_no)
    user_item_dao.update_user_profile(user_id, item_type, None)

    if item_type == "background":
        session["user"]["background_img"] = None
    elif item_type == "icon":
        session["user"]["icon"] = None
    elif item_type == "insignia":
        session["user"]["insignia"] = None

    session.modified = True

    return jsonify({
        "success": True,
        "item_type": item_type,
        "item_img": None
    })


@bp.route("/mypage-items/load")
def mypage_items_load():
    user = get_logged_user()
    if not user:
        return jsonify([]), 403

    user_id = user["id"]

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get("per_page", 12))
    except ValueError:
        per_page = 12

    offset = (page - 1) * per_page

    rows = user_item_dao.get_user_items_page(user_id, offset=offset, limit=per_page)

    result = []
    for row in rows:
        result.append({
            "item_no":      row["item_no"],
            "item_name":    row["item_name"],
            "item_type":    row["item_type"],
            "item_img_url": url_for("mypage.static", filename=row["item_img"]),
            "is_equipped":  bool(row["is_equipped"]),
        })

    return jsonify(result)


# ------------------------------------------------------------
# 6. 내 정보 페이지
# ------------------------------------------------------------
@bp.route("/mypage-info")
def mypage_info():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    user_info = user_info_dao.get_user_by_id(user_id)

    return render_template(
        "mypage-info.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        user=user_info,
        current_bg=session["user"].get("background_img") or None
    )


# ------------------------------------------------------------
# 7. 닉네임/이메일 중복 확인
# ------------------------------------------------------------
@bp.route("/api/mypage/check-nickname", methods=["POST"])
def api_check_nickname():
    data = request.get_json()
    nickname = (data.get("nickname") or "").strip()
    exists = user_info_dao.check_nickname_exists(nickname)
    return jsonify({"success": True, "exists": exists})


@bp.route("/api/mypage/check-email", methods=["POST"])
def api_check_email():
    data = request.get_json()
    email = (data.get("email") or "").strip()
    exists = user_info_dao.check_email_exists(email)
    return jsonify({"success": True, "exists": exists})


# ------------------------------------------------------------
# 8. 프로필 수정
# ------------------------------------------------------------
@bp.route("/api/mypage/update-profile", methods=["POST"])
def api_update_profile():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False, "msg": "로그인 필요"}), 403

    user_id = user["id"]
    data = request.get_json()

    new_password = (data.get("password") or "").strip()
    new_nick = (data.get("nickname") or "").strip()
    new_email = (data.get("email") or "").strip()

    current = user_info_dao.get_user_by_id(user_id)

    if new_nick != current["nick"] and user_info_dao.check_nickname_exists(new_nick):
        return jsonify({"success": False, "msg": "이미 사용 중인 닉네임입니다."})

    if new_email != current["email"] and user_info_dao.check_email_exists(new_email):
        return jsonify({"success": False, "msg": "이미 사용 중인 이메일입니다."})

    if new_password:
        user_info_dao.update_password(user_id, new_password)

    user_info_dao.update_user_info(user_id, new_nick, new_email)

    user["nick"] = new_nick
    user["email"] = new_email
    session["user"] = user
    session.modified = True

    return jsonify({"success": True})


# ------------------------------------------------------------
# 9. 팔로잉 / 팔로워
# ------------------------------------------------------------
@bp.route("/mypage-following")
def mypage_following():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    following = follow_dao.get_following_list(user_id)

    for f in following:
        f["is_following"] = True

    return render_template(
        "mypage-following.html",
        following_list=following,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None
    )


@bp.route("/mypage-follower")
def mypage_follower():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    followers = follow_dao.get_follower_list(user_id)

    for f in followers:
        f["is_following"] = follow_dao.is_following(user_id, f["user_id"])

    return render_template(
        "mypage-follower.html",
        follower_list=followers,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None
    )


@bp.route("/api/follow-toggle", methods=["POST"])
def api_follow_toggle():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False, "msg": "로그인 필요"}), 403

    user_id = user["id"]
    data = request.get_json()
    target_id = data.get("target_id")
    do_follow = data.get("follow")

    if do_follow:
        ok = follow_dao.follow(user_id, target_id)

        if ok and user_id != target_id:
            alert_dao.create_alert(
                sender_id=user_id,
                receiver_id=target_id,
                alert_type=301,
                alert_content=f"{user['nick']} 님이 당신을 팔로우했습니다."
            )

        return jsonify({"success": ok})
    else:
        return jsonify({"success": follow_dao.unfollow(user_id, target_id)})


@bp.route("/mypage-following/load")
def mypage_following_load():
    user = get_logged_user()
    if not user:
        return jsonify([]), 403

    user_id = user["id"]

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except Exception:
        return jsonify([])

    offset = (page - 1) * per_page
    rows = follow_dao.get_following_page(user_id, offset, per_page)

    result = []
    for r in rows:
        result.append({
            "user_id": r["user_id"],
            "nickname": r["nickname"],
            "icon": url_for("mypage.static", filename=r["icon"]) if r["icon"] else None,
            "is_following": True
        })

    return jsonify(result)


@bp.route("/mypage-follower/load")
def mypage_follower_load():
    user = get_logged_user()
    if not user:
        return jsonify([]), 403

    user_id = user["id"]

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except Exception:
        return jsonify([])

    offset = (page - 1) * per_page
    rows = follow_dao.get_follower_page(user_id, offset, per_page)

    result = []
    for r in rows:
        result.append({
            "user_id": r["user_id"],
            "nickname": r["nickname"],
            "icon": url_for("mypage.static", filename=r["icon"]) if r["icon"] else None,
            "is_following": follow_dao.is_following(user_id, r["user_id"])
        })

    return jsonify(result)


# ------------------------------------------------------------
# 10. 메시지 기능
# ------------------------------------------------------------
@bp.route("/mypage-message")
def mypage_message():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    rooms = message_dao.get_rooms_for_user(user_id)
    total_unread = sum(r["unread_count"] for r in rooms)
    follow_list = follow_dao.get_following_list(user_id)

    return render_template(
        "mypage-message.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        rooms=rooms,
        user_id=user_id,
        follow_list=follow_list,
        total_unread=total_unread
    )


@bp.route("/mypage-message/room/<int:room_no>")
def mypage_message_room(room_no):
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    room = message_dao.get_room_info(room_no, user_id)
    if not room:
        return require_login_js()

    return render_template(
        "mypage-room.html",
        room_no=room_no,
        partner_id=room["partner_id"],
        partner_nick=room["partner_nick"],
        user_id=user_id,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None
    )


@bp.route("/api/mypage/messages/room/<int:room_no>")
def api_get_room_messages(room_no):
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    user_id = user["id"]
    rows = message_dao.get_room_messages(room_no, user_id)
    message_dao.mark_room_as_read(room_no, user_id)

    messages = [{
        "message_no": row["message_no"],
        "room_no": row["room_no"],
        "sender_id": row["sender_id"],
        "receiver_id": row["receiver_id"],
        "is_me": row["sender_id"] == user_id,
        "content": mask_slang(row["message_content"]),
        "sent_at": row["message_sent_at"].strftime("%Y-%m-%d %H:%M")
    } for row in rows]

    return jsonify({"success": True, "messages": messages})


@bp.route("/api/mypage/messages/send", methods=["POST"])
def api_send_message():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    user_id = user["id"]
    data = request.get_json()

    receiver_id = data.get("receiver_id")
    content = data.get("content", "").strip()
    room_no = data.get("room_no")

    if not receiver_id or not content:
        return jsonify({"success": False, "msg": "잘못된 요청"}), 400

    if not room_no:
        room_no = message_dao.create_or_get_room(user_id, receiver_id)

    msg_no = message_dao.send_message(room_no, user_id, receiver_id, content)
    masked = mask_slang(content)

    receiver_info = user_dao.get_user_by_id(receiver_id)

    send_dm_message(
        receiver_id,
        {
            "room_no": room_no,
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "content": masked,
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    )

    return jsonify({
        "success": True,
        "room_no": room_no,
        "message_no": msg_no,
        "sender_id": user_id,
        "receiver_nick": receiver_info["nick"],
        "content": masked,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })


@bp.route("/api/mypage/messages/delete-room", methods=["POST"])
def api_delete_room():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    user_id = user["id"]
    data = request.get_json()
    room_nos = data.get("room_nos") or []

    for rn in room_nos:
        message_dao.delete_room_for_user(int(rn), user_id)

    return jsonify({"success": True})


@bp.route("/api/mypage/search-user", methods=["POST"])
def api_search_user():
    data = request.get_json()
    keyword = f"%{data.get('keyword', '')}%"

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT id, nick 
        FROM user
        WHERE id LIKE %s OR nick LIKE %s
        LIMIT 20
    """, (keyword, keyword))

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(users)


@bp.route("/api/mypage/message/start", methods=["POST"])
def api_start_message():
    user = session.get("user")
    if not user:
        return jsonify(success=False), 403

    data = request.get_json()
    target_id = data.get("target_id")
    content = data.get("content")

    if not target_id or not content:
        return jsonify(success=False), 400

    sender_id = user["id"]

    room_no = message_dao.create_or_get_room(sender_id, target_id)
    message_dao.send_message(room_no, sender_id, target_id, content)

    masked_content = mask_slang(content)

    return jsonify(success=True, room_no=room_no, content=masked_content)

@bp.route("/mypage-message/start/<string:target_id>")
def mypage_message_start(target_id):
    user = get_logged_user()
    if not user:
        return require_login_js()

    sender_id = user["id"]

    # 자기 자신에게 메시지 방지
    if sender_id == target_id:
        return """
            <script>
                alert("자기 자신에게는 메시지를 보낼 수 없습니다.");
                history.back();
            </script>
        """

    # 방 생성 또는 조회
    room_no = message_dao.create_or_get_room(sender_id, target_id)

    # 바로 방으로 이동
    return redirect(url_for(
        "mypage.mypage_message_room",
        room_no=room_no
    ))


# ------------------------------------------------------------
# 11. 포인트
# ------------------------------------------------------------
@bp.route("/mypage-point")
def mypage_point():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    order = request.args.get("order", "latest")

    point_list = list(point_dao.get_point_history(user_id, order=order))
    user_point = user["user_current_point"]

    sorted_list = point_list.copy()
    sorted_list.sort(key=lambda r: r["point_created_at"], reverse=True)

    balance_map = {}
    balance = user_point

    for row in sorted_list:
        balance_map[row["point_no"]] = balance
        balance -= row["point_amount"]

    for row in point_list:
        row["remain_point"] = balance_map[row["point_no"]]

    return render_template(
        "mypage-point.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        point_list=point_list,
        user_point=user_point
    )


@bp.route("/mypage-point/load")
def mypage_point_load():
    user = get_logged_user()
    if not user:
        return jsonify([]), 403

    user_id = user["id"]

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        order = request.args.get("order", "latest")
    except Exception:
        return jsonify([])

    offset = (page - 1) * per_page

    rows = point_dao.get_point_history_page(
        user_id=user_id,
        order=order,
        offset=offset,
        limit=per_page
    )

    if not rows:
        return jsonify([])

    user_point = user["user_current_point"]

    temp_rows = list(rows)
    temp_rows.sort(key=lambda r: r["point_created_at"], reverse=True)

    if page == 1:
        balance = user_point
    else:
        prior_rows = point_dao.get_point_history_page(
            user_id=user_id,
            order="latest",
            offset=0,
            limit=offset + len(rows)
        )
        balance = user_point
        for r in prior_rows:
            balance -= r["point_amount"]

    remain_map = {}
    for r in temp_rows:
        remain_map[r["point_no"]] = balance
        balance -= r["point_amount"]

    output = []
    for r in rows:
        output.append({
            "point_no": r["point_no"],
            "point_created_at": r["point_created_at"].strftime("%Y-%m-%d"),
            "point_reason": r["point_reason"],
            "point_amount": r["point_amount"],
            "remain_point": remain_map[r["point_no"]],
            "board_no": r["board_no"],
            "point_type": r["point_type"]
        })

    return jsonify(output)


# ------------------------------------------------------------
# 12. 알림
# ------------------------------------------------------------
@bp.route("/mypage-alert")
def mypage_alert():
    user = get_logged_user()
    if not user:
        return require_login_js()

    alerts = alert_dao.get_alert_list(user["id"])

    return render_template(
        "mypage-alert.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        alerts=alerts
    )


@bp.route("/api/alert/delete", methods=["POST"])
def api_alert_delete():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    data = request.get_json()
    alert_dao.delete_alert(data.get("alert_no"), user["id"])
    return jsonify({"success": True})


@bp.route("/api/alert/delete-all", methods=["POST"])
def api_alert_delete_all():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    alert_dao.delete_all_alerts(user["id"])
    return jsonify({"success": True})


@bp.route("/mypage-alert/load")
def mypage_alert_load():
    user = get_logged_user()
    if not user:
        return jsonify([]), 403

    user_id = user["id"]

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except Exception:
        return jsonify([])

    offset = (page - 1) * per_page
    rows = alert_dao.get_alert_page(user_id, offset, per_page)

    result = []
    for r in rows:
        type_map = {
            101: "댓글",
            201: "좋아요",
            301: "팔로우",
            401: "포인트 적립",
            402: "포인트 사용",
            501: "답변 채택",
            901: "공지"
        }

        type_str = type_map.get(r["alert_type"], "알림")

        result.append({
            "alert_no": r["alert_no"],
            "alert_content": r["alert_content"],
            "alert_type": type_str,
            "alerted_at": r["alerted_at"].strftime("%Y-%m-%d %H:%M"),
            "target_board_no": r["target_board_no"],
            "target_comment_answer_no": r["target_comment_answer_no"]
        })

    return jsonify(result)


# ------------------------------------------------------------
# 13. 회원 탈퇴
# ------------------------------------------------------------
@bp.route("/mypage-withdraw")
def mypage_withdraw():
    user = get_logged_user()
    if not user:
        return require_login_js()

    return render_template(
        "mypage-withdraw.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None
    )


@bp.route("/api/mypage/withdraw", methods=["POST"])
def api_withdraw():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False, "msg": "로그인 필요"}), 403

    data = request.get_json() or {}
    user_id = data.get("id")
    password = data.get("pw")

    if not user_id or not password:
        return jsonify({"success": False, "msg": "아이디/비밀번호 필요"}), 400

    user_row = user_dao.check_login(user_id, password)
    if not user_row:
        return jsonify({"success": False, "msg": "아이디 또는 비밀번호 불일치"}), 400

    withdraw_dao.withdraw_user(user_id)
    session.pop("user", None)

    return jsonify({"success": True})


# ------------------------------------------------------------
# 14. 포인트샵
# ------------------------------------------------------------
@bp.route("/pointshop")
def pointshop():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_items = user_item_dao.get_user_items(user["id"])
    owned = {item["item_no"] for item in user_items}

    products = item_dao.get_all_items()
    for p in products:
        p["owned"] = (p["item_no"] in owned)

    user_point = user["user_current_point"]

    return render_template(
        "pointshop.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        products=products,
        user_point=user_point
    )


@bp.route("/api/mypage/item/buy", methods=["POST"])
def api_item_buy():
    user = get_logged_user()
    if not user:
        return jsonify(success=False, msg="로그인 필요"), 403

    item_no = request.json.get("item_no")
    user_id = user["id"]

    item = item_dao.get_item(item_no)
    if not item:
        return jsonify(success=False, msg="아이템 없음"), 400

    price = item["item_price"]

    if user_item_dao.has_item(user_id, item_no):
        return jsonify(success=False, msg="이미 보유한 아이템입니다."), 400

    current_point = point_dao.get_total_point(user_id)
    if current_point < price:
        return jsonify(success=False, msg="포인트 부족"), 400

    point_dao.use_point(user_id, price, f"아이템 구매: {item['item_name']}")
    user_item_dao.add_item(user_id, item_no)

    session["user"]["user_current_point"] = current_point - price
    session.modified = True

    return jsonify(
        success=True,
        new_point=session["user"]["user_current_point"]
    )

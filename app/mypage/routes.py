from flask import Blueprint, render_template, request, jsonify, session, redirect
from config import SIDEBAR_CONFIG
from flask import current_app 
from datetime import datetime
from app.mypage.events import send_dm_message
import re
from collections import Counter
import pymysql

from recommend.aezen_recommender import (
    build_user_vector, recommend_articles
)





# DAO
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



# DAO 객체
user_dao = UserDao(lambda: current_app.get_db_connection())
alert_dao = AlertDao(lambda: current_app.get_db_connection())
follow_dao = FollowDao(lambda: current_app.get_db_connection())
message_dao = MessageDao(lambda: current_app.get_db_connection())
posts_dao = MyPagePostsDao(lambda: current_app.get_db_connection())
point_dao = PointDao(lambda:current_app.get_db_connection())
user_info_dao = UserInfoDao(lambda: current_app.get_db_connection())
withdraw_dao = WithdrawDao(lambda: current_app.get_db_connection())
item_dao = ItemDao(lambda: current_app.get_db_connection())
user_item_dao = UserItemDao(lambda: current_app.get_db_connection())
view_log_dao = ViewLogDao(lambda: current_app.get_db_connection())
interest_dao = InterestDao(lambda: current_app.get_db_connection())
interest_vector_dao = InterestVectorDao(lambda: current_app.get_db_connection())

bp = Blueprint(
    "mypage",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/mypage/static"
)

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
        # 1️⃣ 기본 필터: 로그인한 사용자가 작성한 글
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND id = %s"
        params_filter = [login_user_id]

        # feed 필터 적용
        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        # 2️⃣ 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        else:  # 최신순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 3️⃣ LIMIT + OFFSET
        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        # 게시글 번호 조회
        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            # 상세 조회
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

            # 게시글 조립
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
                if row.get("comment_answer_no") and not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
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

# ------------------------------------------------------------
# 2. 게시글 상세 API
# ------------------------------------------------------------
@bp.route("/api/mypage/post/<int:board_no>")
def api_mypage_post_detail(board_no):
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
        return jsonify({"success": False, "msg": "board_no 없음"}), 400

    view_log_dao.insert_view_log(user["id"], board_no)

    return jsonify({"success": True})

@bp.route("/board/<int:board_no>")
def mypage_board_detail(board_no):
    # 게시글 데이터 가져오기
    post = posts_dao.get_post_detail(board_no)
    files = posts_dao.get_files_by_board(board_no)
    tags = posts_dao.get_tags_by_board(board_no)
    comments = posts_dao.get_comments_by_board(board_no)

    if not post:
        return "<script>alert('게시글을 찾을 수 없습니다.'); history.back();</script>"

    # boardList 형식 그대로 맞추기
    boardList = [{
        "boardNo": post["board_no"],
        "id": post["id"],
        "nick": post["writer_nick"],
        "boardTitle": post["board_title"],
        "boardContent": post["board_content"],
        "boardCategory": post["board_category"],
        "hit": post["hit"],
        "boardLike": post["board_like"],
        "boardDislike": post["board_dislike"],
        "boardCreatedAt": post["board_created_at"],
        "boardUpdatedAt": post["board_updated_at"],
        "board_deleted": post["board_deleted"],
        "files": files,
        "tags": tags,
        "comments": comments
    }]

    login_user_id = session.get("user", {}).get("id")

    return render_template(
        "home.html",
        boardList=boardList,        # 하나만 넣어서 렌더링
        show_writeBtn=False,        # 상세 페이지에서는 글쓰기 버튼 숨기는 게 자연스럽다
        show_notice_buttons=False,  # 필요하면 유지해도 됨
        sidebar=SIDEBAR_CONFIG["default"],
        active="chat",
        login_user_id=login_user_id
    )


# ------------------------------------------------------------
# 3. 관심사 페이지
# ------------------------------------------------------------


# ------------------------------------------------------------
# 기술 키워드 사전
# ------------------------------------------------------------
TECH_KEYWORDS = {
    "python", "java", "c", "c++", "javascript", "typescript",
    "react", "vue", "svelte", "nextjs",
    "spring", "django", "flask", "fastapi", "node",
    "sql", "mysql", "oracle", "postgres", "mongodb",
    "ai", "ml", "deeplearning", "pytorch", "tensorflow",
    "docker", "k8s", "kubernetes", "aws", "gcp", "azure"
}

# ------------------------------------------------------------
# 분야별 매핑 (Radar Chart용)
# ------------------------------------------------------------
TECH_CATEGORY = {
    "Frontend": ["react", "vue", "svelte", "javascript", "typescript", "nextjs"],
    "Backend": ["python", "java", "spring", "django", "fastapi", "flask", "node"],
    "Database": ["sql", "mysql", "oracle", "postgres", "mongodb"],
    "AI/ML": ["ai", "ml", "deeplearning", "pytorch", "tensorflow"],
    "DevOps": ["docker", "k8s", "kubernetes", "aws", "gcp", "azure"]
}

# ------------------------------------------------------------
# 키워드 추출 함수
# ------------------------------------------------------------
def extract_keywords(text):
    if not text:
        return []
    text = text.lower()
    found = []
    for kw in TECH_KEYWORDS:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, text):
            found.append(kw)
    return found



# ------------------------------------------------------------
# 관심도 분석 + BERT 추천 라우트 (완성본)
# ------------------------------------------------------------
@bp.route("/mypage-interest")
def mypage_interest():

    user = session.get("user")
    if not user:
        return require_login_js()

    user_id = user["id"]

    # -----------------------------
    # 1) 태그 / 텍스트 데이터 수집
    # -----------------------------
    tag_data = interest_dao.get_all_tags(user_id)
    written_tags = tag_data["written_tags"]
    viewed_tags = tag_data["viewed_tags"]

    text_sources = interest_dao.get_all_text_sources(user_id)
    written_posts = text_sources["written_posts"]
    viewed_posts = text_sources["viewed_posts"]
    written_comments = text_sources["written_comments"]
    viewed_comments = text_sources["viewed_comments"]

    # -----------------------------
    # 2) 그래프 키워드 분석
    # -----------------------------
    tag_keywords = written_tags + viewed_tags
    text_keywords = []

    for p in written_posts + viewed_posts:
        text_keywords += extract_keywords(p["board_title"])
        text_keywords += extract_keywords(p["board_content"])

    for c in written_comments + viewed_comments:
        text_keywords += extract_keywords(c["comment_answer_content"])

    all_keywords = tag_keywords + text_keywords
    counter = Counter(all_keywords)

    # TOP5
    top5 = counter.most_common(5)
    if top5:
        top5_labels = [x[0] for x in top5]
        top5_values = [x[1] for x in top5]
    else:
        top5_labels = ["데이터 없음"]
        top5_values = [0]

    # Radar
    radar_map = {cat: 0 for cat in TECH_CATEGORY}
    for kw in all_keywords:
        for cat, lst in TECH_CATEGORY.items():
            if kw in lst:
                radar_map[cat] += 1

    radar_labels = list(radar_map.keys())
    radar_values = list(radar_map.values())

    # -----------------------------
    # 3) 추천 시스템용 텍스트 구성
    # -----------------------------
    texts = []
    for p in written_posts + viewed_posts:
        texts.append(p["board_title"] or "")
        texts.append(p["board_content"] or "")
    for c in written_comments + viewed_comments:
        texts.append(c["comment_answer_content"] or "")

    texts += written_tags + viewed_tags

    # -----------------------------
    # 4) 캐시된 벡터 불러오기
    # -----------------------------
    user_vector = interest_vector_dao.load_vector(user_id)

    # -----------------------------
    # 5) 없다면 생성 + DB 저장
    # -----------------------------
    if user_vector is None and texts:
        user_vector = build_user_vector(texts)
        if user_vector is not None:
            interest_vector_dao.save_vector(user_id, user_vector)

    # -----------------------------
    # 6) 추천 계산
    # -----------------------------
    recommended_articles = []
    if user_vector is not None:
        recommended_articles = recommend_articles(user_vector, top_n=5)

    # -----------------------------
    # 7) 렌더링
    # -----------------------------
    return render_template(
        "mypage-interest.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",

        top5_labels=top5_labels,
        top5_values=top5_values,
        radar_labels=radar_labels,
        radar_values=radar_values,

        recommended_articles=recommended_articles,

        current_bg=session["user"].get("background_img") or None
    )




# ------------------------------------------------------------
# 4. 아이템 관리 페이지 (DB 기반)
# ------------------------------------------------------------
@bp.route('/mypage-items')
def mypage_items():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]

    # 구매한 아이템만 가져오기 (정답)
    items = user_item_dao.get_user_items(user_id)

    # 장착 여부는 이미 포함됨 (ui.is_equipped)
    # items: [
    #   { item_no, is_equipped, item_name, item_type, item_price, item_img }
    # ]

    return render_template(
        'mypage-items.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        items=items
    )


# ------------------------------------------------------------
# 아이템 장착
# ------------------------------------------------------------
@bp.route("/api/mypage/item/equip", methods=["POST"])
def api_item_equip():
    user = get_logged_user()
    if not user:
        return jsonify({"success": False}), 403

    user_id = user["id"]
    item_no = request.json.get("item_no")

    # 아이템 정보 조회
    item = item_dao.get_item(item_no)
    if not item:
        return jsonify({"success": False, "msg": "아이템 없음"}), 400

    item_type = item["item_type"]
    item_img = item["item_img"]

    # 같은 타입 전체 해제 (함수명 수정!)
    user_item_dao.unequip_type(user_id, item_type)

    # 현재 아이템 장착
    user_item_dao.equip_item(user_id, item_no)

    # user 테이블 업데이트
    user_item_dao.update_user_profile(user_id, item_type, item_img)

    # 세션 즉시 반영
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


# ------------------------------------------------------------
# 아이템 해제
# ------------------------------------------------------------
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

    # 아이템 해제
    user_item_dao.unequip_item(user_id, item_no)

    # user 테이블 NULL 처리
    user_item_dao.update_user_profile(user_id, item_type, None)

    # 세션 갱신
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



# ------------------------------------------------------------
# 5. 내 정보 페이지
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
        current_bg = session["user"].get("background_img") or None

    )

# ------------------------------------------------------------
# 6. 닉네임/이메일 중복 확인
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
# 7. 프로필 수정
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
# 8. 팔로잉 / 팔로워
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
        current_bg = session["user"].get("background_img") or None

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
        current_bg = session["user"].get("background_img") or None
    )

# ------------------------------------------------------------
# 8-1. 팔로우 토글
# ------------------------------------------------------------
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
        return jsonify({"success": follow_dao.follow(user_id, target_id)})
    else:
        return jsonify({"success": follow_dao.unfollow(user_id, target_id)})

# ------------------------------------------------------------
# 9. 메시지 기능
# ------------------------------------------------------------



@bp.route("/mypage-message")
def mypage_message():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    rooms = message_dao.get_rooms_for_user(user_id)
    total_unread = sum(r["unread_count"] for r in rooms)

    return render_template(
        "mypage-message.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        rooms=rooms,
        user_id=user_id,
        total_unread=total_unread
    )

@bp.route("/mypage-message/room/<int:room_no>")
def mypage_message_room(room_no):
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]

    # 방 정보 불러오기
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
        "content": row["message_content"],
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

    # 방 생성 or 기존 방 불러오기
    if not room_no:
        room_no = message_dao.create_or_get_room(user_id, receiver_id)

    # DB 저장
    msg_no = message_dao.send_message(room_no, user_id, receiver_id, content)
    receiver_info = user_dao.get_user_by_id(receiver_id)

    # 🔥 WebSocket 실시간 메시지 전송
    send_dm_message(
        receiver_id,
        {
            "room_no": room_no,
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "content": content,
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    )

    return jsonify({
        "success": True,
        "room_no": room_no,
        "message_no": msg_no,
        "sender_id": user_id,
        "receiver_nick": receiver_info["nick"],
        "content": content,
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

# ------------------------------------------------------------
# 10. 포인트
# ------------------------------------------------------------
@bp.route("/mypage-point")
def mypage_point():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    order = request.args.get("order", "latest")

    point_list = point_dao.get_point_history(user_id, order=order)
    total_point = point_dao.get_total_point(user_id)

    return render_template(
        "mypage-point.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg = session["user"].get("background_img") or None,
        point_list=point_list,
        total_point=total_point
    )

# ------------------------------------------------------------
# 11. 알림
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
        current_bg = session["user"].get("background_img") or None,
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

# ------------------------------------------------------------
# 12. 회원 탈퇴
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
        current_bg = session["user"].get("background_img") or None
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

    # 1) 유저 정보 확인
    user_row = user_dao.check_login(user_id, password)
    if not user_row:
        return jsonify({"success": False, "msg": "아이디 또는 비밀번호 불일치"}), 400

    # 2) 탈퇴 처리
    withdraw_dao.withdraw_user(user_id)

    # 3) 세션 삭제
    session.pop("user", None)

    return jsonify({"success": True})


# ------------------------------------------------------------
# 13. 기타
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

    # 1) 중복 구매 방지
    if user_item_dao.has_item(user_id, item_no):
        return jsonify(success=False, msg="이미 보유한 아이템입니다."), 400

    # 2) 포인트 체크
    current_point = point_dao.get_total_point(user_id)
    if current_point < price:
        return jsonify(success=False, msg="포인트 부족"), 400

    # 3) 포인트 차감
    point_dao.use_point(user_id, price, f"아이템 구매: {item['item_name']}")

    # 4) 아이템 지급
    user_item_dao.add_item(user_id, item_no)

    # 🔥 5) 세션에 최신 포인트 반영
    session["user"]["user_current_point"] = current_point - price
    session.modified = True

    # 🔥 6) JS에서 즉시 업데이트할 수 있도록 new_point 반환
    return jsonify(
        success=True,
        new_point=session["user"]["user_current_point"]
    )

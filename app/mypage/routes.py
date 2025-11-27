from flask import Blueprint, render_template, request, jsonify, session, redirect
from config import SIDEBAR_CONFIG
from flask import current_app
from datetime import datetime
from app.mypage.events import send_dm_message

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
# DAO 객체
user_dao = UserDao(lambda: current_app.get_db_connection)
alert_dao = AlertDao(lambda:current_app.get_db_connection)
follow_dao = FollowDao(lambda:current_app.get_db_connection)
message_dao = MessageDao(lambda:current_app.get_db_connection)
posts_dao = MyPagePostsDao(lambda:current_app.get_db_connection)
point_dao = PointDao(lambda:current_app.get_db_connection)
user_info_dao = UserInfoDao(lambda:current_app.get_db_connection)
withdraw_dao = WithdrawDao(lambda:current_app.get_db_connection)
item_dao = ItemDao(lambda:current_app.get_db_connection)
user_item_dao = UserItemDao(lambda:current_app.get_db_connection)
view_log_dao = ViewLogDao(lambda:current_app.get_db_connection)
interest_dao = InterestDao(lambda:current_app.get_db_connection)
import re
from collections import Counter

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

# ------------------------------------------------------------
# 1. 마이페이지 - 게시글 목록
# ------------------------------------------------------------
@bp.route("/mypage-posts")
def mypage_posts():
    user = get_logged_user()
    if not user:
        return require_login_js()

    user_id = user["id"]
    sort = request.args.get("top", "최신순")

    posts = posts_dao.get_my_posts_full(user_id)

    if sort == "팔로우순":
        posts = follow_dao.get_following_posts(user_id)

    if sort == "최신순":
        posts.sort(key=lambda x: x["board_no"], reverse=True)
    elif sort == "조회순":
        posts.sort(key=lambda x: x.get("hit", 0), reverse=True)
    elif sort == "추천순":
        posts.sort(key=lambda x: x.get("board_like", 0), reverse=True)

    return render_template(
        "mypage-posts.html",
        posts=posts,
        show_notice_buttons=True,
        notice_buttons={
            "top_buttons": ["최신순", "조회순", "추천순"],
            "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
        },
        show_writeBtn=True,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=session["user"].get("background_img") or None,
        top_filter=sort
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
# 관심도 분석 라우트
# ------------------------------------------------------------
@bp.route("/mypage-interest")
def mypage_interest():
    user = session.get("user")
    if not user:
        return """
            <script>
                alert('로그인이 필요합니다.');
                window.location.href='/';
            </script>
        """

    user_id = user["id"]

    # 1. 태그 기반 데이터 ---------------------------------------
    tag_data = interest_dao.get_all_tags(user_id)
    written_tags = tag_data["written_tags"]
    viewed_tags = tag_data["viewed_tags"]

    # 태그는 기술명과 1:1 대응되므로 그대로 키워드로 사용
    tag_keywords = written_tags + viewed_tags

    # 2. 텍스트 기반 데이터 -------------------------------------
    text_sources = interest_dao.get_all_text_sources(user_id)

    written_posts = text_sources["written_posts"]
    viewed_posts = text_sources["viewed_posts"]
    written_comments = text_sources["written_comments"]
    viewed_comments = text_sources["viewed_comments"]

    text_keywords = []

    # (1) 게시글 제목/내용
    for p in written_posts + viewed_posts:
        text_keywords += extract_keywords(p["board_title"])
        text_keywords += extract_keywords(p["board_content"])

    # (2) 댓글/답변 내용
    for c in written_comments + viewed_comments:
        text_keywords += extract_keywords(c["comment_answer_content"])

    # 3. 전체 키워드 통합 ---------------------------------------
    all_keywords = tag_keywords + text_keywords

    counter = Counter(all_keywords)

    # 4. TOP5 기술 (Bar Chart)
    top5 = counter.most_common(5)
    top5_labels = [x[0] for x in top5]
    top5_values = [x[1] for x in top5]

    # 만약 데이터가 없을 경우 예외 처리
    if len(top5_labels) == 0:
        top5_labels = ["데이터 없음"]
        top5_values = [0]

    # 5. Radar Chart (기술 분야별)
    radar_map = {cat: 0 for cat in TECH_CATEGORY}

    for kw in all_keywords:
        for cat, lst in TECH_CATEGORY.items():
            if kw in lst:
                radar_map[cat] += 1

    radar_labels = list(radar_map.keys())
    radar_values = list(radar_map.values())

    # ------------------------------------------------------------
    # 템플릿 렌더링
    # ------------------------------------------------------------
    return render_template(
        "mypage-interest.html",
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",

        top5_labels=top5_labels,
        top5_values=top5_values,
        radar_labels=radar_labels,
        radar_values=radar_values,

        current_bg = session["user"].get("background_img") or None
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

    # 전체 아이템
    items = item_dao.get_all_items()

    # 유저가 가진 아이템
    user_items = user_item_dao.get_user_items(user_id)
    owned = {u["item_no"]: u for u in user_items}

    # 장착 여부 추가
    for item in items:
        item["is_equipped"] = (
            owned.get(item["item_no"], {}).get("is_equipped") == 1
        )

    return render_template(
        'mypage-items.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg = session["user"].get("background_img") or None,

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
@bp.route("/minigame")
def minigame():
    return render_template("minigame.html")

@bp.route("/pointstore")
def pointstore():
    return render_template(
        "pointstore.html",
        show_notice_buttons=True,
        notice_buttons={
            "top_buttons": ["최신순", "조회순", "검색순"],
            "feed_buttons": ["전체", "상품응모", "당첨자발표"]
        },
        show_writeBtn=True,
        sidebar=SIDEBAR_CONFIG["pointstore"],
        active="pointstore"
    )

@bp.route("/pointshop")
def pointshop():
    return render_template(
        "pointshop.html",
        show_notice_buttons=True,
        notice_buttons={
            "top_buttons": ["최신순", "구매순", "낮은가격순", "높은가격순"],
            "feed_buttons": ["전체", "아이콘", "배경이미지"]
        },
        show_writeBtn=True,
        sidebar=SIDEBAR_CONFIG["pointstore"],
        active="pointstore"
    )

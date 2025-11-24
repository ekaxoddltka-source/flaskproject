from flask import Blueprint, render_template, request, jsonify, session, redirect
from config import SIDEBAR_CONFIG
from app.account.routes import get_db_connection


# DAO
from app.mypage.dao.user_dao import UserDao
from app.mypage.dao.alert_dao import AlertDao
from app.mypage.dao.follow_dao import FollowDao
from app.mypage.dao.message_dao import MessageDao
from app.mypage.dao.mypage_posts_dao import MyPagePostsDao
from app.mypage.dao.point_dao import PointDao
from app.mypage.dao.user_info_dao import UserInfoDao
from app.mypage.dao.withdraw_dao import WithdrawDao

# DAO 초기화
user_dao = UserDao(get_db_connection)
alert_dao = AlertDao(get_db_connection)
follow_dao = FollowDao(get_db_connection)
message_dao = MessageDao(get_db_connection)
posts_dao = MyPagePostsDao(get_db_connection)
point_dao = PointDao(get_db_connection)
user_info_dao = UserInfoDao(get_db_connection)
withdraw_dao = WithdrawDao(get_db_connection)

bp = Blueprint(
    'mypage',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/mypage/static'
)


# ============================================================
# 공통: 로그인 체크 함수
# ============================================================
def get_logged_user():
    user = session.get("user")
    if not user:
        return None
    return user


# ============================================================
# 마이페이지 - 내 글
# ============================================================
@bp.route('/mypage-posts')
def mypage_posts():
    user = get_logged_user()
    if not user:
        return redirect("/")       # GET 허용 URL

    user_id = user["id"]

    current_bg = "backgrounds/m.png"
    sort = request.args.get("top", "최신순")

    posts = posts_dao.get_my_posts_full(user_id)

    if sort == "팔로우순":
        posts = follow_dao.get_following_posts(user_id)

    if sort == "최신순":
        posts.sort(key=lambda x: x["board_no"], reverse=True)
    elif sort == "조회순" and posts and "hit" in posts[0]:
        posts.sort(key=lambda x: x["hit"], reverse=True)
    elif sort == "추천순" and posts and "board_like" in posts[0]:
        posts.sort(key=lambda x: x["board_like"], reverse=True)

    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색순"],
        "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }

    return render_template(
        'mypage-posts.html',
        posts=posts,
        show_notice_buttons=True,
        notice_buttons=notice_buttons,
        show_writeBtn=True,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg=current_bg,
        top_filter=sort
    )


# ============================================================
# 게시글 상세 API
# ============================================================
@bp.route('/api/mypage/post/<int:board_no>')
def api_mypage_post_detail(board_no):
    return {
        "post": posts_dao.get_post_detail(board_no),
        "files": posts_dao.get_files_by_board(board_no),
        "tags": posts_dao.get_tags_by_board(board_no),
        "comments": posts_dao.get_comments_by_board(board_no)
    }


# ============================================================
# 추천 API (세션 기반 1인 1투표)
# ============================================================
@bp.route('/api/post/like', methods=['POST'])
def api_post_like():
    data = request.get_json()
    board_no = str(data.get("board_no"))

    user = get_logged_user()
    if not user:
        return jsonify({"success": False, "msg": "로그인 필요"}), 403

    if "votes" not in session:
        session["votes"] = {}

    votes = session["votes"]
    old = votes.get(board_no, 0)

    if old == 1:
        posts_dao.update_like(board_no, -1)
        votes[board_no] = 0
    elif old == -1:
        posts_dao.update_dislike(board_no, -1)
        posts_dao.update_like(board_no, +1)
        votes[board_no] = 1
    else:
        posts_dao.update_like(board_no, +1)
        votes[board_no] = 1

    session.modified = True
    status = posts_dao.get_like_dislike(board_no)

    return jsonify({
        "success": True,
        "board_like": status["board_like"],
        "board_dislike": status["board_dislike"],
        "vote": votes[board_no]
    })


# ============================================================
# 비추천 API
# ============================================================
@bp.route('/api/post/dislike', methods=['POST'])
def api_post_dislike():
    data = request.get_json()
    board_no = str(data.get("board_no"))

    user = get_logged_user()
    if not user:
        return jsonify({"success": False, "msg": "로그인 필요"}), 403

    if "votes" not in session:
        session["votes"] = {}

    votes = session["votes"]
    old = votes.get(board_no, 0)

    if old == -1:
        posts_dao.update_dislike(board_no, -1)
        votes[board_no] = 0
    elif old == 1:
        posts_dao.update_like(board_no, -1)
        posts_dao.update_dislike(board_no, +1)
        votes[board_no] = -1
    else:
        posts_dao.update_dislike(board_no, +1)
        votes[board_no] = -1

    session.modified = True
    status = posts_dao.get_like_dislike(board_no)

    return jsonify({
        "success": True,
        "board_like": status["board_like"],
        "board_dislike": status["board_dislike"],
        "vote": votes[board_no]
    })


@bp.route('/mypage-interest')
def mypage_interest():
    user = get_logged_user()
    if not user:
        return redirect("/")

    return render_template(
        'mypage-interest.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        top5_labels=["Python", "React", "AI", "SQL", "Docker"],
        top5_values=[55, 40, 30, 22, 15],
        radar_labels=["Frontend", "Backend", "AI/ML", "DevOps", "CS 기본"],
        radar_values=[65, 45, 88, 40, 55],
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-items')
def mypage_item():
    user = get_logged_user()
    if not user:
        return redirect("/")

    items = [
        {"id": 1, "name": "고양이 아이콘", "desc": "프로필 아이콘",
         "type": "icon", "img": "icons/cat.png", "equipped": True},
        {"id": 2, "name": "아이돌 배경", "desc": "배경 이미지",
         "type": "bg", "img": "backgrounds/m.png", "equipped": True}
    ]

    return render_template(
        'mypage-items.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        items=items,
        current_bg="backgrounds/m.png"
    )

@bp.route('/mypage-info')
def mypage_info():
    user = get_logged_user()
    if not user:
        return redirect("/login")

    user_id = user["id"]

    # DB에서 최신 유저 정보 가져오기
    user_info = user_info_dao.get_user_by_id(user_id)

    return render_template(
        'mypage-info.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        user=user_info,   # 템플릿에서 사용 가능
        current_bg="backgrounds/m.png"
    )

@bp.route("/api/mypage/check-nickname", methods=["POST"])
def api_check_nickname():
    data = request.get_json()
    nickname = (data.get("nickname") or "").strip()

    if not nickname:
        return jsonify({"success": False, "msg": "닉네임이 없습니다."}), 400

    exists = user_info_dao.check_nickname_exists(nickname)
    return jsonify({"success": True, "exists": exists})

@bp.route("/api/mypage/check-email", methods=["POST"])
def api_check_email():
    data = request.get_json()
    email = (data.get("email") or "").strip()

    if not email:
        return jsonify({"success": False, "msg": "이메일이 없습니다."}), 400

    exists = user_info_dao.check_email_exists(email)
    return jsonify({"success": True, "exists": exists})

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

    if not new_nick or not new_email:
        return jsonify({"success": False, "msg": "닉네임과 이메일은 필수입니다."}), 400

    # 기존 정보
    current = user_info_dao.get_user_by_id(user_id)

    # 닉네임 중복체크
    if new_nick != current["nick"]:
        if user_info_dao.check_nickname_exists(new_nick):
            return jsonify({"success": False, "msg": "이미 사용 중인 닉네임입니다."}), 400

    # 이메일 중복체크
    if new_email != current["email"]:
        if user_info_dao.check_email_exists(new_email):
            return jsonify({"success": False, "msg": "이미 사용 중인 이메일입니다."}), 400

    # 비밀번호 변경
    if new_password:
        user_info_dao.update_password(user_id, new_password)

    # 닉네임/이메일 업데이트
    user_info_dao.update_user_info(user_id, new_nick, new_email)

    # 세션 갱신
    session_user = session.get("user")
    if session_user:
        session_user["nick"] = new_nick
        session_user["email"] = new_email
        session["user"] = session_user
        session.modified = True

    return jsonify({"success": True, "msg": "회원 정보가 수정되었습니다."})


@bp.route('/mypage-following')
def mypage_following():
    user = get_logged_user()
    if not user:
        return redirect("/")

    user_id = user["id"]
    following = follow_dao.get_following_list(user_id)

    for f in following:
        f["is_following"] = True

    return render_template(
        'mypage-following.html',
        following_list=following,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-follower')
def mypage_follower():
    user = get_logged_user()
    if not user:
        return redirect("/")

    user_id = user["id"]
    followers = follow_dao.get_follower_list(user_id)

    for f in followers:
        f["is_following"] = follow_dao.is_following(user_id, f["user_id"])

    return render_template(
        'mypage-follower.html',
        follower_list=followers,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-message')
def mypage_message():
    user = get_logged_user()
    if not user:
        return redirect("/")

    return render_template(
        'mypage-message.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-point')
def mypage_point():
    user = get_logged_user()
    if not user:
        return redirect("/")

    return render_template(
        'mypage-point.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-alert')
def mypage_alert():
    user = get_logged_user()
    if not user:
        return redirect("/")

    return render_template(
        'mypage-alert.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-withdraw')
def mypage_withdraw():
    user = get_logged_user()
    if not user:
        return redirect("/")

    return render_template(
        'mypage-withdraw.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/minigame')
def minigame():
    return render_template('minigame.html')


@bp.route('/pointstore')
def pointstore():
    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "검색순"],
        "feed_buttons": ["전체", "상품응모", "당첨자발표"]
    }
    return render_template(
        'pointstore.html',
        show_notice_buttons=True,
        notice_buttons=notice_buttons,
        show_writeBtn=True,
        sidebar=SIDEBAR_CONFIG["pointstore"],
        active="pointstore"
    )


@bp.route('/pointshop')
def pointshop():
    notice_buttons = {
        "top_buttons": ["최신순", "구매순", "낮은가격순", "높은가격순"],
        "feed_buttons": ["전체", "아이콘", "배경이미지"]
    }
    return render_template(
        'pointshop.html',
        show_notice_buttons=True,
        notice_buttons=notice_buttons,
        show_writeBtn=True,
        sidebar=SIDEBAR_CONFIG["pointstore"],
        active="pointstore"
    )

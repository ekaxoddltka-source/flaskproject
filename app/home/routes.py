# app/home/routes.py
from flask import Blueprint, render_template, jsonify, request, session
from datetime import datetime
from config import SIDEBAR_CONFIG
import pymysql
from app.account.routes import get_db_connection

bp = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)

@bp.route("/api/latest_notice")
def latest_notice():
    conn = get_db_connection()
    cur = conn.cursor()

    sql = "SELECT board_title FROM board where board_category = 4 ORDER BY board_created_at DESC LIMIT 1"
    cur.execute(sql)
    row = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({"title": row["board_title"] if row else ""})

@bp.route('/')
def home():
    # GET 파라미터 읽기
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')  

    # DB 연결
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 기본 SQL
    sql = """
        SELECT 
            board.*, 
            comment_answer.*, 
            user.nick AS writer_nick,
            user.id AS writer_id,
            comment_user.nick AS commenter_nick,
            comment_user.id AS commenter_id,
            file.*,
            tag.tag_name
        FROM board
        LEFT JOIN user ON board.id = user.id
        LEFT JOIN file ON board.board_no = file.board_no
        LEFT JOIN tag_board ON tag_board.board_no = board.board_no
        LEFT JOIN tag ON tag.tag_no = tag_board.tag_no
        LEFT JOIN comment_answer ON board.board_no = comment_answer.board_no
        LEFT JOIN user AS comment_user ON comment_answer.id = comment_user.id
        WHERE board.board_deleted = 0
    """

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        sql += f" AND board_category = {category_map[feed_filter]}"

    # top 정렬
    if top_filter == "조회순":
        sql += " ORDER BY board.hit DESC"
    elif top_filter == "추천순":
        sql += " ORDER BY board.board_like DESC"
    elif top_filter == "팔로우순":
        sql += " ORDER BY follow_count DESC"  # follow_count 컬럼 필요
    elif top_filter == "검색순":
        sql += " ORDER BY search_score DESC"  # search_score 컬럼 필요
    else:
        sql += " ORDER BY board.board_no DESC"  # 최신순 기본

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    # resultMap 재현
    board_map = {}
    for row in rows:
        boardNo = row["board_no"]
        if boardNo not in board_map:
            board_map[boardNo] = {
                "boardNo": row["board_no"],
                "id": row["writer_id"],
                "nick": row["writer_nick"],
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
        post = board_map[boardNo]
        if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
            post["files"].append({
                "fileNo": row["file_no"],
                "logicalFileName": row["logical_file_name"],
                "physicalFileName": row["physical_file_name"],
                "fileSize": row["file_size"],
                "fileExt": row["file_ext"]
            })
        if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
            post["tags"].append({"tagName": row["tag_name"]})
        if row["comment_answer_no"] is not None:
            if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                post["comments"].append({
                    "commentAnswerNo": row["comment_answer_no"],
                    "boardNo": row["board_no"],
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

    boardList = list(board_map.values())

    # 버튼 배열
    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색순"],
        "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }

    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')

    login_user_id = session.get("user", {}).get("id")

    return render_template(
        'home.html',
        boardList=boardList,
        show_writeBtn=True,
        show_notice_buttons=True,
        notice_buttons=notice_buttons,
        active="chat",
        sidebar=SIDEBAR_CONFIG["default"],
        top_filter=top_filter,       
        feed_filter=feed_filter,
        login_user_id=login_user_id      
    )

@bp.route('/write')
def write():
    return render_template(
    'write.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/terms')
def terms():
        # GET 파라미터 읽기
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')  

    # DB 연결
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 기본 SQL
    sql = """
        SELECT 
            board.*, 
            comment_answer.*, 
            user.nick AS writer_nick,
            user.id AS writer_id,
            comment_user.nick AS commenter_nick,
            comment_user.id AS commenter_id,
            file.*,
            tag.tag_name
        FROM board
        LEFT JOIN user ON board.id = user.id
        LEFT JOIN file ON board.board_no = file.board_no
        LEFT JOIN tag_board ON tag_board.board_no = board.board_no
        LEFT JOIN tag ON tag.tag_no = tag_board.tag_no
        LEFT JOIN comment_answer ON board.board_no = comment_answer.board_no
        LEFT JOIN user AS comment_user ON comment_answer.id = comment_user.id
        WHERE board.board_deleted = 0 and board.board_category = 5
    """

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        sql += f" AND board_category = {category_map[feed_filter]}"

    # top 정렬
    if top_filter == "조회순":
        sql += " ORDER BY board.hit DESC"
    elif top_filter == "추천순":
        sql += " ORDER BY board.board_like DESC"
    elif top_filter == "팔로우순":
        sql += " ORDER BY follow_count DESC"  # follow_count 컬럼 필요
    elif top_filter == "검색순":
        sql += " ORDER BY search_score DESC"  # search_score 컬럼 필요
    else:
        sql += " ORDER BY board.board_no DESC"  # 최신순 기본

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    # resultMap 재현
    board_map = {}
    for row in rows:
        boardNo = row["board_no"]
        if boardNo not in board_map:
            board_map[boardNo] = {
                "boardNo": row["board_no"],
                "id": row["writer_id"],
                "nick": row["writer_nick"],
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
        post = board_map[boardNo]
        if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
            post["files"].append({
                "fileNo": row["file_no"],
                "logicalFileName": row["logical_file_name"],
                "physicalFileName": row["physical_file_name"],
                "fileSize": row["file_size"],
                "fileExt": row["file_ext"]
            })
        if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
            post["tags"].append({"tagName": row["tag_name"]})
        if row["comment_answer_no"] is not None:
            if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                post["comments"].append({
                    "commentAnswerNo": row["comment_answer_no"],
                    "boardNo": row["board_no"],
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

    boardList = list(board_map.values())

    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색순"],
    "feed_buttons": ["전체"]
    }

    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')

    login_user_id = session.get("user", {}).get("id")

    return render_template(
    'terms.html',
    boardList=boardList,
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["info"],
    active="info",
    login_user_id=login_user_id 
)

@bp.route('/info')
def info():
        # GET 파라미터 읽기
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')  

    # DB 연결
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 기본 SQL
    sql = """
        SELECT 
            board.*, 
            comment_answer.*, 
            user.nick AS writer_nick,
            user.id AS writer_id,
            comment_user.nick AS commenter_nick,
            comment_user.id AS commenter_id,
            file.*,
            tag.tag_name
        FROM board
        LEFT JOIN user ON board.id = user.id
        LEFT JOIN file ON board.board_no = file.board_no
        LEFT JOIN tag_board ON tag_board.board_no = board.board_no
        LEFT JOIN tag ON tag.tag_no = tag_board.tag_no
        LEFT JOIN comment_answer ON board.board_no = comment_answer.board_no
        LEFT JOIN user AS comment_user ON comment_answer.id = comment_user.id
        WHERE board.board_deleted = 0 and board.board_category = 4
    """

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        sql += f" AND board_category = {category_map[feed_filter]}"

    # top 정렬
    if top_filter == "조회순":
        sql += " ORDER BY board.hit DESC"
    elif top_filter == "추천순":
        sql += " ORDER BY board.board_like DESC"
    elif top_filter == "팔로우순":
        sql += " ORDER BY follow_count DESC"  # follow_count 컬럼 필요
    elif top_filter == "검색순":
        sql += " ORDER BY search_score DESC"  # search_score 컬럼 필요
    else:
        sql += " ORDER BY board.board_no DESC"  # 최신순 기본

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    # resultMap 재현
    board_map = {}
    for row in rows:
        boardNo = row["board_no"]
        if boardNo not in board_map:
            board_map[boardNo] = {
                "boardNo": row["board_no"],
                "id": row["writer_id"],
                "nick": row["writer_nick"],
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
        post = board_map[boardNo]
        if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
            post["files"].append({
                "fileNo": row["file_no"],
                "logicalFileName": row["logical_file_name"],
                "physicalFileName": row["physical_file_name"],
                "fileSize": row["file_size"],
                "fileExt": row["file_ext"]
            })
        if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
            post["tags"].append({"tagName": row["tag_name"]})
        if row["comment_answer_no"] is not None:
            if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                post["comments"].append({
                    "commentAnswerNo": row["comment_answer_no"],
                    "boardNo": row["board_no"],
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

    boardList = list(board_map.values())

    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색순"],
    "feed_buttons": ["전체"]
    }

    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')

    login_user_id = session.get("user", {}).get("id")

    return render_template(
    'info.html',
    boardList=boardList,
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["info"],
    active="info",
    login_user_id=login_user_id 
)

@bp.route('/privacy')
def privacy():
        # GET 파라미터 읽기
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')  

    # DB 연결
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 기본 SQL
    sql = """
        SELECT 
            board.*, 
            comment_answer.*, 
            user.nick AS writer_nick,
            user.id AS writer_id,
            comment_user.nick AS commenter_nick,
            comment_user.id AS commenter_id,
            file.*,
            tag.tag_name
        FROM board
        LEFT JOIN user ON board.id = user.id
        LEFT JOIN file ON board.board_no = file.board_no
        LEFT JOIN tag_board ON tag_board.board_no = board.board_no
        LEFT JOIN tag ON tag.tag_no = tag_board.tag_no
        LEFT JOIN comment_answer ON board.board_no = comment_answer.board_no
        LEFT JOIN user AS comment_user ON comment_answer.id = comment_user.id
        WHERE board.board_deleted = 0 and board.board_category = 6
    """

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        sql += f" AND board_category = {category_map[feed_filter]}"

    # top 정렬
    if top_filter == "조회순":
        sql += " ORDER BY board.hit DESC"
    elif top_filter == "추천순":
        sql += " ORDER BY board.board_like DESC"
    elif top_filter == "팔로우순":
        sql += " ORDER BY follow_count DESC"  # follow_count 컬럼 필요
    elif top_filter == "검색순":
        sql += " ORDER BY search_score DESC"  # search_score 컬럼 필요
    else:
        sql += " ORDER BY board.board_no DESC"  # 최신순 기본

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    # resultMap 재현
    board_map = {}
    for row in rows:
        boardNo = row["board_no"]
        if boardNo not in board_map:
            board_map[boardNo] = {
                "boardNo": row["board_no"],
                "id": row["writer_id"],
                "nick": row["writer_nick"],
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
        post = board_map[boardNo]
        if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
            post["files"].append({
                "fileNo": row["file_no"],
                "logicalFileName": row["logical_file_name"],
                "physicalFileName": row["physical_file_name"],
                "fileSize": row["file_size"],
                "fileExt": row["file_ext"]
            })
        if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
            post["tags"].append({"tagName": row["tag_name"]})
        if row["comment_answer_no"] is not None:
            if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                post["comments"].append({
                    "commentAnswerNo": row["comment_answer_no"],
                    "boardNo": row["board_no"],
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

    boardList = list(board_map.values())

    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색순"],
    "feed_buttons": ["전체"]
    }

    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')

    login_user_id = session.get("user", {}).get("id")

    return render_template(
    'privacy.html',
    boardList=boardList,
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["info"],
    active="info",
    login_user_id=login_user_id
)

@bp.route("/report", methods=["POST"])
def report_post():
    if "user" not in session:
        return jsonify({"success": False, "msg": "로그인이 필요합니다."})

    data = request.get_json()
    board_no = data.get("board_no")
    report_category = data.get("report_category")
    report_content = data.get("report_content")
    report_user_id = session["user"]["id"]
    now = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1. 중복 신고 체크
        sql_check = """
            SELECT COUNT(*) AS cnt 
            FROM report
            WHERE board_no=%s AND report_user_id=%s
        """
        cursor.execute(sql_check, (board_no, report_user_id))
        count = cursor.fetchone()["cnt"]

        if count > 0:
            return jsonify({"success": False, "msg": "이미 신고한 게시글입니다."})

        # 2. 신고 등록
        sql_insert = """
            INSERT INTO report
            (report_user_id, report_category, report_content, board_no, reported_at, report_status, report_updated_at)
            VALUES (%s, %s, %s, %s, %s, 1, %s)
        """
        cursor.execute(sql_insert, (report_user_id, report_category, report_content, board_no, now, now))
        conn.commit()

        return jsonify({"success": True, "msg": "신고가 접수되었습니다."})

    except Exception as e:
        conn.rollback()
        print("Report insert error:", e)
        return jsonify({"success": False, "msg": str(e)})

    finally:
        cursor.close()
        conn.close()

@bp.route("/post/delete", methods=["POST"])
def delete_post():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    data = request.get_json()
    board_no = data.get("id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE board SET board_deleted = 1 WHERE board_no = %s",
        (board_no,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)

@bp.route("/comment/delete", methods=["POST"])
def delete_comment():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    # form-urlencoded로 전달된 데이터 받기
    data = request.get_json()
    comment_id = data.get("id")
    if not comment_id:
        return jsonify(success=False, msg="댓글 ID가 없습니다.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM comment_answer WHERE comment_answer_no = %s",
        (comment_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)


@bp.route("/answer/delete", methods=["POST"])
def delete_answer():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    # form-urlencoded로 전달된 데이터 받기
    data = request.get_json()   
    answer_id = data.get("id")
    if not answer_id:
        return jsonify(success=False, msg="답변 ID가 없습니다.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM comment_answer WHERE comment_answer_no = %s",
        (answer_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)


@bp.route("/comment/update", methods=["POST"])
def update_comment():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    comment_id = request.form.get("id")
    content = request.form.get("content", "").strip()

    if not comment_id or not content:
        return jsonify(success=False, msg="필수 정보 누락")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE comment_answer SET comment_answer_content = %s, comment_answer_updated_at = NOW() WHERE comment_answer_no = %s",
        (content, comment_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)

@bp.route("/answer/update", methods=["POST"])
def update_answer():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    answer_id = request.form.get("id")
    content = request.form.get("content", "").strip()

    if not answer_id or not content:
        return jsonify(success=False, msg="필수 정보 누락")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE comment_answer SET comment_answer_content = %s, comment_answer_updated_at = NOW() WHERE comment_answer_no = %s",
        (content, answer_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(success=True)

@bp.route("/addComment", methods=["POST"])
def add_comment():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    data = request.get_json()
    board_no = data.get("boardNo")
    content = data.get("content", "").strip()

    if not board_no or not content:
        return jsonify(success=False, msg="필수 정보 누락")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO comment_answer 
            (board_no, id, comment_answer_content, comment_answer_type, comment_answer_at)
            VALUES (%s, %s, %s, 1, NOW())
        """
        cursor.execute(sql, (board_no, session["user"]["id"], content))
        conn.commit()
        comment_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, msg=str(e))
    finally:
        cursor.close()
        conn.close()

    return jsonify(success=True, id=comment_id)

@bp.route("/addAnswer", methods=["POST"])
def add_answer():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    data = request.get_json()
    board_no = data.get("boardNo")
    content = data.get("content", "").strip()

    if not board_no or not content:
        return jsonify(success=False, msg="필수 정보 누락")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO comment_answer
            (board_no, id, comment_answer_content, comment_answer_type, comment_answer_at)
            VALUES (%s, %s, %s, 2, NOW())
        """
        cursor.execute(sql, (board_no, session["user"]["id"], content))
        conn.commit()
        answer_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, msg=str(e))
    finally:
        cursor.close()
        conn.close()

    return jsonify(success=True, id=answer_id, author=session["user"]["nick"])

@bp.route("/answer/accept", methods=["POST"])
def accept_answer():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")
    
    data = request.get_json()
    answer_id = data.get("answerId")
    if not answer_id:
        return jsonify(success=False, msg="답변 ID가 없습니다.")
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 1. 답변 정보 가져오기
        cursor.execute("SELECT board_no, id FROM comment_answer WHERE comment_answer_no=%s", (answer_id,))
        answer = cursor.fetchone()
        if not answer:
            return jsonify(success=False, msg="답변이 존재하지 않습니다.")
        
        board_no = answer["board_no"]
        
        # 2. 게시글 작성자 확인
        cursor.execute("SELECT id FROM board WHERE board_no=%s", (board_no,))
        board = cursor.fetchone()
        if not board:
            return jsonify(success=False, msg="게시글이 존재하지 않습니다.")
        
        if board["id"] != session["user"]["id"]:
            return jsonify(success=False, msg="게시글 작성자만 답변을 채택할 수 있습니다.")
        
        # 3. 기존 채택 답변 해제
        cursor.execute(
            "UPDATE comment_answer SET answer_accepted=0 WHERE board_no=%s AND answer_accepted=1",
            (board_no,)
        )
        
        # 4. 선택 답변 채택
        cursor.execute(
            "UPDATE comment_answer SET answer_accepted=1 WHERE comment_answer_no=%s",
            (answer_id,)
        )
        conn.commit()
        return jsonify(success=True, msg="답변이 채택되었습니다.", answerId=answer_id)
    
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, msg=str(e))
    
    finally:
        cursor.close()
        conn.close()

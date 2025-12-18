# app/home/routes.py
from flask import Blueprint, render_template, jsonify, request, session, send_from_directory, abort, redirect, flash, current_app
from datetime import datetime
from config import SIDEBAR_CONFIG
import pymysql
import os
from urllib.parse import unquote
from google import genai
from google.genai import types
from app.filters.slang_filter import mask_slang

bp = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)

# Gemini 클라이언트 초기화
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    print(f"Gemini Client 초기화 오류: {e}")
    client = None

@bp.route("/api/me")
def api_me():
    user_id = session.get("user_id")
    nick = session.get("nick")
    if user_id and nick:
        return jsonify({"id": user_id, "nick": nick})
    else:
        return jsonify({"id": None, "nick": None})

@bp.route("/api/latest_notice")
def latest_notice():
    conn = current_app.get_db_connection()
    cur = conn.cursor()

    sql = "SELECT board_title FROM board where board_category = 4 and board_deleted = 0 ORDER BY board_created_at DESC LIMIT 1"
    cur.execute(sql)
    row = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({"title": row["board_title"] if row else ""})

@bp.route('/load_more_posts')
def load_more_posts():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()
    tag_name = request.args.get('tag_name')
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1️⃣ 기본 필터 + 파라미터
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0"
        params_filter = []

        # feed 필터
        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
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
        else:
            board_filter_sql += " AND board_category IN (1,2,3)"

        # 팔로우 필터
        login_user_id = session.get("user", {}).get("id")
        if top_filter == "팔로우순" and login_user_id:
            board_filter_sql += """
                AND id IN (
                    SELECT following_id
                    FROM follow
                    WHERE followed_id = %s
                )
            """
            params_filter.append(login_user_id)

        # 검색 필터
        if search_type and search_keyword:
            if search_type == "board_title":
                board_filter_sql += " AND board_title LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "board_content":
                board_filter_sql += " AND board_content LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "id":
                board_filter_sql += " AND id IN (SELECT id FROM user WHERE nick LIKE %s)"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "tag":
                board_filter_sql += """
                    AND board_no IN (
                        SELECT tb.board_no
                        FROM tag_board tb
                        JOIN tag t ON tb.tag_no = t.tag_no
                        WHERE t.tag_name LIKE %s
                    )
                """
                params_filter.append(f"%{search_keyword}%")

        # 태그 필터
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

        # 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        else:  # 최신순 & 팔로우순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 2️⃣ SQL 실행 (LIMIT/OFFSET 제거!)
        cursor.execute(f"{board_filter_sql} {order_clause}", tuple(params_filter))
        all_board_rows = cursor.fetchall()
        all_board_nos = [r['board_no'] for r in all_board_rows]

        # 3️⃣ Python에서 페이징 적용
        board_nos = all_board_nos[offset:offset + per_page]

        if not board_nos:
            return jsonify([])

        # 4️⃣ 상세 조회 (기존 로직 유지)
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

        # 5️⃣ 게시글 조립
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

        # 6️⃣ Python에서 정렬 유지
        boardList = [board_map[b] for b in board_nos if b in board_map]

        return jsonify(boardList)

    finally:
        cursor.close()
        conn.close()

@bp.route('/')
def home():
    page = 1
    per_page = 10
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1️⃣ 기본 필터
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND board_category IN (1,2,3)"
        params_filter = []

        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        login_user_id = session.get("user", {}).get("id")

        # 2️⃣ 팔로우 필터 (검색어와 상관없이 적용)
        if top_filter == "팔로우순" and login_user_id:
            board_filter_sql += """
            AND id IN (
                SELECT following_id
                FROM follow
                WHERE followed_id = %s
            )
            """
            params_filter.append(login_user_id)

        # 3️⃣ 검색 필터
        if search_type and search_keyword:
            if search_type == "board_title":
                board_filter_sql += " AND board_title LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "board_content":
                board_filter_sql += " AND board_content LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "id":
                board_filter_sql += " AND id IN (SELECT id FROM user WHERE nick LIKE %s)"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "tag":
                board_filter_sql += """
                AND board_no IN (
                    SELECT tb.board_no
                    FROM tag_board tb
                    JOIN tag t ON tb.tag_no = t.tag_no
                    WHERE t.tag_name LIKE %s
                )
                """
                params_filter.append(f"%{search_keyword}%")

        # 4️⃣ 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "팔로우순":
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"
        else:  # 최신순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 5️⃣ LIMIT + OFFSET
        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        # 6️⃣ 게시글 번호 조회
        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            # 7️⃣ 상세 조회 (Python에서 순서 유지)
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
            params_for_detail = tuple(board_nos)
            cursor.execute(sql, params_for_detail)
            rows = cursor.fetchall()

            # 8️⃣ 게시글 조립
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

            # 9️⃣ Python에서 정렬 유지
            boardList = [board_map[b] for b in board_nos if b in board_map]

    finally:
        cursor.close()
        conn.close()

    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색"],
        "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }

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

@bp.route('/write', methods=['GET', 'POST'])
def write():
    user = session.get("user")
    if not user:
        return redirect("/")

    user_type = user.get("user_type")

    if request.method == "GET":
        return render_template(
            'write.html',
            sidebar=SIDEBAR_CONFIG["default"],
            active="chat",
            user_type=user_type
        )

    # POST 요청: 글 저장
    title = request.form.get("boardTitle", "").strip()
    content = request.form.get("boardContent", "").strip()     
    category = request.form.get("boardCategory")
    user_id = user["id"]

    # 파일 업로드 (여러 파일 처리)
    uploaded_files = request.files.getlist("attach")
    saved_files_info = []

    import os, uuid
    UPLOAD_FOLDER = "app/uploads"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    for uploaded_file in uploaded_files:
        if uploaded_file and uploaded_file.filename != "":
            ext = os.path.splitext(uploaded_file.filename)[1]
            physical_name = f"{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, physical_name)
            uploaded_file.save(filepath)
            saved_files_info.append({
                "logical_name": uploaded_file.filename,
                "physical_name": physical_name,
                "size": os.path.getsize(filepath),
                "ext": ext[1:]
            })

    # DB 연결
    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1. board 테이블에 글 저장
        now = datetime.now()
        sql_board = """
        INSERT INTO board
        (id, board_title, board_content, board_category, hit, board_like, board_dislike, board_created_at, board_updated_at, board_deleted)
        VALUES (%s, %s, %s, %s, 0, 0, 0, %s, %s, 0)
        """
        cursor.execute(sql_board, (user_id, title, content, category, now, now))
        board_no = cursor.lastrowid  # 방금 삽입된 글 번호

        # 2. 파일 정보 저장
        for file_info in saved_files_info:
            sql_file = """
            INSERT INTO file
            (board_no, logical_file_name, physical_file_name, file_size, file_ext)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_file, (
                board_no,
                file_info["logical_name"],
                file_info["physical_name"],
                file_info["size"],
                file_info["ext"]
            ))

        # 3. 해시태그 저장 (기존 단일 태그 로직 그대로 사용)
        tag_string = request.form.get("tagName", "")
        tags = [t.strip() for t in tag_string.split(",") if t.strip()]
        for tag_name in tags:
            cursor.execute("SELECT tag_no FROM tag WHERE tag_name=%s", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_no = tag_row["tag_no"]
            else:
                cursor.execute("INSERT INTO tag (tag_name) VALUES (%s)", (tag_name,))
                tag_no = cursor.lastrowid
            cursor.execute("INSERT INTO tag_board (board_no, tag_no) VALUES (%s, %s)", (board_no, tag_no))

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/")

@bp.route('/add_item', methods=['POST'])
def add_item():
    user = session.get("user")
    if not user:
        return redirect("/")

    # 폼 데이터
    item_name = request.form.get("item_name", "").strip()
    item_price = request.form.get("item_price", "").strip()
    item_type = request.form.get("item_type")  # icon / background

    file = request.files.get("item_img")

    base_path = current_app.root_path

    # 업로드 경로 분기
    if item_type == "icon":
        upload_dir = os.path.join(base_path, "mypage", "static", "icons")
        db_img_path = "icons/"
    else:
        upload_dir = os.path.join(base_path, "mypage", "static", "backgrounds")
        db_img_path = "backgrounds/"

    # 디렉토리 생성
    os.makedirs(upload_dir, exist_ok=True)

    # 파일 저장
    filename = None
    if file and file.filename:
        # 원본 파일명 보안 처리
        filename = file.filename

        save_path = os.path.join(upload_dir, filename)
        file.save(save_path)

    # DB 저장
    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        sql = """
        INSERT INTO item
        (item_name, item_type, item_price, item_img, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(sql, (
            item_name,
            item_type,
            item_price,
            db_img_path + filename
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/pointshop")

@bp.route('/update/<int:board_no>', methods=['GET', 'POST'])
def update_post(board_no):
    user = session.get("user")
    if not user:
        flash("로그인이 필요한 페이지입니다.", "error")
        return redirect("/")

    user_id = user.get("id")
    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 기존 글 가져오기
        cursor.execute("SELECT * FROM board WHERE board_no=%s AND board_deleted=0", (board_no,))
        post = cursor.fetchone()
        if not post:
            flash("게시글을 찾을 수 없습니다.", "error")
            return redirect("/")

        # 작성자 확인
        if post["id"] != user_id:
            flash("권한이 없습니다.", "error")
            return redirect("/")

        if request.method == "GET":
            # 태그
            cursor.execute("""
                SELECT t.tag_name 
                FROM tag_board tb 
                JOIN tag t ON tb.tag_no = t.tag_no 
                WHERE tb.board_no=%s
            """, (board_no,))
            tags = [row['tag_name'] for row in cursor.fetchall()]
            tagString = ",".join(tags)

            # 파일
            cursor.execute("SELECT * FROM file WHERE board_no=%s", (board_no,))
            files = cursor.fetchall()
            files_camel = [{
                "fileNo": f["file_no"],
                "logicalFileName": f["logical_file_name"],
                "physicalFileName": f["physical_file_name"],
                "fileSize": f["file_size"],
                "fileExt": f["file_ext"]
            } for f in files]

            # 게시글 CamelCase 매핑
            post_camel = {
                "boardNo": post["board_no"],
                "boardTitle": post["board_title"],
                "boardContent": post["board_content"],
                "boardCategory": post["board_category"],
                "files": files_camel
            }

            return render_template(
                "write.html",
                post=post_camel,
                tagString=tagString,
                user_type=user["user_type"],
                sidebar=SIDEBAR_CONFIG["default"],
                active="chat"
            )

        elif request.method == "POST":
            # POST: DB 업데이트
            title = request.form.get("boardTitle", "").strip()
            content = request.form.get("boardContent", "").strip()
            category = request.form.get("boardCategory")
            tagString = request.form.get("tagName", "").strip()
            files = request.files.getlist("attach")

            if not title or not content:
                flash("제목과 내용을 모두 입력해야 합니다.", "error")
                return redirect(request.url)            
    
            now = datetime.now()
            # 게시글 업데이트
            cursor.execute("""
                UPDATE board
                SET board_title=%s, board_content=%s, board_category=%s, board_updated_at=%s
                WHERE board_no=%s
            """, (title, content, category, now, board_no))

            # 태그 업데이트
            cursor.execute("DELETE FROM tag_board WHERE board_no=%s", (board_no,))
            if tagString:
                tag_list = [t.strip() for t in tagString.split(",") if t.strip()]
                for tag_name in tag_list:
                    cursor.execute("SELECT tag_no FROM tag WHERE tag_name=%s", (tag_name,))
                    tag_row = cursor.fetchone()
                    if tag_row:
                        tag_no = tag_row['tag_no']
                    else:
                        cursor.execute("INSERT INTO tag (tag_name) VALUES (%s)", (tag_name,))
                        tag_no = cursor.lastrowid
                    cursor.execute("INSERT INTO tag_board (board_no, tag_no) VALUES (%s, %s)", (board_no, tag_no))

            # 파일 업로드
            upload_path = "app/uploads"
            import os, uuid
            for f in files:
                if f and f.filename:
                    ext = os.path.splitext(f.filename)[1][1:]
                    physical_name = f"{uuid.uuid4().hex}{ext}"
                    f.save(os.path.join(upload_path, physical_name))
                    size = os.path.getsize(os.path.join(upload_path, physical_name))
                    cursor.execute("""
                        INSERT INTO file 
                        (board_no, logical_file_name, physical_file_name, file_size, file_ext)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (board_no, f.filename, physical_name, size, ext))

            conn.commit()
            flash("게시글이 수정되었습니다.", "success")
            return redirect("/")

    finally:
        cursor.close()
        conn.close()

@bp.route('/info')
def info():
    page = 1
    per_page = 10
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1️⃣ 기본 필터
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 and board_category = 4"
        params_filter = []

        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        login_user_id = session.get("user", {}).get("id")

        # 2️⃣ 팔로우 필터 (검색어와 상관없이 적용)
        if top_filter == "팔로우순" and login_user_id:
            board_filter_sql += """
            AND id IN (
                SELECT following_id
                FROM follow
                WHERE followed_id = %s
            )
            """
            params_filter.append(login_user_id)

        # 3️⃣ 검색 필터
        if search_type and search_keyword:
            if search_type == "board_title":
                board_filter_sql += " AND board_title LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "board_content":
                board_filter_sql += " AND board_content LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "id":
                board_filter_sql += " AND id IN (SELECT id FROM user WHERE nick LIKE %s)"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "tag":
                board_filter_sql += """
                AND board_no IN (
                    SELECT tb.board_no
                    FROM tag_board tb
                    JOIN tag t ON tb.tag_no = t.tag_no
                    WHERE t.tag_name LIKE %s
                )
                """
                params_filter.append(f"%{search_keyword}%")

        # 4️⃣ 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "팔로우순":
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"
        else:  # 최신순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 5️⃣ LIMIT + OFFSET
        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        # 6️⃣ 게시글 번호 조회
        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            # 7️⃣ 상세 조회 (Python에서 순서 유지)
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
            params_for_detail = tuple(board_nos)
            cursor.execute(sql, params_for_detail)
            rows = cursor.fetchall()

            # 8️⃣ 게시글 조립
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

            # 9️⃣ Python에서 정렬 유지
            boardList = [board_map[b] for b in board_nos if b in board_map]

    finally:
        cursor.close()
        conn.close()

    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색"],
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

@bp.route('/terms')
def terms():
    page = 1
    per_page = 10
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1️⃣ 기본 필터
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 and board_category = 5"
        params_filter = []

        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        login_user_id = session.get("user", {}).get("id")

        # 2️⃣ 팔로우 필터 (검색어와 상관없이 적용)
        if top_filter == "팔로우순" and login_user_id:
            board_filter_sql += """
            AND id IN (
                SELECT following_id
                FROM follow
                WHERE followed_id = %s
            )
            """
            params_filter.append(login_user_id)

        # 3️⃣ 검색 필터
        if search_type and search_keyword:
            if search_type == "board_title":
                board_filter_sql += " AND board_title LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "board_content":
                board_filter_sql += " AND board_content LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "id":
                board_filter_sql += " AND id IN (SELECT id FROM user WHERE nick LIKE %s)"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "tag":
                board_filter_sql += """
                AND board_no IN (
                    SELECT tb.board_no
                    FROM tag_board tb
                    JOIN tag t ON tb.tag_no = t.tag_no
                    WHERE t.tag_name LIKE %s
                )
                """
                params_filter.append(f"%{search_keyword}%")

        # 4️⃣ 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "팔로우순":
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"
        else:  # 최신순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 5️⃣ LIMIT + OFFSET
        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        # 6️⃣ 게시글 번호 조회
        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            # 7️⃣ 상세 조회 (Python에서 순서 유지)
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
            params_for_detail = tuple(board_nos)
            cursor.execute(sql, params_for_detail)
            rows = cursor.fetchall()

            # 8️⃣ 게시글 조립
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

            # 9️⃣ Python에서 정렬 유지
            boardList = [board_map[b] for b in board_nos if b in board_map]

    finally:
        cursor.close()
        conn.close()

    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색"],
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

@bp.route('/privacy')
def privacy():
    page = 1
    per_page = 10
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1️⃣ 기본 필터
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 and board_category = 6"
        params_filter = []

        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        login_user_id = session.get("user", {}).get("id")

        # 2️⃣ 팔로우 필터 (검색어와 상관없이 적용)
        if top_filter == "팔로우순" and login_user_id:
            board_filter_sql += """
            AND id IN (
                SELECT following_id
                FROM follow
                WHERE followed_id = %s
            )
            """
            params_filter.append(login_user_id)

        # 3️⃣ 검색 필터
        if search_type and search_keyword:
            if search_type == "board_title":
                board_filter_sql += " AND board_title LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "board_content":
                board_filter_sql += " AND board_content LIKE %s"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "id":
                board_filter_sql += " AND id IN (SELECT id FROM user WHERE nick LIKE %s)"
                params_filter.append(f"%{search_keyword}%")
            elif search_type == "tag":
                board_filter_sql += """
                AND board_no IN (
                    SELECT tb.board_no
                    FROM tag_board tb
                    JOIN tag t ON tb.tag_no = t.tag_no
                    WHERE t.tag_name LIKE %s
                )
                """
                params_filter.append(f"%{search_keyword}%")

        # 4️⃣ 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "팔로우순":
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"
        else:  # 최신순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 5️⃣ LIMIT + OFFSET
        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        # 6️⃣ 게시글 번호 조회
        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            # 7️⃣ 상세 조회 (Python에서 순서 유지)
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
            params_for_detail = tuple(board_nos)
            cursor.execute(sql, params_for_detail)
            rows = cursor.fetchall()

            # 8️⃣ 게시글 조립
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

            # 9️⃣ Python에서 정렬 유지
            boardList = [board_map[b] for b in board_nos if b in board_map]

    finally:
        cursor.close()
        conn.close()

    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색"],
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

    conn = current_app.get_db_connection()
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

    conn = current_app.get_db_connection()
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

    conn = current_app.get_db_connection()
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

    conn = current_app.get_db_connection()
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

    data = request.get_json()
    comment_id = data.get("id")
    content = data.get("content", "").strip()

    if not comment_id or not content:
        return jsonify(success=False, msg="필수 정보 누락")
    
    # 욕설 포함 시 수정 금지
    if mask_slang(content) != content:
        return jsonify(success=False, msg="욕설이 포함되어 있어 댓글을 수정할 수 없습니다.")

    conn = current_app.get_db_connection()
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

    data = request.get_json()
    answer_id = data.get("id")
    content = data.get("content", "").strip()

    if not answer_id or not content:
        return jsonify(success=False, msg="필수 정보 누락")
    
        #  욕설 포함 시 수정 금지
    if mask_slang(content) != content:
        return jsonify(success=False, msg="욕설이 포함되어 있어 답변을 수정할 수 없습니다.")

    conn = current_app.get_db_connection()
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

    # 욕설 포함 여부 검사
    if mask_slang(content) != content:
        return jsonify(success=False, msg="댓글에 욕설이 포함되어 있어 등록할 수 없습니다.")


    conn = current_app.get_db_connection()
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
    
    if mask_slang(content) != content:
        return jsonify(success=False, msg="답변에 욕설이 포함되어 있어 작성할 수 없습니다.")


    conn = current_app.get_db_connection()
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
    
    conn = current_app.get_db_connection()
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

@bp.route("/vote", methods=["POST"])
def vote():
    if "user" not in session:
        return jsonify(success=False, msg="로그인이 필요합니다.")

    data = request.get_json()
    type_ = data.get("type")        # 'post' or 'comment'
    action = data.get("action")     # 'like' or 'dislike'
    target_id = data.get("id")      # 게시글 번호 또는 댓글 번호

    if not type_ or not action or not target_id:
        return jsonify(success=False, msg="필수 정보 누락")

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        if type_ == "post":
            table = "board"
            like_col = "board_like"
            dislike_col = "board_dislike"
            id_col = "board_no"
        elif type_ == "comment":
            table = "comment_answer"
            like_col = "comment_like_count"
            dislike_col = "comment_dislike_count"
            id_col = "comment_answer_no"
        else:
            return jsonify(success=False, msg="잘못된 타입")

        # 추천/비추천 업데이트
        if action == "like":
            cursor.execute(f"UPDATE {table} SET {like_col} = {like_col} + 1 WHERE {id_col} = %s", (target_id,))
        else:
            cursor.execute(f"UPDATE {table} SET {dislike_col} = {dislike_col} + 1 WHERE {id_col} = %s", (target_id,))

        conn.commit()

        # 최종 카운트 조회
        cursor.execute(f"SELECT {like_col}, {dislike_col} FROM {table} WHERE {id_col} = %s", (target_id,))
        row = cursor.fetchone()
        count = row[like_col] if action == "like" else row[dislike_col]

        return jsonify(success=True, count=count)

    except Exception as e:
        conn.rollback()
        return jsonify(success=False, msg=str(e))
    finally:
        cursor.close()
        conn.close()

@bp.route("/post/hit/<int:board_no>", methods=["POST"])
def increment_hit(board_no):
    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("UPDATE board SET hit = hit + 1 WHERE board_no = %s", (board_no,))
        conn.commit()
        cursor.execute("SELECT hit FROM board WHERE board_no = %s", (board_no,))
        new_hit = cursor.fetchone()["hit"]
        return jsonify(success=True, hit=new_hit)
    except Exception as e:
        conn.rollback()
        return jsonify(success=False, msg=str(e))
    finally:
        cursor.close()
        conn.close()

@bp.route("/download")
def download_file():
    from flask import current_app
    UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')

    file_no = request.args.get("no")
    if not file_no:
        return abort(400, "파일 번호가 필요합니다.")

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # DB에서 물리/논리 파일명 가져오기
        cursor.execute(
            "SELECT physical_file_name, logical_file_name FROM file WHERE file_no = %s",
            (file_no,)
        )
        row = cursor.fetchone()
        if not row:
            return abort(404, "파일이 존재하지 않습니다.")

        physical_name = row["physical_file_name"]
        logical_name = row["logical_file_name"]

        file_path = os.path.join(UPLOAD_FOLDER, physical_name)
        if not os.path.exists(file_path):
            return abort(404, "파일이 존재하지 않습니다.")

        # send_from_directory로 다운로드
        return send_from_directory(
            UPLOAD_FOLDER,
            physical_name,
            as_attachment=True,
            download_name=logical_name
        )
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})
    finally:
        cursor.close()
        conn.close()

@bp.route("/delete_file/<int:file_no>", methods=["POST"])
def delete_file(file_no):
    user = session.get("user")
    if not user:
        return {"success": False, "message": "로그인이 필요합니다."}, 401

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 1. 파일 정보 가져오기
        cursor.execute("SELECT * FROM file WHERE file_no=%s", (file_no,))
        file_row = cursor.fetchone()
        if not file_row:
            return {"success": False, "message": "파일이 존재하지 않습니다."}, 404

        # 2. 작성자 확인 (파일이 속한 게시글 확인)
        cursor.execute("SELECT * FROM board WHERE board_no=%s", (file_row["board_no"],))
        post = cursor.fetchone()
        if post["id"] != user["id"]:
            return {"success": False, "message": "권한이 없습니다."}, 403

        # 3. 실제 파일 삭제
        import os
        file_path = os.path.join("app/uploads", file_row["physical_file_name"])
        if os.path.exists(file_path):
            os.remove(file_path)

        # 4. DB에서 삭제
        cursor.execute("DELETE FROM file WHERE file_no=%s", (file_no,))
        conn.commit()

        return {"success": True}

    finally:
        cursor.close()
        conn.close()

@bp.route('/tags/')
@bp.route('/tags/<path:tag_name>')
def tag_filter(tag_name=None):
    tag_name = unquote(tag_name) if tag_name else None

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    top_filter = request.args.get('top', '최신순')
    feed_filter = request.args.get('feed', '전체')
    offset = (page - 1) * per_page

    conn = current_app.get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 1️⃣ 태그 필터가 있는 경우, 해당 게시글 번호 조회
        board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0"
        params_filter = []

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

        # 2️⃣ feed_filter 적용
        category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
        if feed_filter != "전체" and feed_filter in category_map:
            board_filter_sql += " AND board_category = %s"
            params_filter.append(category_map[feed_filter])

        # 3️⃣ 팔로우 필터 적용
        login_user_id = session.get("user", {}).get("id")
        if top_filter == "팔로우순" and login_user_id:
            board_filter_sql += """
            AND id IN (
                SELECT following_id
                FROM follow
                WHERE followed_id = %s
            )
            """
            params_filter.append(login_user_id)

        # 4️⃣ 정렬
        if top_filter == "조회순":
            order_clause = "ORDER BY hit DESC, board_created_at DESC, board_no DESC"
        elif top_filter == "추천순":
            order_clause = "ORDER BY board_like DESC, board_created_at DESC, board_no DESC"
        else:  # 최신순 & 팔로우순 기본
            order_clause = "ORDER BY board_created_at DESC, board_no DESC"

        # 5️⃣ LIMIT + OFFSET
        board_filter_sql = f"{board_filter_sql} {order_clause} LIMIT %s OFFSET %s"
        params_filter.extend([per_page, offset])

        # 6️⃣ 게시글 번호 조회
        cursor.execute(board_filter_sql, tuple(params_filter))
        board_rows = cursor.fetchall()
        board_nos = [r['board_no'] for r in board_rows]

        if not board_nos:
            boardList = []
        else:
            # 7️⃣ 상세 조회
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

            # 8️⃣ 게시글 조립
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

            # 9️⃣ Python에서 정렬 유지
            boardList = [board_map[b] for b in board_nos if b in board_map]

    finally:
        cursor.close()
        conn.close()

    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색"],
        "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }

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
        login_user_id=login_user_id,
        tag_name=tag_name
    )

@bp.route('/api/recommend_tags', methods=['POST'])
def recommend_tags():
    # 1. 요청 데이터 확인
    data = request.json
    title = data.get('title', 'No Title')
    content = data.get('content', 'No Content')

    if not client:
        return jsonify({"error": "API Client not initialized"}), 500

    prompt = f"""
    아래 제목과 내용을 분석하여, 이 글에 가장 적합한 **한국어 해시태그 5개**를 **다른 설명 없이 쉼표(,)로만 구분하여** 추천해 주세요.
    
    예시 출력 형식: **파이썬,플라스크,웹개발,데이터베이스,취미생활**
    
    ---
    
    제목: "{title}"
    내용: "{content[:500]}..."
    """

    try:
        # 2. 모델 호출 전 확인
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        
        # 3. 모델 응답 확인 (가장 중요한 부분)
        
        # 4. 응답 처리 및 반환
        recommended_tags = response.text.strip()
        
        # 5. 최종 결과 확인
        return jsonify({"tags": recommended_tags})

    except Exception as e:
        print(f"DEBUG_ERROR: Full API/Processing Error: {e}")
        # 이 부분이 실행되었을 때 500 에러 메시지가 브라우저로 갑니다.
        return jsonify({"error": "Failed to get recommendations"}), 500
    
@bp.route("/follow", methods=["POST"])
def follow():
    user = session.get("user")
    if not user:
        return jsonify(success=False, msg="로그인 필요")

    data = request.get_json(silent=True)
    if not data or "followed_id" not in data:
        return jsonify(success=False, msg="잘못된 요청")

    following_id = str(user["id"]).strip()
    followed_id = str(data["followed_id"]).strip()

    # 빈 값 방지
    if not followed_id:
        return jsonify(success=False, msg="잘못된 요청")

    # 자기 자신 팔로우 방지
    if following_id == followed_id:
        return jsonify(success=False, msg="자기 자신은 팔로우할 수 없습니다.")

    conn = current_app.get_db_connection()
    cursor = conn.cursor()

    try:
        # 이미 팔로우 중인지 체크
        cursor.execute("""
            SELECT 1
            FROM follow
            WHERE following_id=%s AND followed_id=%s
        """, (following_id, followed_id))

        if cursor.fetchone():
            return jsonify(success=False, msg="이미 팔로잉 중입니다.")

        # 팔로우 등록
        cursor.execute("""
            INSERT INTO follow (following_id, followed_id)
            VALUES (%s, %s)
        """, (following_id, followed_id))

        conn.commit()
        return jsonify(success=True, msg="팔로우 완료")

    finally:
        cursor.close()
        conn.close()

@bp.route("/unfollow", methods=["POST"])
def unfollow():
    user = session.get("user")
    if not user:
        return jsonify(success=False, msg="로그인 필요")

    data = request.get_json(silent=True)
    if not data or "followed_id" not in data:
        return jsonify(success=False, msg="잘못된 요청")

    following_id = str(user["id"]).strip()
    followed_id = str(data["followed_id"]).strip()

    if not followed_id:
        return jsonify(success=False, msg="잘못된 요청")

    conn = current_app.get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM follow
            WHERE following_id=%s AND followed_id=%s
        """, (following_id, followed_id))

        conn.commit()
        return jsonify(success=True, msg="언팔로우 완료")

    finally:
        cursor.close()
        conn.close()

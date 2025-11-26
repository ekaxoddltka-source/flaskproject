# app/home/routes.py
from flask import Blueprint, render_template, jsonify, request, session, send_from_directory, abort
from datetime import datetime
from config import SIDEBAR_CONFIG
import pymysql
import os
from urllib.parse import unquote
from app.database import get_db_connection

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

    sql = "SELECT board_title FROM board where board_category = 4 and board_deleted = 0 ORDER BY board_created_at DESC LIMIT 1"
    cur.execute(sql)
    row = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({"title": row["board_title"] if row else ""})

@bp.route('/')
def home():
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 검색용 게시글 번호 필터링 (서브쿼리 방식)
    board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0"
    params_filter = []

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        board_filter_sql += f" AND board_category = {category_map[feed_filter]}"
    
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

    # 검색 타입에 따른 조건
    if search_type and search_keyword:
        if search_type == "board_title":
            board_filter_sql += " AND board_title LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "board_content":
            board_filter_sql += " AND board_content LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "id":
            board_filter_sql += """
            AND id IN (
                SELECT id FROM user WHERE nick LIKE %s
            )
            """
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

    cursor.execute(board_filter_sql, tuple(params_filter))
    board_nos = [row['board_no'] for row in cursor.fetchall()]

    if not board_nos:
        boardList = []
    else:
        format_strings = ','.join(['%s'] * len(board_nos))
        sql = f"""
            SELECT 
                board.board_no AS board_no,
                board.id AS writer_id,
                user.nick AS writer_nick,
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

        cursor.execute(sql, board_nos)
        rows = cursor.fetchall()

        board_map = {}
        for row in rows:
            boardNo = row["board_no"]
            if boardNo not in board_map:
                board_map[boardNo] = {
                    "boardNo": boardNo,
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
            # 파일 처리
            if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
                post["files"].append({
                    "fileNo": row["file_no"],
                    "logicalFileName": row["logical_file_name"],
                    "physicalFileName": row["physical_file_name"],
                    "fileSize": row["file_size"],
                    "fileExt": row["file_ext"]
                })
            # 태그 처리
            if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
                post["tags"].append({"tagName": row["tag_name"]})
            # 댓글 처리
            if row["comment_answer_no"] is not None:
                if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                    post["comments"].append({
                        "commentAnswerNo": row["comment_answer_no"],
                        "boardNo": boardNo,
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

    # top 정렬
    if top_filter == "조회순":
        boardList.sort(key=lambda x: x["hit"], reverse=True)
    elif top_filter == "추천순":
        boardList.sort(key=lambda x: x["boardLike"], reverse=True)
    elif top_filter == "팔로우순":
        boardList.sort(key=lambda x: x.get("follow_count", 0), reverse=True)
    else:
        boardList.sort(key=lambda x: x["boardNo"], reverse=True)

    cursor.close()
    conn.close()

    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색순"],
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

@bp.route('/write')
def write():
    return render_template(
    'write.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/terms')
def terms():
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 검색용 게시글 번호 필터링 (서브쿼리 방식)
    board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND board_category = 5"
    params_filter = []

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        board_filter_sql += f" AND board_category = {category_map[feed_filter]}"

    print("search_type:", search_type)
    print("search_keyword:", search_keyword)

    # 검색 타입에 따른 조건
    if search_type and search_keyword:
        if search_type == "board_title":
            board_filter_sql += " AND board_title LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "board_content":
            board_filter_sql += " AND board_content LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "id":
            board_filter_sql += """
            AND id IN (
                SELECT id FROM user WHERE nick LIKE %s
            )
            """
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

    print("검색 SQL:", board_filter_sql)
    print("파라미터:", params_filter)

    cursor.execute(board_filter_sql, tuple(params_filter))
    board_nos = [row['board_no'] for row in cursor.fetchall()]

    if not board_nos:
        boardList = []
    else:
        format_strings = ','.join(['%s'] * len(board_nos))
        sql = f"""
            SELECT 
                board.board_no AS board_no,
                board.id AS writer_id,
                user.nick AS writer_nick,
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

        cursor.execute(sql, board_nos)
        rows = cursor.fetchall()

        board_map = {}
        for row in rows:
            boardNo = row["board_no"]
            if boardNo not in board_map:
                board_map[boardNo] = {
                    "boardNo": boardNo,
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
            # 파일 처리
            if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
                post["files"].append({
                    "fileNo": row["file_no"],
                    "logicalFileName": row["logical_file_name"],
                    "physicalFileName": row["physical_file_name"],
                    "fileSize": row["file_size"],
                    "fileExt": row["file_ext"]
                })
            # 태그 처리
            if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
                post["tags"].append({"tagName": row["tag_name"]})
            # 댓글 처리
            if row["comment_answer_no"] is not None:
                if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                    post["comments"].append({
                        "commentAnswerNo": row["comment_answer_no"],
                        "boardNo": boardNo,
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

    # top 정렬
    if top_filter == "조회순":
        boardList.sort(key=lambda x: x["hit"], reverse=True)
    elif top_filter == "추천순":
        boardList.sort(key=lambda x: x["boardLike"], reverse=True)
    elif top_filter == "팔로우순":
        boardList.sort(key=lambda x: x.get("follow_count", 0), reverse=True)
    else:
        boardList.sort(key=lambda x: x["boardNo"], reverse=True)

    cursor.close()
    conn.close()

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
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 검색용 게시글 번호 필터링 (서브쿼리 방식)
    board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND board_category = 4"
    params_filter = []

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        board_filter_sql += f" AND board_category = {category_map[feed_filter]}"

    print("search_type:", search_type)
    print("search_keyword:", search_keyword)

    # 검색 타입에 따른 조건
    if search_type and search_keyword:
        if search_type == "board_title":
            board_filter_sql += " AND board_title LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "board_content":
            board_filter_sql += " AND board_content LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "id":
            board_filter_sql += """
            AND id IN (
                SELECT id FROM user WHERE nick LIKE %s
            )
            """
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

    print("검색 SQL:", board_filter_sql)
    print("파라미터:", params_filter)

    cursor.execute(board_filter_sql, tuple(params_filter))
    board_nos = [row['board_no'] for row in cursor.fetchall()]

    if not board_nos:
        boardList = []
    else:
        format_strings = ','.join(['%s'] * len(board_nos))
        sql = f"""
            SELECT 
                board.board_no AS board_no,
                board.id AS writer_id,
                user.nick AS writer_nick,
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

        cursor.execute(sql, board_nos)
        rows = cursor.fetchall()

        board_map = {}
        for row in rows:
            boardNo = row["board_no"]
            if boardNo not in board_map:
                board_map[boardNo] = {
                    "boardNo": boardNo,
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
            # 파일 처리
            if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
                post["files"].append({
                    "fileNo": row["file_no"],
                    "logicalFileName": row["logical_file_name"],
                    "physicalFileName": row["physical_file_name"],
                    "fileSize": row["file_size"],
                    "fileExt": row["file_ext"]
                })
            # 태그 처리
            if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
                post["tags"].append({"tagName": row["tag_name"]})
            # 댓글 처리
            if row["comment_answer_no"] is not None:
                if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                    post["comments"].append({
                        "commentAnswerNo": row["comment_answer_no"],
                        "boardNo": boardNo,
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

    # top 정렬
    if top_filter == "조회순":
        boardList.sort(key=lambda x: x["hit"], reverse=True)
    elif top_filter == "추천순":
        boardList.sort(key=lambda x: x["boardLike"], reverse=True)
    elif top_filter == "팔로우순":
        boardList.sort(key=lambda x: x.get("follow_count", 0), reverse=True)
    else:
        boardList.sort(key=lambda x: x["boardNo"], reverse=True)

    cursor.close()
    conn.close()

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
    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')
    search_type = request.args.get('search_type')
    search_keyword = request.args.get('keyword', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 검색용 게시글 번호 필터링 (서브쿼리 방식)
    board_filter_sql = "SELECT board_no FROM board WHERE board_deleted = 0 AND board_category = 6"
    params_filter = []

    # feed 필터링
    category_map = {"자유": 1, "Q&A": 2, "코딩테스트": 3, "공지사항": 4, "이용약관": 5, "개인정보처리방침": 6}
    if feed_filter != "전체" and feed_filter in category_map:
        board_filter_sql += f" AND board_category = {category_map[feed_filter]}"

    print("search_type:", search_type)
    print("search_keyword:", search_keyword)

    # 검색 타입에 따른 조건
    if search_type and search_keyword:
        if search_type == "board_title":
            board_filter_sql += " AND board_title LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "board_content":
            board_filter_sql += " AND board_content LIKE %s"
            params_filter.append(f"%{search_keyword}%")

        elif search_type == "id":
            board_filter_sql += """
            AND id IN (
                SELECT id FROM user WHERE nick LIKE %s
            )
            """
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

    print("검색 SQL:", board_filter_sql)
    print("파라미터:", params_filter)

    cursor.execute(board_filter_sql, tuple(params_filter))
    board_nos = [row['board_no'] for row in cursor.fetchall()]

    if not board_nos:
        boardList = []
    else:
        format_strings = ','.join(['%s'] * len(board_nos))
        sql = f"""
            SELECT 
                board.board_no AS board_no,
                board.id AS writer_id,
                user.nick AS writer_nick,
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

        cursor.execute(sql, board_nos)
        rows = cursor.fetchall()

        board_map = {}
        for row in rows:
            boardNo = row["board_no"]
            if boardNo not in board_map:
                board_map[boardNo] = {
                    "boardNo": boardNo,
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
            # 파일 처리
            if row["file_no"] is not None and not any(f["fileNo"] == row["file_no"] for f in post["files"]):
                post["files"].append({
                    "fileNo": row["file_no"],
                    "logicalFileName": row["logical_file_name"],
                    "physicalFileName": row["physical_file_name"],
                    "fileSize": row["file_size"],
                    "fileExt": row["file_ext"]
                })
            # 태그 처리
            if row["tag_name"] is not None and not any(t["tagName"] == row["tag_name"] for t in post["tags"]):
                post["tags"].append({"tagName": row["tag_name"]})
            # 댓글 처리
            if row["comment_answer_no"] is not None:
                if not any(c["commentAnswerNo"] == row["comment_answer_no"] for c in post["comments"]):
                    post["comments"].append({
                        "commentAnswerNo": row["comment_answer_no"],
                        "boardNo": boardNo,
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

    # top 정렬
    if top_filter == "조회순":
        boardList.sort(key=lambda x: x["hit"], reverse=True)
    elif top_filter == "추천순":
        boardList.sort(key=lambda x: x["boardLike"], reverse=True)
    elif top_filter == "팔로우순":
        boardList.sort(key=lambda x: x.get("follow_count", 0), reverse=True)
    else:
        boardList.sort(key=lambda x: x["boardNo"], reverse=True)

    cursor.close()
    conn.close()

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

    data = request.get_json()
    comment_id = data.get("id")
    content = data.get("content", "").strip()

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

    data = request.get_json()
    answer_id = data.get("id")
    content = data.get("content", "").strip()

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

    conn = get_db_connection()
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
    conn = get_db_connection()
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

    conn = get_db_connection()
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

@bp.route('/tags/')
@bp.route('/tags/<path:tag_name>')
def tag_filter(tag_name):
    tag_name = unquote(tag_name)  # URL 디코딩

    top_filter = request.args.get('top', '최신순')  
    feed_filter = request.args.get('feed', '전체')  

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 해당 태그가 달린 게시글 번호만 가져오기
    cursor.execute("""
        SELECT DISTINCT b.board_no
        FROM board b
        JOIN tag_board tb ON b.board_no = tb.board_no
        JOIN tag t ON tb.tag_no = t.tag_no
        WHERE b.board_deleted = 0 AND t.tag_name = %s
    """, (tag_name,))
    board_nos = [row['board_no'] for row in cursor.fetchall()]

    if not board_nos:
        boardList = []
    else:
        # 2. 해당 게시글들 전체 정보를 가져오기 (모든 태그 포함)
        format_strings = ','.join(['%s'] * len(board_nos))
        sql = f"""
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
            WHERE board.board_no IN ({format_strings})
        """
        cursor.execute(sql, board_nos)
        rows = cursor.fetchall()

        # board_map 생성 (기존 home() 방식과 동일)
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

    cursor.close()
    conn.close()

    notice_buttons = {
        "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색순"],
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


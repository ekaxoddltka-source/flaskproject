# app/home/routes.py
from flask import Blueprint, render_template, jsonify, request
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

    return render_template(
        'home.html',
        boardList=boardList,
        show_writeBtn=True,
        show_notice_buttons=True,
        notice_buttons=notice_buttons,
        active="chat",
        sidebar=SIDEBAR_CONFIG["default"],
        top_filter=top_filter,       
        feed_filter=feed_filter      
    )

@bp.route('/write')
def write():
    return render_template(
    'write.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/info')
def info():
    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "검색순"],
    "feed_buttons": ["전체"]
    }
    return render_template(
    'info.html', 
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["info"],
    active="info"
)
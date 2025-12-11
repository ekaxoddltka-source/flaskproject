from flask import Blueprint, render_template, jsonify, request, current_app
import pymysql

bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/admin/static'
)

@bp.route("/admin-users")
def admin_users():
    
    return render_template("admin-users.html")

# =========================
# 사용자 목록 API (동적 로딩 + 페이지네이션)
# =========================
@bp.route("/api/admin-users", methods=["GET"])
def api_admin_users():
    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "ASC").upper()

    # 페이지네이션
    try:
        page = int(request.args.get("page", 1))
    except:
        page = 1
    try:
        limit = int(request.args.get("limit", 10))
    except:
        limit = 10

    if page < 1:
        page = 1
    if limit < 1 or limit > 200:
        limit = 10

    offset = (page - 1) * limit

    conn = current_app.get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # ---------------------------
    # 🔍 기본 SQL 구성 (너의 기존 스타일 유지)
    # ---------------------------
    sql_where = "WHERE 1"
    params = []

    # 검색
    if search:
        sql_where += " AND (id = %s OR nick LIKE %s)"
        params.append(search)
        params.append(f"%{search}%")

    # 정렬 화이트리스트
    if sort_by not in ["created_at", "last_login_at", "user_type", "withdraw" ,"user_current_point"]:
        sort_by = "created_at"
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "ASC"

    # ---------------------------
    # 📌 전체 개수 조회
    # ---------------------------
    count_sql = f"SELECT COUNT(*) AS total FROM user {sql_where}"
    cur.execute(count_sql, params)
    total_count = cur.fetchone()["total"]

    # ---------------------------
    # 📌 실제 페이징된 데이터 조회
    # ---------------------------
    data_sql = f"""
        SELECT *
        FROM user
        {sql_where}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """
    cur.execute(data_sql, params + [limit, offset])
    users = cur.fetchall()

    # 날짜 포맷
    for u in users:
        for key in ["created_at", "updated_at", "last_login_at", "withdraw_at"]:
            if key in u and u[key]:
                u[key] = u[key].strftime("%Y-%m-%d %H:%M:%S")

    # ---------------------------
    # 📌 통계 정보 (기존 그대로 유지)
    # ---------------------------
    cur.execute("""
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN withdraw=0 THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN withdraw=1 THEN 1 ELSE 0 END) AS withdrawn
        FROM user
    """)
    stats = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({
        "users": users,
        "stats": stats,
        "total_count": total_count,
        "page": page,
        "limit": limit
    })

# =========================
# 사용자 정보 업데이트 API (통합)
# =========================
@bp.route("/api/admin-users/update", methods=["POST"])
def api_admin_users_update():
    data = request.json
    updates = data.get("updates", [])

    if not isinstance(updates, list) or len(updates) == 0:
        return jsonify({"success": False, "message": "No update data provided"}), 400

    conn = current_app.get_db_connection()
    cur = conn.cursor()

    try:
        for u in updates:
            user_id = u.get("id")
            if not user_id:
                continue

            fields = []
            params = []

            # 변경된 필드만 업데이트
            if "user_type" in u:
                fields.append("user_type = %s")
                params.append(u["user_type"])

            if "withdraw" in u:
                fields.append("withdraw = %s")
                params.append(u["withdraw"])

                if u["withdraw"] == 1:
                    fields.append("withdraw_at = NOW()")
                elif u["withdraw"] == 0:
                    fields.append("withdraw_at = NULL")
    
            if "points" in u:
                fields.append("user_current_point = %s")
                params.append(u["points"])

            if not fields:
                continue  # 변경된 값이 없음 → 스킵

            set_clause = ", ".join(fields)
            params.append(user_id)

            sql = f"UPDATE user SET {set_clause} WHERE id = %s"
            cur.execute(sql, params)

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cur.close()
        conn.close()

    return jsonify({"success": True})



@bp.route("/admin-report")
def admin_report():
    
    return render_template("admin-report.html")

# =========================
# 신고 목록 조회 (검색 + 필터 + 페이징 통합)
# =========================
@bp.route("/api/admin-reports", methods=["GET"])
def api_admin_reports():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()         # 1=대기중, 2=처리완료, 3=취소
    category = request.args.get("category", "").strip()     # 1~4

    try:
        page = int(request.args.get("page", 1))
    except:
        page = 1

    if page < 1:
        page = 1

    limit = 10  # 페이지당 항목 수 고정
    offset = (page - 1) * limit

    offset = (page - 1) * limit

    conn = current_app.get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # ---------------------------
    # WHERE 조건
    # ---------------------------
    sql_where = "WHERE 1"
    params = []

    if search:
        sql_where += """
            AND (
                report_user_id = %s
                OR board_no = CAST(%s AS UNSIGNED)
                OR report_content LIKE %s
            )
        """
        params += [search, search, f"%{search}%"]

    if status:
        sql_where += " AND report_status = %s"
        params.append(status)

    if category:
        sql_where += " AND report_category = %s"
        params.append(category)

    # ---------------------------
    # 전체 개수
    # ---------------------------
    count_sql = f"SELECT COUNT(*) AS total FROM report {sql_where}"
    cur.execute(count_sql, params)
    total_count = cur.fetchone()["total"]

    # ---------------------------
    # 실제 데이터 조회
    # ---------------------------
    sql = f"""
        SELECT
            report_no,
            report_user_id,
            board_no,
            report_category,
            report_content,
            report_status,
            reported_at,
            report_updated_at
        FROM report
        {sql_where}
        ORDER BY report_no ASC
        LIMIT %s OFFSET %s
    """
    cur.execute(sql, params + [limit, offset])
    reports = cur.fetchall()

    # 날짜 문자열 변환 + 카테고리/상태 텍스트 매핑
    category_map = {1: "욕설/비방", 2: "스팸/광고", 3: "음란물", 4: "도배"}
    status_map = {1: "대기중", 2: "처리완료", 3: "취소"}

    for r in reports:
        r["category_text"] = category_map.get(r["report_category"], "기타")
        r["status_text"] = status_map.get(r["report_status"], "알수없음")
        for key in ["reported_at", "report_updated_at"]:
            if r[key]:
                r[key] = r[key].strftime("%Y-%m-%d %H:%M:%S")

    cur.close()
    conn.close()

    return jsonify({
        "reports": reports,
        "total_count": total_count,
        "page": page,
        "limit": limit
    })


# =========================
# 신고 업데이트 (통합)
# - 단일/일괄 처리 완료 (report_status=2)
# - 단일/일괄 취소(삭제) (report_status=3)
# =========================
@bp.route("/api/admin-reports/update", methods=["POST"])
def api_admin_reports_update():
    data = request.json
    action = data.get("action")      # resolve, delete
    ids = data.get("ids", [])        # report_no 리스트

    if not action or not isinstance(ids, list) or len(ids) == 0:
        return jsonify({"success": False, "message": "Invalid parameters"}), 400

    conn = current_app.get_db_connection()
    cur = conn.cursor()

    try:
        if action == "resolve":
            # 선택한 신고 번호들로 게시글 번호(board_no) 조회
            cur.execute(
                "SELECT DISTINCT board_no FROM report WHERE report_no IN (%s)" % ",".join(["%s"]*len(ids)),
                ids
            )
            board_nos = [row["board_no"] for row in cur.fetchall()]

            if board_nos:
                # 같은 게시글 번호를 가진 모든 신고를 처리 완료로
                cur.execute(
                    "UPDATE report SET report_status = 2, report_updated_at = NOW() WHERE board_no IN (%s)" % ",".join(["%s"]*len(board_nos)),
                    board_nos
                )
                # 해당 게시글 삭제 처리
                cur.execute(
                    "UPDATE board SET board_deleted = 1 WHERE board_no IN (%s)" % ",".join(["%s"]*len(board_nos)),
                    board_nos
                )

        elif action == "delete":
            # 실제 DB에서 삭제
            sql = """
                DELETE FROM report
                WHERE report_no IN (%s)
            """ % (",".join(["%s"] * len(ids)))
            cur.execute(sql, ids)

        else:
            return jsonify({"success": False, "message": "Unknown action"}), 400

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cur.close()
        conn.close()

    return jsonify({"success": True})


@bp.route("/admin-ad")
def admin_ad():
    
    return render_template("admin-ad.html")
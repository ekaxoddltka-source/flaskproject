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
# 사용자 목록 API (동적 로딩)
# =========================
@bp.route("/api/admin-users", methods=["GET"])
def api_admin_users():
    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "ASC").upper()

    conn = current_app.get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT * FROM user WHERE 1"
    params = []

    # 검색
    if search:
        # id는 정확히, nick은 포함 검색
        sql += " AND (id = %s OR nick LIKE %s)"
        params.append(search)               # 정확히 일치
        params.append(f"%{search}%")       # 포함 검색

    # 정렬
    if sort_by not in ["created_at", "last_login_at", "user_type", "withdraw"]:
        sort_by = "created_at"
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "ASC"

    sql += f" ORDER BY {sort_by} {sort_order}"

    cur.execute(sql, params)
    users = cur.fetchall()

    for u in users:
        for key in ["created_at", "updated_at", "last_login_at", "withdraw_at"]:
            if key in u and u[key]:
                u[key] = u[key].strftime("%Y-%m-%d %H:%M:%S")


    # 통계
    cur.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN withdraw=0 THEN 1 ELSE 0 END) AS active, SUM(CASE WHEN withdraw=1 THEN 1 ELSE 0 END) AS withdrawn FROM user")
    stats = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({"users": users, "stats": stats})

# =========================
# 사용자 목록 API (동적 로딩)
# =========================





@bp.route("/admin-report")
def admin_report():
    
    return render_template("admin-report.html")

@bp.route("/admin-ad")
def admin_ad():
    
    return render_template("admin-ad.html")
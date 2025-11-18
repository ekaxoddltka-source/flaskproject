# app/account/routes.py
from flask import Blueprint, render_template
from config import SIDEBAR_CONFIG

bp = Blueprint(
    'account',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/account/static'
)

@bp.route('/join-agree')
def join_agree():
    return render_template(
    'join_agree.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/join-info')
def join_info():
    return render_template(
    'join_info.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)

@bp.route('/join-find')
def join_find():
    return render_template(
    'join_find.html',
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
)
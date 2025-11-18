# app/home/routes.py
from flask import Blueprint, render_template
from config import SIDEBAR_CONFIG

bp = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)

@bp.route('/')
def home():
    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색순"],
    "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }
    return render_template(
    'home.html', 
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["default"],
    active="chat"
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
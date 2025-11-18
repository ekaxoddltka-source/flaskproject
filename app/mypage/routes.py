from flask import Blueprint, render_template
from config import SIDEBAR_CONFIG

bp = Blueprint(
    'mypage',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/mypage/static'
)

@bp.route('/mypage-posts')
def mypage():
    notice_buttons = {
    "top_buttons": ["최신순", "조회순", "추천순", "팔로우순", "검색순"],
    "feed_buttons": ["전체", "자유", "코딩테스트", "Q&A"]
    }
    return render_template(
    'mypage-posts.html', 
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage"
)

@bp.route('/minigame')
def minigame():
    return render_template(
    'minigame.html'
)

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
    "feed_buttons": ["전체", "아이콘", "휘장", "배경이미지"]
    }
    return render_template(
    'pointshop.html', 
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["pointstore"],
    active="pointstore"
)
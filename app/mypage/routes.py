from flask import Blueprint, render_template
from config import SIDEBAR_CONFIG

bp = Blueprint(
    'mypage',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/mypage/static'
)

@bp.route('/mypage')
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
@bp.route('/mypage-interest')
def mypage_interest():

    # 실제 DB 기반이면 여기서 분석
    top5_labels = ["Python", "React", "AI", "SQL", "Docker"]
    top5_values = [55, 40, 30, 22, 15]

    radar_labels = ["Frontend", "Backend", "AI/ML", "DevOps", "CS 기본"]
    radar_values = [65, 45, 88, 40, 55]

    return render_template(
        'mypage-interest.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        top5_labels=top5_labels,
        top5_values=top5_values,
        radar_labels=radar_labels,
        radar_values=radar_values
    )


@bp.route('/mypage-info')
def mypage_info():
    return render_template(
    'mypage-info.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage"
)

@bp.route('/mypage-follow')
def mypage_follow():
    return render_template(
    'mypage-follow.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage"
)

@bp.route('/mypage-message')
def mypage_message():
    return render_template(
    'mypage-message.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage"
)

@bp.route('/mypage-point')
def mypage_point():
    return render_template(
    'mypage-point.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage"
)

@bp.route('/mypage-alert')
def mypage_alert():
    return render_template(
    'mypage-alert.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage"
)

@bp.route('/mypage-withdraw')
def mypage_withdraw():
    return render_template(
    'mypage-withdraw.html',            
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
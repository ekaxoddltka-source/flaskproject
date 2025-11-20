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
def mypage_posts():

    current_bg = "backgrounds/m.png"

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
    active="mypage",
    current_bg = current_bg
)
@bp.route('/mypage-interest')
def mypage_interest():

    current_bg = "backgrounds/m.png"

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
        radar_values=radar_values,
        current_bg = current_bg
    )

@bp.route('/mypage-items')
def mypage_item():

    # 배경 이미지 장착된 경로
    current_bg = "backgrounds/m.png"   # 🔥 여기를 반드시 설정해야 한다

    # 아이템 리스트
    items = [
        {
            "id": 1,
            "name": "고양이 아이콘",
            "desc": "프로필 아이콘",
            "type": "icon",
            "img": "icons/cat.png",     # 🔥 올바른 상대경로
            "equipped": True
        },
  
        {
            "id": 2,
            "name": "아이돌 배경",
            "desc": "배경 이미지",
            "type": "bg",
            "img": "backgrounds/m.png",   # 🔥 전역 경로 제거
            "equipped": True
        },
    ]

    return render_template(
        'mypage-items.html',
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        items=items,
        current_bg=current_bg     # 🔥 템플릿으로 전달
    )


@bp.route('/mypage-info')
def mypage_info():
    current_bg = "backgrounds/m.png"
    return render_template(
    'mypage-info.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage",
    current_bg = current_bg
)

@bp.route('/mypage-following')
def mypage_following():

    # 임시 테스트 데이터
    following_list = [
        {"nickname": "프론트엔드 요정", "is_following": True},
        {"nickname": "알고리즘 장인", "is_following": True},
        {"nickname": "Fullstack 고수", "is_following": True}
    ]

    return render_template(
        'mypage-following.html',
        following_list=following_list,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-follower')
def mypage_follower():

    # 임시 테스트 데이터
    follower_list = [
        {"nickname": "코딩 입문자", "is_following": False},
        {"nickname": "개발 중독자", "is_following": True},
    ]

    return render_template(
        'mypage-follower.html',
        follower_list=follower_list,
        sidebar=SIDEBAR_CONFIG["default"],
        active="mypage",
        current_bg="backgrounds/m.png"
    )


@bp.route('/mypage-message')
def mypage_message():
    current_bg = "backgrounds/m.png"
    return render_template(
    'mypage-message.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage",
    current_bg = current_bg
)

@bp.route('/mypage-point')
def mypage_point():
    current_bg = "backgrounds/m.png"
    return render_template(
    'mypage-point.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage",
    current_bg = current_bg
)

@bp.route('/mypage-alert')
def mypage_alert():
    current_bg = "backgrounds/m.png"
    return render_template(
    'mypage-alert.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage",
    current_bg = current_bg
)

@bp.route('/mypage-withdraw')
def mypage_withdraw():
    current_bg = "backgrounds/m.png"
    return render_template(
    'mypage-withdraw.html',            
    sidebar=SIDEBAR_CONFIG["default"],
    active="mypage",
    current_bg = current_bg
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
    "feed_buttons": ["전체", "아이콘", "배경이미지"]
    }
    return render_template(
    'pointshop.html', 
    show_notice_buttons=True,
    notice_buttons=notice_buttons,
    show_writeBtn=True,
    sidebar=SIDEBAR_CONFIG["pointstore"],
    active="pointstore"
)
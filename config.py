SIDEBAR_CONFIG = {
    "default": {
        "tabs": [
            {"id": "chat", "label": "실시간채팅"},
            {"id": "mypage", "label": "마이페이지"},
        ],
        "lists": {
            "mypage": [
                {"url": "/mypage-posts", "label": "내 글 관리"},
                {"url": "/mypage-interest", "label": "내 관심 그래프"},
                {"url": "/mypage-items", "label": "아이템관리"},
                {"url": "/mypage-info", "label": "정보수정"},
                {"url": "/mypage-following", "label": "팔로우 / 팔로워 관리"},
                {"url": "/mypage-message", "label": "메세지"},
                {"url": "/mypage-point", "label": "포인트"},
                {"url": "/mypage-alert", "label": "알림"},
                {"url": "/mypage-withdraw", "label": "회원탈퇴"},
            ]
        },
        "default_active": "chat",
        "default_panel": "panel-chat",
    },

    "info": {
        "tabs": [
            {"id": "chat", "label": "실시간채팅"},
            {"id": "info", "label": "공지사항"},
        ],
        "lists": {
            "info": [
                {"url": "/info", "label": "공지사항"},
                {"url": "/terms", "label": "이용약관"},
                {"url": "/privacy", "label": "개인정보처리방침"}
            ]
        },
        "default_active": "info",
        "default_panel": "panel-info",
    },

    "pointstore": {
        "tabs": [
            {"id": "chat", "label": "실시간채팅"},
            {"id": "pointstore", "label_line1": "포인트상점", "label_line2": "보유포인트 : 54,000P"},
        ],
        "lists": {
            "pointstore": [
                {"url": "/pointstore", "label": "상품응모 / 당첨자발표"},
                {"url": "/pointshop", "label": "포인트샵"},
                {"url": "/minigame", "label": "미니게임"},
            ]
        },
        "default_active": "pointstore",
        "default_panel": "panel-pointstore",
    },
}

document.addEventListener("DOMContentLoaded", () => {

    /* --------------------------------------
     * 1) 팔로우 / 팔로잉 버튼 토글
     * -------------------------------------- */
    document.querySelectorAll(".follow-toggle").forEach(btn => {
        btn.addEventListener("click", () => {

            const isFollowing = btn.classList.contains("following");
            const targetUserId = btn.dataset.userId;  // 🔥 추가됨

            if (isFollowing) {
                btn.classList.remove("following");
                btn.textContent = "팔로우";
            } else {
                btn.classList.add("following");
                btn.textContent = "팔로잉";
            }

            // 🔥 AJAX 요청 (백엔드 구현 후 활성화)
            fetch("/api/follow-toggle", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target_id: targetUserId,
                    follow: !isFollowing
                })
            });
        });
    });


    /* --------------------------------------
     * 2) 탭 이동 강조 효과
     * -------------------------------------- */
    const path = window.location.pathname;

    const followTab = document.querySelector(".follow-tabs a[href='/mypage-following']");
    const followerTab = document.querySelector(".follow-tabs a[href='/mypage-follower']");

    if (path.includes("following")) {
        followTab.classList.add("active");
        followerTab.classList.remove("active");
    }
    if (path.includes("follower")) {
        followerTab.classList.add("active");
        followTab.classList.remove("active");
    }

});

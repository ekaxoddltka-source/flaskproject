document.addEventListener("DOMContentLoaded", () => {

    /* --------------------------------------
     * 1) 팔로우 / 팔로잉 버튼 토글
     * -------------------------------------- */
    document.querySelectorAll(".follow-toggle").forEach(btn => {
        btn.addEventListener("click", () => {

            const isFollowing = btn.classList.contains("following");

            if (isFollowing) {
                // 현재 팔로잉 → 팔로우로 전환
                btn.classList.remove("following");
                btn.textContent = "팔로우";
            } else {
                // 현재 팔로우 → 팔로잉으로 전환
                btn.classList.add("following");
                btn.textContent = "팔로잉";
            }

            // 나중에 AJAX 추가할 자리
            /*
            fetch("/api/follow", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ target_user: userId, follow: !isFollowing })
            });
            */
        });
    });


    /* --------------------------------------
     * 2) 탭 이동 강조 효과 (현재 페이지 표시)
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

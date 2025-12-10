document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       1) 팔로우 토글 버튼 함수 (중복 바인딩 방지)
    ============================================================ */
    function bindFollowButton(btn) {
        if (btn.dataset.bound === "1") return; // 이미 바인딩됨
        btn.dataset.bound = "1";

        btn.addEventListener("click", async () => {
            const isFollowing = btn.classList.contains("following");
            const targetUserId = btn.dataset.userId;

            // 서버 요청
            const res = await fetch("/api/follow-toggle", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target_id: targetUserId,
                    follow: !isFollowing
                })
            });

            const data = await res.json();
            if (!data.success) return; // 실패 시 UI 변경 안 함

            // 서버 성공 후 UI 변경
            if (isFollowing) {
                btn.classList.remove("following");
                btn.textContent = "팔로우";
            } else {
                btn.classList.add("following");
                btn.textContent = "팔로잉";
            }
        });
    }

    // 기존 버튼들 바인딩
    document.querySelectorAll(".follow-toggle").forEach(bindFollowButton);



    /* ============================================================
       2) 탭 강조
    ============================================================ */
    const path = window.location.pathname;

    const followTab = document.querySelector(".follow-tabs a[href='/mypage-following']");
    const followerTab = document.querySelector(".follow-tabs a[href='/mypage-follower']");

    if (path.includes("following")) followTab?.classList.add("active");
    if (path.includes("follower")) followerTab?.classList.add("active");



    /* ============================================================
       3) 인피니티 스크롤
    ============================================================ */

    const scrollTarget = document.querySelector(".posts");
    const grid = document.querySelector(".follow-grid");

    let page = 1;
    const perPage = 20;
    let loading = false;
    let reachedEnd = false;

    // 현재 페이지 따라 URL 자동 선택
    const loadUrl = path.includes("following")
        ? "/mypage-following/load"
        : "/mypage-follower/load";

    // 📌 중복 추가 방지용 Set
    const existingIds = new Set(
        [...document.querySelectorAll(".follow-card")].map(c => c.dataset.userId)
    );

    async function loadMore() {
        if (loading || reachedEnd) return;
        loading = true;

        try {
            const res = await fetch(`${loadUrl}?page=${page + 1}&per_page=${perPage}`);
            const data = await res.json();

            if (!Array.isArray(data) || data.length === 0) {
                reachedEnd = true;
                return;
            }

            page++;

            data.forEach(user => {
                if (existingIds.has(user.user_id)) return; // 중복 방지

                existingIds.add(user.user_id);

                const html = `
                <div class="follow-card" data-user-id="${user.user_id}">
                    <div class="profile-img">
                        <img src="${user.icon ?? '/mypage/static/icons/default.png'}">
                    </div>

                    <div class="nickname">${user.nickname}</div>

                    <button class="follow-toggle ${user.is_following ? "following" : ""}"
                            data-user-id="${user.user_id}">
                        ${user.is_following ? "팔로잉" : "팔로우"}
                    </button>
                </div>`;

                grid.insertAdjacentHTML("beforeend", html);
            });

            // 새로 추가된 버튼 모두 바인딩
            document.querySelectorAll(".follow-toggle").forEach(bindFollowButton);

        } catch (err) {
            console.error("loadMore error:", err);
        } finally {
            loading = false;
        }
    }


    function onScroll() {
        const top = scrollTarget.scrollTop;
        const height = scrollTarget.clientHeight;
        const total = scrollTarget.scrollHeight;

        // 마지막 200px 근처에서 로드
        if (top + height >= total - 200) {
            loadMore();
        }
    }

    // 스크롤 이벤트
    scrollTarget.addEventListener("scroll", onScroll, { passive: true });

    // 첫 화면에서 스크롤이 부족하면 자동으로 로드
    onScroll();
});

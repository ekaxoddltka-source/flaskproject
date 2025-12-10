document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       1) 정렬 버튼 → 서버 이동
    ===================================================== */
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const sort = btn.dataset.sort;

            const map = {
                newest: "latest",
                oldest: "oldest",
                high: "high",
                low: "low"
            };

            const order = map[sort] || "latest";
            window.location.href = `/mypage-point?order=${order}`;
        });
    });


    /* =====================================================
       2) 인피니티 스크롤
    ===================================================== */

    const scrollTarget = document.querySelector(".posts");
    const tbody = document.querySelector(".point-table tbody");

    let page = 1;
    let loading = false;
    let reachedEnd = false;
    const perPage = 20;

    const order = new URL(window.location.href).searchParams.get("order") || "latest";

    async function loadMore() {
        if (loading || reachedEnd) return;
        loading = true;

        try {
            const res = await fetch(`/mypage-point/load?page=${page + 1}&per_page=${perPage}&order=${order}`);
            const data = await res.json();

            if (!Array.isArray(data) || data.length === 0) {
                reachedEnd = true;
                return;
            }

            page += 1;

            data.forEach(r => {

                // 날짜 포맷 (예: YYYY-MM-DD)
                const dateStr = r.point_created_at.split("T")[0];

                // + 또는 - 붙은 포인트 수량
                const pointAmount = r.point_amount > 0 
                    ? `+${r.point_amount}` 
                    : `${r.point_amount}`;

                // 누적 포인트 포맷
                const remainStr = r.remain_point.toLocaleString() + " P";

                // 활동 링크
                const linkHTML = r.board_no 
                    ? `<a href="/board/${r.board_no}">바로가기</a>`
                    : "-";

                // 상태 (1=사용 / 2=적립)
                const state = r.point_type === 2 ? "적립" : "사용";

                const html = `
                <tr>
                    <td><input type="checkbox" class="point-check"></td>
                    <td>${dateStr}</td>
                    <td>${r.point_reason}</td>
                    <td>${pointAmount}</td>
                    <td class="total-point-cell">${remainStr}</td>
                    <td>${linkHTML}</td>
                    <td>${state}</td>
                </tr>
                `;

                tbody.insertAdjacentHTML("beforeend", html);
            });

        } catch (err) {
            console.error(err);
        } finally {
            loading = false;
        }
    }

    function onScroll() {
        const top = scrollTarget.scrollTop;
        const height = scrollTarget.clientHeight;
        const total = scrollTarget.scrollHeight;

        if (top + height >= total - 100) {
            loadMore();
        }
    }

    scrollTarget.addEventListener("scroll", onScroll, { passive: true });
    onScroll(); // 첫 로딩 시 scrollHeight 작으면 자동 실행
});

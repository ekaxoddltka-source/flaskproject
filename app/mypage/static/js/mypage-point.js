document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       1) 누적 포인트 계산 (테이블에서 직접 계산)
    ===================================================== */
    const rows = document.querySelectorAll(".point-table tbody tr");
    let total = 0;

    rows.forEach(tr => {
        const amountText = tr.children[3].innerText;
        const amount = parseInt(amountText.replace("+", ""), 10);

        total += amount;

        tr.querySelector(".total-point-cell").innerText = total;
    });


    /* =====================================================
       2) 정렬 버튼 → 서버에 요청하여 갱신
    ===================================================== */
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {

            const sort = btn.dataset.sort;

            // sort 이름을 서버에서 사용하는 정렬키로 맞추기
            const map = {
                newest: "latest",
                oldest: "oldest",
                high: "high",
                low: "low"
            };

            const order = map[sort] || "latest";

            // 요청 보내기
            window.location.href = `/mypage-point?order=${order}`;
        });
    });

});

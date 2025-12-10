document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       1) 개별 삭제 버튼 바인딩 (중복 방지)
    ============================================================ */
    function bindDeleteButtons(scope) {
        scope.querySelectorAll(".btn-delete").forEach(btn => {
            if (btn.dataset.bound === "1") return;
            btn.dataset.bound = "1";

            btn.addEventListener("click", async () => {
                const alertNo = btn.dataset.alertNo;
                const row = btn.closest(".alert-item");

                if (!confirm("이 알림을 삭제하시겠습니까?")) return;

                const res = await fetch("/api/alert/delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ alert_no: alertNo })
                });

                const data = await res.json();
                if (data.success) {
                    row.remove();
                }
            });
        });
    }

    bindDeleteButtons(document);



    /* ============================================================
       2) 전체 삭제
    ============================================================ */
    const deleteAllBtn = document.querySelector("#btn-delete-all");

    if (deleteAllBtn) {
        deleteAllBtn.addEventListener("click", async () => {
            if (!confirm("전체 알림을 삭제하시겠습니까?")) return;

            const res = await fetch("/api/alert/delete-all", {
                method: "POST"
            });

            const data = await res.json();
            if (data.success) {
                document.querySelectorAll(".alert-item").forEach(i => i.remove());
            }
        });
    }



    /* ============================================================
       3) 인피니티 스크롤 (.posts 기준)
    ============================================================ */

    const scrollBox = document.querySelector(".posts");
    const tbody = document.querySelector("#alert-table-body");

    let page = 1;
    const perPage = 20;
    let loading = false;
    let reachedEnd = false;


    async function loadMoreAlerts() {
        if (loading || reachedEnd) return;
        loading = true;

        try {
            console.log("[alert] loadMoreAlerts 호출 → page:", page + 1);

            const res = await fetch(`/mypage-alert/load?page=${page + 1}&per_page=${perPage}`);
            const data = await res.json();

            console.log("[alert] 응답:", data);

            if (!Array.isArray(data) || data.length === 0) {
                reachedEnd = true;
                return;
            }

            page++;

            data.forEach(a => {
                const link = a.target_board_no
                    ? `/board/${a.target_board_no}`
                    : (a.target_comment_answer_no ? `/comment/${a.target_comment_answer_no}` : "-");

                const linkHtml = (link !== "-")
                    ? `<a href="${link}" class="alert-link">바로가기</a>`
                    : "-";

                const html = `
                    <tr class="alert-item">
                        <td><input type="checkbox" class="alert-check" data-alert-no="${a.alert_no}"></td>
                        <td>${a.alert_content}</td>
                        <td>${a.alert_type}</td>
                        <td>${a.alerted_at}</td>
                        <td>${linkHtml}</td>
                        <td>
                            <button class="btn-delete" data-alert-no="${a.alert_no}">삭제</button>
                        </td>
                    </tr>
                `;

                tbody.insertAdjacentHTML("beforeend", html);
            });

            bindDeleteButtons(tbody);

        } catch (err) {
            console.error("loadMoreAlerts ERROR:", err);
        } finally {
            loading = false;
        }
    }



    /* ============================================================
       4) 스크롤 감지 (.posts 내부)
    ============================================================ */
    function onScroll() {
        const top = scrollBox.scrollTop;
        const height = scrollBox.clientHeight;
        const full = scrollBox.scrollHeight;

        if (top + height >= full - 200) {
            loadMoreAlerts();
        }
    }

    scrollBox.addEventListener("scroll", onScroll, { passive: true });

    // 첫 화면에서 내용이 부족하면 자동으로 로드
    onScroll();
});

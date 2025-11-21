document.addEventListener("DOMContentLoaded", () => {

    const tbody = document.getElementById("alert-tbody");
    const selectAll = document.getElementById("select-all-notifications");
    const deleteSelectedBtn = document.querySelector(".btn-delete-selected");

    /* -----------------------------------------------------
       0) 더미 데이터 (백엔드 연결 전 테스트용)
       ----------------------------------------------------- */
    const dummyAlerts = [
        {
            id: 1,
            date: "2025-02-01 13:24",
            msg: "누군가 내 게시글에 댓글을 남겼습니다",
            type: "댓글",
            link: "#"
        },
        {
            id: 2,
            date: "2025-02-01 09:10",
            msg: "내 댓글에 답글이 달렸습니다",
            type: "답글",
            link: "#"
        },
        {
            id: 3,
            date: "2025-01-31 22:50",
            msg: "게시글이 추천을 받았습니다",
            type: "추천",
            link: "#"
        }
    ];

    /* -----------------------------------------------------
       1) 알림 내역 렌더링
       ----------------------------------------------------- */
    function loadAlerts() {
        tbody.innerHTML = "";

        dummyAlerts.forEach(alert => {
            const tr = document.createElement("tr");
            tr.dataset.id = alert.id;

            tr.innerHTML = `
                <td><input type="checkbox" class="alert-check"></td>
                <td>${alert.date}</td>
                <td>${alert.msg}</td>
                <td>${alert.type}</td>
                <td><a href="${alert.link}">바로가기</a></td>
                <td><button class="btn-delete-row" style="color:red;">삭제</button></td>
            `;

            tbody.appendChild(tr);
        });

        attachRowEvents();
    }

    loadAlerts();


    /* -----------------------------------------------------
       2) 개별 삭제 버튼
       ----------------------------------------------------- */
    function attachRowEvents() {
        document.querySelectorAll(".btn-delete-row").forEach(btn => {
            btn.addEventListener("click", function () {
                const row = this.closest("tr");
                row.remove();
            });
        });
    }


    /* -----------------------------------------------------
       3) 전체 선택 / 해제
       ----------------------------------------------------- */
    if (selectAll) {
        selectAll.addEventListener("change", () => {
            const checked = selectAll.checked;

            document.querySelectorAll(".alert-check").forEach(chk => {
                chk.checked = checked;
            });
        });
    }


    /* -----------------------------------------------------
       4) 선택 삭제
       ----------------------------------------------------- */
    deleteSelectedBtn.addEventListener("click", () => {
        const checks = document.querySelectorAll(".alert-check:checked");

        if (checks.length === 0) {
            alert("삭제할 알림을 선택하세요.");
            return;
        }

        checks.forEach(chk => {
            chk.closest("tr").remove();
        });

        // 전체 선택 체크박스 초기화
        selectAll.checked = false;
    });

});

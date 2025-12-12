document.addEventListener("DOMContentLoaded", () => {
    // ===========================
    // 1. 탭 메뉴 활성화 및 페이지 이동
    // ===========================
    document.getElementById("goHomeBtn").addEventListener("click", () => {
        window.location.href = "/";
    });
    const tabs = document.querySelectorAll(".tab-btn");
    const path = window.location.pathname;

    tabs.forEach(tab => {
        const target = tab.getAttribute("data-target");

        if (
            (path.includes("admin-users") && target === "tab-users") ||
            (path.includes("admin-report") && target === "tab-reports") ||
            (path.includes("admin-ad") && target === "tab-ads")
        ) {
            tab.classList.add("active");
        } else {
            tab.classList.remove("active");
        }

        tab.addEventListener("click", () => {
            let url = "/";
            switch (target) {
                case "tab-users": url = "/admin-users"; break;
                case "tab-reports": url = "/admin-report"; break;
                case "tab-ads": url = "/admin-ad"; break;
            }
            window.location.href = url;
        });
    });

    // ===========================
    // 2. DOM
    // ===========================
    const reportTableBody = document.getElementById("reportTableBody");
    const searchInput = document.getElementById("searchReportInput");
    const searchBtn = document.getElementById("searchReportBtn");
    const filterStatus = document.getElementById("filterStatusSelect");
    const filterCategory = document.getElementById("filterCategorySelect");
    const bulkResolveBtn = document.getElementById("bulkResolveBtn");
    const bulkDeleteBtn = document.getElementById("bulkDeleteBtn");
    const selectAllCheckbox = document.getElementById("selectAllReports");
    const pagination = document.getElementById("reportPagination");

    // 1. 카테고리 맵 정의 및 select 옵션 채우기
    const categoryMap = {1: "욕설/비방", 2: "스팸/광고", 3: "음란물", 4: "도배"};
    for (const key in categoryMap) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = categoryMap[key];
        filterCategory.appendChild(opt);
    }

    let page = 1;
    const limit = 10;
    let currentReports = [];

    // ===========================
    // 3. 테이블 렌더링
    // ===========================
    function renderTable(reports) {
        reportTableBody.innerHTML = "";
        reports.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><input type="checkbox" class="report-checkbox" data-id="${r.report_no}"></td>
                <td>${r.report_no}</td>
                <td>${r.report_user_id}</td>
                <td><a href="/board/${r.board_no}" target="_blank">${r.board_no}</a></td>
                <td>${r.category_text}</td>
                <td>${r.report_content}</td>
                <td>${r.status_text}</td>
                <td>${r.reported_at}</td>
                <td>${r.report_updated_at}</td>
                <td>
                    ${r.report_status === 1 ? `<button class="report-action-btn" data-action="resolve" data-id="${r.report_no}">처리 완료</button>` : ""}
                    ${r.report_status !== 2 ? `<button class="report-action-btn" data-action="delete" data-id="${r.report_no}">삭제</button>` : ""}
                    ${r.report_status === 2 ? `<button class="report-action-btn" data-action="restore" data-board-no="${r.board_no}">되돌리기</button>` : ""}
                </td>
            `;
            reportTableBody.appendChild(tr);
        });
    }
    
    // ===========================
    // 4. 페이지네이션 렌더링
    // ===========================
    function renderPagination(totalCount) {
        pagination.innerHTML = "";
        const totalPages = Math.ceil(totalCount / limit);
        if (totalPages <= 1) return;

        const groupSize = 10;
        const currentGroup = Math.ceil(page / groupSize);
        const groupStart = (currentGroup - 1) * groupSize + 1;
        let groupEnd = groupStart + groupSize - 1;
        if (groupEnd > totalPages) groupEnd = totalPages;

        if (groupStart > 1) {
            const prevBtn = document.createElement("button");
            prevBtn.textContent = "이전";
            prevBtn.addEventListener("click", () => {
                page = groupStart - 1;
                loadReports();
            });
            pagination.appendChild(prevBtn);
        }

        for (let i = groupStart; i <= groupEnd; i++) {
            const btn = document.createElement("button");
            btn.textContent = i;
            if (i === page) btn.classList.add("active-page");
            btn.addEventListener("click", () => {
                page = i;
                loadReports();
            });
            pagination.appendChild(btn);
        }

        if (groupEnd < totalPages) {
            const nextBtn = document.createElement("button");
            nextBtn.textContent = "다음";
            nextBtn.addEventListener("click", () => {
                page = groupEnd + 1;
                loadReports();
            });
            pagination.appendChild(nextBtn);
        }
    }

    // ===========================
    // 5. 데이터 불러오기
    // ===========================
    function loadReports() {
        const params = new URLSearchParams({
            page: page,
            limit: limit,
            search: searchInput.value,
            status: filterStatus.value,
            category: filterCategory.value
        });

        fetch(`/api/admin-reports?${params.toString()}`)
            .then(res => res.json())
            .then(data => {
                currentReports = data.reports;
                renderTable(currentReports);
                renderPagination(data.total_count);
                selectAllCheckbox.checked = false;
            });
    }

    // ===========================
    // 6. 검색/필터 이벤트
    // ===========================
    searchBtn.addEventListener("click", () => { page = 1; loadReports(); });
    searchInput.addEventListener("keypress", e => { if(e.key === "Enter") { page = 1; loadReports(); } });
    filterStatus.addEventListener("change", () => { page = 1; loadReports(); });
    filterCategory.addEventListener("change", () => { page = 1; loadReports(); });

    // ===========================
    // 7. 개별 처리/삭제 버튼 이벤트
    // ===========================
    reportTableBody.addEventListener("click", e => {
        if (!e.target.classList.contains("report-action-btn")) return;

        const action = e.target.dataset.action;

        if(action === "restore") {
            const boardNo = e.target.dataset.boardNo;
            fetch("/api/admin-reports/restore", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ board_nos: [boardNo] })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) loadReports();
                else alert(data.message || "복구 실패");
            });
            return;
        }

        const id = e.target.dataset.id;

        fetch("/api/admin-reports/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action, ids: [id] })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) loadReports();
            else alert(data.message || "처리 실패");
        });
    });

    // ===========================
    // 8. 일괄 처리
    // ===========================
    bulkResolveBtn.addEventListener("click", () => {
        const selected = [...document.querySelectorAll(".report-checkbox:checked")].map(cb => cb.dataset.id);
        if (selected.length === 0) return alert("선택된 신고가 없습니다.");
        fetch("/api/admin-reports/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "resolve", ids: selected })
        }).then(res => res.json())
          .then(data => { if(data.success) loadReports(); else alert(data.message || "실패"); });
    });

    bulkDeleteBtn.addEventListener("click", () => {
        const selected = [...document.querySelectorAll(".report-checkbox:checked")].map(cb => cb.dataset.id);
        if (selected.length === 0) return alert("선택된 신고가 없습니다.");
        fetch("/api/admin-reports/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "delete", ids: selected })
        }).then(res => res.json())
          .then(data => { if(data.success) loadReports(); else alert(data.message || "실패"); });
    });

    // ===========================
    // 9. 전체 선택 체크박스
    // ===========================
    selectAllCheckbox.addEventListener("change", e => {
        const checked = e.target.checked;
        document.querySelectorAll(".report-checkbox").forEach(cb => cb.checked = checked);
    });

    // ===========================
    // 초기 로딩
    // ===========================
    loadReports();
});

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
    const userTableBody = document.getElementById("userTableBody");
    const totalUsers = document.getElementById("totalUsers");
    const activeUsers = document.getElementById("activeUsers");
    const withdrawUsers = document.getElementById("withdrawUsers");

    const searchInput = document.getElementById("searchUserInput");
    const searchBtn = document.getElementById("searchUserBtn");
    const sortSelect = document.getElementById("sortUserSelect");
    const sortOrderBtn = document.getElementById("sortOrderBtn");

    const selectAllUsers = document.getElementById("selectAllUsers");

    let sortOrder = "ASC";

    // ===========================
    // 선택 유지 저장소
    // ===========================
    let selectedUserIds = new Set();

    // ===========================
    // 3. 헬퍼
    // ===========================
    function formatDate(dateStr) {
        return dateStr || "-";
    }
    function formatNumber(num) {
        return num.toLocaleString();
    }

    // ===========================
    //  페이지네이션 함수
    // ===========================
    let page = 1;
    let limit = 10;

    const pagination = document.getElementById("pagination");

    function renderPagination(totalPages, currentPage) {
        const pagination = document.getElementById("pagination");
        pagination.innerHTML = "";

        if (totalPages <= 1) return;

        const groupSize = 10;
        const currentGroup = Math.ceil(currentPage / groupSize);
        const groupStart = (currentGroup - 1) * groupSize + 1;
        let groupEnd = groupStart + groupSize - 1;
        if (groupEnd > totalPages) groupEnd = totalPages;

        // PREV 버튼
        if (groupStart > 1) {
            const prevBtn = document.createElement("button");
            prevBtn.className = "page-btn";
            prevBtn.textContent = "이전";
            prevBtn.addEventListener("click", () => {
                page = groupStart - 1;
                fetchUsers();
            });
            pagination.appendChild(prevBtn);
        }

        // 페이지 번호
        for (let i = groupStart; i <= groupEnd; i++) {
            const btn = document.createElement("button");
            btn.className = "page-btn";
            btn.textContent = i;

            if (i === currentPage) btn.classList.add("active");

            btn.addEventListener("click", () => {
                page = i;
                fetchUsers();
            });

            pagination.appendChild(btn);
        }

        // NEXT 버튼
        if (groupEnd < totalPages) {
            const nextBtn = document.createElement("button");
            nextBtn.className = "page-btn";
            nextBtn.textContent = "다음";
            nextBtn.addEventListener("click", () => {
                page = groupEnd + 1;
                fetchUsers();
            });
            pagination.appendChild(nextBtn);
        }
    }

    // ===========================
    // 4. 사용자 목록 불러오기
    // ===========================
    function fetchUsers() {
        const search = searchInput.value;
        const sort_by = sortSelect.value || "created_at";

        fetch(`/api/admin-users?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}&sort_by=${sort_by}&sort_order=${sortOrder}`)
            .then(res => res.json())
            .then(data => {
                userTableBody.innerHTML = "";

                data.users.forEach(user => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td><input type="checkbox" class="user-checkbox" value="${user.id}"></td>
                        <td>${user.id}</td>
                        <td>${user.name || ""}</td>
                        <td>${user.nick}</td>
                        <td>${user.email}</td>
                        <td>${formatDate(user.created_at)}</td>
                        <td>${formatDate(user.last_login_at)}</td>
                        <td>
                            <select class="user-role">
                                <option value="1" ${user.user_type == 1 ? "selected" : ""}>관리자</option>
                                <option value="2" ${user.user_type == 2 ? "selected" : ""}>일반회원</option>
                            </select>
                        </td>
                        <td>
                            <select class="user-withdraw">
                                <option value="0" ${user.withdraw == 0 ? "selected" : ""}>활성회원</option>
                                <option value="1" ${user.withdraw == 1 ? "selected" : ""}>탈퇴회원</option>
                            </select>                            
                        </td>
                        <td>${formatDate(user.withdraw_at || "-")}</td>
                        <td><input type="text" class="user-points" value="${user.user_current_point}"> P</td>
                        <td><button data-action="ban">적용</button></td>
                    `;
                    userTableBody.appendChild(row);

                    const checkbox = row.querySelector(".user-checkbox");
                    const roleSelect = row.querySelector(".user-role");
                    const withdrawSelect = row.querySelector(".user-withdraw");
                    const pointsInput = row.querySelector(".user-points");

                    // ⭐ 초기값 저장
                    row.dataset.initialRole = String(user.user_type);
                    row.dataset.initialWithdraw = String(user.withdraw);
                    row.dataset.initialPoints = String(user.user_current_point);

                    // ⭐ 포맷팅된 값으로 표시
                    pointsInput.value = Number(row.dataset.initialPoints).toLocaleString();

                    // ⭐ 변경 감지 통합 함수
                    function updateCheckbox() {
                        const roleCurrent = roleSelect.value;
                        const withdrawCurrent = withdrawSelect.value;

                        const pointsCurrent = pointsInput.value.replace(/,/g, '');
                        const initialPoints = row.dataset.initialPoints;

                        const hasChanged =
                            roleCurrent !== row.dataset.initialRole ||
                            withdrawCurrent !== row.dataset.initialWithdraw ||
                            pointsCurrent !== initialPoints;

                        checkbox.checked = hasChanged;

                        if (hasChanged) {
                            selectedUserIds.add(String(user.id));
                        } else {
                            selectedUserIds.delete(String(user.id));
                        }
                    }

                    // ⭐ 입력 이벤트 / 선택 이벤트 연결
                    roleSelect.addEventListener("change", updateCheckbox);
                    withdrawSelect.addEventListener("change", updateCheckbox);

                    pointsInput.addEventListener("input", () => {
                        let rawValue = pointsInput.value.replace(/,/g, '');
                        if (isNaN(rawValue) || rawValue === "") rawValue = 0;
                        pointsInput.value = Number(rawValue).toLocaleString();
                    });

                    pointsInput.addEventListener("change", updateCheckbox);

                    // ⭐ 체크박스 직접 클릭 시에도 selectedUserIds 반영
                    checkbox.addEventListener("change", () => {
                        if (checkbox.checked) selectedUserIds.add(String(user.id));
                        else selectedUserIds.delete(String(user.id));
                    });

                    // ⭐ 기존 선택 유지
                    if (selectedUserIds.has(String(user.id))) {
                        checkbox.checked = true;
                    }
                });

                renderPagination(Math.ceil(data.total_count / limit), page);

                // ===========================
                // 전체 선택 체크박스 유지
                // ===========================
                const currentCheckboxes = document.querySelectorAll(".user-checkbox");

                if (selectAllUsers.checked) {
                    currentCheckboxes.forEach(cb => {
                        cb.checked = true;
                        selectedUserIds.add(cb.value);
                    });
                }

                // ===========================
                // 통계 업데이트
                // ===========================
                totalUsers.textContent = formatNumber(data.stats.total);
                activeUsers.textContent = formatNumber(data.stats.active);
                withdrawUsers.textContent = formatNumber(data.stats.withdrawn);
            });
    }

    // ===========================
    // 행별 적용 버튼
    // ===========================
    userTableBody.addEventListener("click", (e) => {
        if (!e.target.matches("button[data-action='ban']")) return;

        const row = e.target.closest("tr");
        const userId = row.querySelector(".user-checkbox").value;

        const updateData = extractRowChanges(row, userId);
        if (!updateData) {
            alert("변경된 내용이 없습니다.");
            return;
        }

        sendUpdateRequest([updateData]);
    });

    // ===========================
    // 선택 일괄 적용 버튼
    // ===========================
    document.getElementById("bulkBanBtn").addEventListener("click", () => {
        const rows = document.querySelectorAll("#userTableBody tr");

        let updates = [];

        rows.forEach(row => {
            const checkbox = row.querySelector(".user-checkbox");
            if (!checkbox.checked) return;

            const userId = checkbox.value;
            const updateData = extractRowChanges(row, userId);

            if (updateData) updates.push(updateData);
        });

        if (updates.length === 0) {
            alert("선택된 변경사항이 없습니다.");
            return;
        }

        sendUpdateRequest(updates);
    });

    // ===========================
    // 행에서 변경된 값만 추출
    // ===========================
    function extractRowChanges(row, userId) {
        const roleSelect = row.querySelector(".user-role");
        const withdrawSelect = row.querySelector(".user-withdraw");
        const pointsInput = row.querySelector(".user-points");

        const initialRole = row.dataset.initialRole;
        const initialWithdraw = row.dataset.initialWithdraw;
        const initialPoints = row.dataset.initialPoints;

        const roleCurrent = roleSelect.value;
        const withdrawCurrent = withdrawSelect.value;
        const pointsCurrent = pointsInput.value.replace(/,/g, '');

        let changed = false;
        let update = { id: userId };

        if (roleCurrent !== initialRole) {
            update.user_type = Number(roleCurrent);
            changed = true;
        }
        if (withdrawCurrent !== initialWithdraw) {
            update.withdraw = Number(withdrawCurrent);
            changed = true;
        }
        if (pointsCurrent !== initialPoints) {
            update.points = Number(pointsCurrent);
            changed = true;
        }

        return changed ? update : null;
    }

    // ===========================
    // API 요청 함수 (통합)
    // ===========================
    function sendUpdateRequest(updates) {
        fetch("/api/admin-users/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ updates })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("적용되었습니다.");
                    fetchUsers();
                } else {
                    alert("업데이트 실패: " + data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert("서버 오류 발생");
            });
    }

    // ===========================
    // 8. 정렬
    // ===========================
    sortOrderBtn.addEventListener("click", () => {
        sortOrder = sortOrder === "ASC" ? "DESC" : "ASC";
        sortOrderBtn.textContent = sortOrder === "ASC" ? "내림차순" : "오름차순";
        page = 1;
        fetchUsers();
    });

    // ===========================
    // 9. 검색
    // ===========================
    searchBtn.addEventListener("click", () => {
        page = 1; 
        fetchUsers();
    });
    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            page = 1;  
            fetchUsers();
        }
    });

    // ===========================
    // 10. 전체 선택 체크박스
    // ===========================
    selectAllUsers.addEventListener("change", () => {
        const checked = selectAllUsers.checked;
        const userCheckboxes = document.querySelectorAll(".user-checkbox");

        userCheckboxes.forEach(cb => {
            cb.checked = checked;
            if (checked) selectedUserIds.add(cb.value);
            else selectedUserIds.delete(cb.value);
        });
    });

    // 초기 로딩
    fetchUsers();
});

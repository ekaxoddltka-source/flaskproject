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
    // 2. 사용자 검색 및 정렬 옵션 DOM 접근
    // ===========================
    const userTableBody = document.getElementById("userTableBody");
    const totalUsers = document.getElementById("totalUsers");
    const activeUsers = document.getElementById("activeUsers");
    const withdrawUsers = document.getElementById("withdrawUsers");

    const searchInput = document.getElementById("searchUserInput");
    const searchBtn = document.getElementById("searchUserBtn");
    const sortSelect = document.getElementById("sortUserSelect");
    const sortOrderBtn = document.getElementById("sortOrderBtn");

    let sortOrder = "ASC";
    // ===========================
    // 3. 날짜와 숫자 포맷 헬퍼 함수
    // ===========================
    function formatDate(dateStr) {
        return dateStr || "-";
    }

    function formatNumber(num) {
        return num.toLocaleString();
    }
    // ===========================
    // 4. API로 사용자 데이터 가져오기
    // ===========================
    function fetchUsers() {
        const search = searchInput.value;
        const sort_by = sortSelect.value || "created_at";

        fetch(`/api/admin-users?search=${encodeURIComponent(search)}&sort_by=${sort_by}&sort_order=${sortOrder}`)
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
                        <td>
                            <button data-action="ban">적용</button>
                        </td>
                    `;
                    userTableBody.appendChild(row);

                    // ===========================
                    // 5. 유저 타입 셀렉트 변경 감지
                    // ===========================
                    const roleSelect = row.querySelector(".user-role");
                    roleSelect.addEventListener("change", () => {
                        const newRole = roleSelect.value;
                        console.log(`유저 ${user.id} 권한 변경: ${newRole}`);
                        // TODO: API 호출
                    });

                    // ===========================
                    // 6. 포인트 입력 → 3자리 쉼표 표시 + 변경 감지
                    // ===========================
                    const pointsInput = row.querySelector(".user-points");

                    // 초기 값 표시
                    pointsInput.value = user.user_current_point.toLocaleString();

                    // 입력 시 ',' 제거하고 숫자로 저장
                    pointsInput.addEventListener("input", () => {
                        // 입력값에서 , 제거
                        let rawValue = pointsInput.value.replace(/,/g, '');
                        if (isNaN(rawValue) || rawValue === "") rawValue = 0;

                        // 화면에는 3자리마다 , 표시
                        pointsInput.value = parseInt(rawValue).toLocaleString();
                    });

                    // 변경 완료 후 API 전송
                    pointsInput.addEventListener("change", () => {
                        const newPoints = parseInt(pointsInput.value.replace(/,/g, '')) || 0;
                        console.log(`유저 ${user.id} 포인트 변경: ${newPoints}`);
                        // TODO: API 호출
                    });
                });

                // ===========================
                // 7. 사용자 통계 업데이트
                // ===========================
                totalUsers.textContent = formatNumber(data.stats.total);
                activeUsers.textContent = formatNumber(data.stats.active);
                withdrawUsers.textContent = formatNumber(data.stats.withdrawn);
            });
    }
    // ===========================
    // 8. 정렬 버튼 클릭 시 오름/내림차순 토글
    // ===========================
    sortOrderBtn.addEventListener("click", () => {
        sortOrder = sortOrder === "ASC" ? "DESC" : "ASC";
        sortOrderBtn.textContent = sortOrder === "ASC" ? "내림차순" : "오름차순";
        fetchUsers();
    });

    // ===========================
    // 9. 검색 버튼 이벤트
    // ===========================
    searchBtn.addEventListener("click", fetchUsers);
    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") fetchUsers();
    });

    // 초기 로딩
    fetchUsers();
});

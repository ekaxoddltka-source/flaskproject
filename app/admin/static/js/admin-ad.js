document.addEventListener("DOMContentLoaded", () => {

    // ===============================
    // 탭 및 초기 로드
    // ===============================

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

    let page = 1;
    const limit = 10;
    function renderPagination(totalCount) {
        const pagination = document.getElementById("adPagination");
        pagination.innerHTML = "";

        const totalPages = Math.ceil(totalCount / limit);
        if (totalPages <= 1) return;

        const groupSize = 10;
        const currentGroup = Math.ceil(page / groupSize);
        const groupStart = (currentGroup - 1) * groupSize + 1;
        let groupEnd = groupStart + groupSize - 1;
        if (groupEnd > totalPages) groupEnd = totalPages;

        if (page > 1) {
            const firstBtn = document.createElement("button");
            firstBtn.textContent = "≪";
            firstBtn.addEventListener("click", () => {
                page = 1;
                loadAds();
            });
            pagination.appendChild(firstBtn);
        }

        if (groupStart > 1) {
            const prevBtn = document.createElement("button");
            prevBtn.textContent = "이전";
            prevBtn.addEventListener("click", () => {
                page = groupStart - 1;
                loadAds();
            });
            pagination.appendChild(prevBtn);
        }

        for (let i = groupStart; i <= groupEnd; i++) {
            const btn = document.createElement("button");
            btn.textContent = i;
            if (i === page) btn.classList.add("active-page");
            btn.addEventListener("click", () => {
                page = i;
                loadAds();
            });
            pagination.appendChild(btn);
        }

        if (groupEnd < totalPages) {
            const nextBtn = document.createElement("button");
            nextBtn.textContent = "다음";
            nextBtn.addEventListener("click", () => {
                page = groupEnd + 1;
                loadAds();
            });
            pagination.appendChild(nextBtn);
        }

        if (page < totalPages) {
            const lastBtn = document.createElement("button");
            lastBtn.textContent = "≫";
            lastBtn.addEventListener("click", () => {
                page = totalPages;
                loadAds();
            });
            pagination.appendChild(lastBtn);
        }
    }

    document.getElementById("searchAdBtn").addEventListener("click", () => {
        page = 1;
        loadAds();
    });
    document.getElementById("searchAdInput").addEventListener("keyup", e => {
        if (e.key === "Enter") {
            page = 1;
            loadAds();
        }
    });
    document.getElementById("filterCategorySelect").addEventListener("change", () => {
        page = 1;
        loadAds();
    });
    document.getElementById("filterActiveSelect").addEventListener("change", () => {
        page = 1;
        loadAds();
    });
    document.getElementById("sortBySelect").addEventListener("change", () => {
        page = 1;
        loadAds();
    });
    document.getElementById("sortOrderSelect").addEventListener("change", () => {
        page = 1;
        loadAds();
    });

    // 일괄 처리
    document.getElementById("bulkActivateBtn").addEventListener("click", () => bulkAction("activate"));
    document.getElementById("bulkDeactivateBtn").addEventListener("click", () => bulkAction("deactivate"));
    document.getElementById("bulkDeleteBtn").addEventListener("click", () => bulkAction("delete"));

    // ===============================
    // 광고 목록
    // ===============================

    function loadAds() {
        const search = document.getElementById("searchAdInput").value;
        const category = document.getElementById("filterCategorySelect").value;
        const active = document.getElementById("filterActiveSelect").value;

        const sortBy = document.getElementById("sortBySelect").value;
        const sortOrder = document.getElementById("sortOrderSelect").value;

        const url =
                `/api/admin-ad?search=${search}&category=${category}&active=${active}` +
                `&sort_by=${sortBy}&sort_order=${sortOrder}&page=${page}&limit=${limit}`;

            fetch(url)
                .then(res => res.json())
                .then(data => {

                    const ads = data.ads;
                    const tbody = document.getElementById("adTableBody");
                    tbody.innerHTML = "";

                ads.forEach(ad => {

                    // 제목/키워드/설명 길이 제한
                    const titleShort = ad.ad_title.length > 15
                        ? ad.ad_title.slice(0, 15) + "..."
                        : ad.ad_title;

                    const keywordsShort = ad.ad_keywords && ad.ad_keywords.length > 15
                        ? ad.ad_keywords.slice(0, 15) + "..."
                        : (ad.ad_keywords || "");

                    const descShort = ad.description && ad.description.length > 15
                        ? ad.description.slice(0, 15) + "..."
                        : (ad.description || "");

                    // 카테고리 변환
                    const categoryMap = {
                        0: "강의",
                        1: "서적",
                        2: "구인",
                        3: "쇼핑"
                    };

                    const catLabel = categoryMap[ad.ad_category] || ad.ad_category;

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><input type="checkbox" class="ad-checkbox" data-id="${ad.ad_id}"></td>
                        <td>${ad.ad_id}</td>
                        <td>${titleShort}</td>
                        <td>${descShort}</td>
                        <td>${catLabel}</td>
                        <td>${ad.ad_priority}</td>
                        <td>${keywordsShort}</td>
                        <td><a href="${ad.landing_url}" target="_blank">이동</a></td>
                        <td>${ad.is_active ? '활성' : '비활성'}</td>
                        <td>${ad.created_at}</td>
                        <td>${ad.updated_at}</td>
                        <td>${ad.views}</td>
                        <td>${ad.clicks}</td>
                        <td>
                            <button class="ad-action-btn" data-action="edit" data-id="${ad.ad_id}">수정</button>
                            <button class="ad-action-btn" data-action="delete" data-id="${ad.ad_id}">삭제</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                    tr.querySelector('[data-action="edit"]')
                        .addEventListener("click", () => openEditModal(ad.ad_id));
                    tr.querySelector('[data-action="delete"]')
                        .addEventListener("click", () => deleteAd(ad.ad_id));
                });
                renderPagination(data.total_count);
            });
    }

    // ===============================
    // 개별 삭제
    // ===============================

    function deleteAd(id) {
        if (!confirm("정말 삭제할까요?")) return;

        fetch("/api/admin-ad/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ad_id: id })
        })
            .then(res => res.json())
            .then(() => loadAds());
    }

    // ===============================
    // 일괄 처리
    // ===============================

    function bulkAction(action) {
        const selected = [...document.querySelectorAll(".ad-checkbox:checked")].map(cb => cb.dataset.id);

        if (selected.length === 0) {
            alert("선택된 광고가 없습니다.");
            return;
        }

        // 액션별 확인 메시지
        const actionMessageMap = {
            "activate": "정말 활성화 하시겠습니까?",
            "deactivate": "정말 비활성화 하시겠습니까?",
            "delete": "정말 삭제하시겠습니까?"
        };

        const confirmMessage = actionMessageMap[action] || "정말 처리하시겠습니까?";

        if (!confirm(confirmMessage)) return;

        fetch("/api/admin-ad/bulk", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action, ids: selected })
        })
            .then(res => res.json())
            .then(() => loadAds());
    }

    function openEditModal(adId) {
        fetch(`/api/admin-ad/${adId}`)
            .then(res => res.json())
            .then(data => {
                const ad = data.ad;

                document.getElementById("editAdId").value = ad.ad_id;
                document.getElementById("editAdTitle").value = ad.ad_title;
                document.getElementById("editAdDesc").value = ad.description || "";
                document.getElementById("editAdKeywords").value = ad.ad_keywords || "";
                document.getElementById("editAdCategory").value = ad.ad_category;
                document.getElementById("editAdPriority").value = ad.ad_priority;
                document.getElementById("editAdUrl").value = ad.landing_url;

                document.getElementById("editAdModal").style.display = "block";
            });
    }
    document.getElementById("saveAdBtn").addEventListener("click", () => {
        const adId = document.getElementById("editAdId").value;

        const updatedData = {
            ad_id: adId,
            ad_title: document.getElementById("editAdTitle").value,
            description: document.getElementById("editAdDesc").value,
            ad_keywords: document.getElementById("editAdKeywords").value,
            ad_category: document.getElementById("editAdCategory").value,
            ad_priority: document.getElementById("editAdPriority").value,
            landing_url: document.getElementById("editAdUrl").value
        };

        fetch("/api/admin-ad/update", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(updatedData)
        })
            .then(res => res.json())
            .then(() => {
                alert("수정되었습니다.");
                document.getElementById("editAdModal").style.display = "none";
                loadAds();
            });
    });
    document.getElementById("closeEditModal").addEventListener("click", () => {
        document.getElementById("editAdModal").style.display = "none";
    });
    loadAds();   // ← 반드시 필요!!
});

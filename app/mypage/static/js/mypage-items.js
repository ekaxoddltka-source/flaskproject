document.addEventListener("DOMContentLoaded", () => {

    /* --------------------------------------------------- */
    /* ELEMENTS */
    /* --------------------------------------------------- */
    const scrollTarget = document.querySelector(".posts");   // ← 무한스크롤의 핵심 수정
    const itemGrid = document.querySelector(".item-grid");

    /* --------------------------------------------------- */
    /* 1) 필터 */
    /* --------------------------------------------------- */
    const filterBtns = document.querySelectorAll(".filter-btn");

    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const type = btn.dataset.type;

            document.querySelectorAll(".item-card").forEach(card => {
                if (type === "all" || card.dataset.type === type) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        });
    });

    /* --------------------------------------------------- */
    /* 2) 장착 / 해제 이벤트 */
    /* --------------------------------------------------- */

    function attachUnequipEvent(btn) {
        btn.onclick = async () => {
            const itemNo = btn.dataset.id;
            const card = btn.closest(".item-card");

            const ok = await unequipItem(itemNo);
            if (!ok) return;

            updateUI_Unequip(card);
        };
    }

    function bindEquipButtons(scope) {
        scope.querySelectorAll(".equip").forEach(btn => {
            btn.onclick = async () => {
                const card = btn.closest(".item-card");
                const itemType = card.dataset.type;
                const itemNo = btn.dataset.id;

                const ok = await equipItem(itemNo);
                if (!ok) return;

                // 같은 타입 다른 카드들 해제
                document.querySelectorAll(`.item-card[data-type="${itemType}"]`)
                    .forEach(c => updateUI_Unequip(c));

                updateUI_Equip(card);
            };
        });

        scope.querySelectorAll(".unequip").forEach(btn => attachUnequipEvent(btn));
    }

    bindEquipButtons(document);

    /* --------------------------------------------------- */
    /* 3) UI 업데이트 */
    /* --------------------------------------------------- */

    function updateUI_Equip(card) {
        const equipBtn = card.querySelector(".equip");
        if (!equipBtn) return;

        equipBtn.classList.add("active");
        equipBtn.textContent = "장착됨";

        let un = card.querySelector(".unequip");
        if (un) un.remove();

        const newUn = document.createElement("button");
        newUn.className = "btn unequip";
        newUn.dataset.id = equipBtn.dataset.id;
        newUn.textContent = "해제";

        card.querySelector(".item-actions").appendChild(newUn);
        attachUnequipEvent(newUn);
    }

    function updateUI_Unequip(card) {
        const equipBtn = card.querySelector(".equip");
        const un = card.querySelector(".unequip");

        if (equipBtn) {
            equipBtn.classList.remove("active");
            equipBtn.textContent = "장착";
        }
        if (un) un.remove();
    }

    /* --------------------------------------------------- */
    /* 4) API */
    /* --------------------------------------------------- */

    async function equipItem(item_no) {
        try {
            const res = await fetch("/api/mypage/item/equip", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ item_no })
            });

            const data = await res.json();
            if (!data.success) return false;

            // 배경 즉시 적용
            if (data.item_type === "background" && data.item_img) {
                document.body.style.setProperty(
                    "--dynamic-bg",
                    `url('/mypage/static/${data.item_img}')`
                );
            }

            return true;

        } catch (err) {
            console.error(err);
            return false;
        }
    }

    async function unequipItem(item_no) {
        try {
            const res = await fetch("/api/mypage/item/unequip", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ item_no })
            });

            const data = await res.json();
            if (!data.success) return false;

            if (data.item_type === "background") {
                document.body.style.removeProperty("--dynamic-bg");
            }

            return true;

        } catch (err) {
            console.error(err);
            return false;
        }
    }

    /* --------------------------------------------------- */
    /* 5) 인피니티 스크롤 */
    /* --------------------------------------------------- */

    let page = 1;
    const perPage = 12;
    let loading = false;
    let reachedEnd = false;

    async function loadMoreItems() {
        if (loading || reachedEnd) return;
        loading = true;

        try {
            const res = await fetch(`/mypage-items/load?page=${page + 1}&per_page=${perPage}`);
            if (!res.ok) throw new Error("network error");

            const data = await res.json();

            if (!Array.isArray(data) || data.length === 0) {
                reachedEnd = true;
                return;
            }

            page += 1;

            data.forEach(item => {
                const html = `
                <div class="item-card" data-type="${item.item_type}">
                    <div class="item-img">
                        <img src="${item.item_img_url}">
                    </div>
                    <div class="item-info">
                        <span class="item-name">${item.item_name}</span>
                        <span class="item-desc">${item.item_type}</span>
                    </div>
                    <div class="item-actions">
                        ${
                            item.is_equipped
                            ? `<button class="btn equip active" data-id="${item.item_no}">장착됨</button>
                               <button class="btn unequip" data-id="${item.item_no}">해제</button>`
                            : `<button class="btn equip" data-id="${item.item_no}">장착</button>`
                        }
                    </div>
                </div>`;

                itemGrid.insertAdjacentHTML("beforeend", html);
            });

            bindEquipButtons(itemGrid);

        } catch (err) {
            console.error("loadMoreItems error:", err);
        } finally {
            loading = false;
        }
    }

    function onPostsScroll() {
        const scrollTop = scrollTarget.scrollTop;
        const clientHeight = scrollTarget.clientHeight;
        const scrollHeight = scrollTarget.scrollHeight;

        // 아래 150px 근처에서 호출
        if (scrollTop + clientHeight >= scrollHeight - 150) {
            loadMoreItems();
        }
    }

    scrollTarget.addEventListener("scroll", onPostsScroll, { passive: true });

    // 스크롤바가 없을 때도 자동으로 두 번째 페이지 로드 시도
    onPostsScroll();
});

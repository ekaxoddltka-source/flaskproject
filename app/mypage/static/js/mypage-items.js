// app/mypage/static/js/mypage-items.js

document.addEventListener("DOMContentLoaded", () => {

    /* --------------------------------------------------- */
    /* 1) 필터 */
    /* --------------------------------------------------- */
    const filterBtns = document.querySelectorAll(".filter-btn");
    const itemCards = document.querySelectorAll(".item-card");

    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const type = btn.dataset.type;

            itemCards.forEach(card => {
                if (type === "all" || card.dataset.type === type) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        });
    });

    /* --------------------------------------------------- */
    /* 2) 장착 / 해제 */
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

    document.querySelectorAll(".equip").forEach(btn => {
        btn.onclick = async () => {
            const card = btn.closest(".item-card");
            const itemType = card.dataset.type;
            const itemNo = btn.dataset.id;

            const ok = await equipItem(itemNo);
            if (!ok) return;

            // 같은 타입 전체 해제
            document.querySelectorAll(`.item-card[data-type="${itemType}"]`)
                .forEach(c => updateUI_Unequip(c));

            // 장착
            updateUI_Equip(card);
        };
    });

    document.querySelectorAll(".unequip").forEach(btn => attachUnequipEvent(btn));

    /* --------------------------------------------------- */
    /* 3) UI 업데이트 */
    /* --------------------------------------------------- */
    function updateUI_Equip(card) {
        const equipBtn = card.querySelector(".equip");
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
            if (data.item_type === "background") {
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

});

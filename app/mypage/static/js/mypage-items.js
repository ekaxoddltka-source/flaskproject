document.addEventListener("DOMContentLoaded", () => {

    /* ---------------------------
     * 1) 필터 기능
     * ---------------------------*/
    const filterBtns = document.querySelectorAll(".filter-btn");
    const itemCards = document.querySelectorAll(".item-card");

    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            // 버튼 active 변경
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

    /* ---------------------------
     * 2) 장착 기능
     * ---------------------------*/

    function unequipButtonEvent(btn) {
        btn.addEventListener("click", () => {
            const card = btn.closest(".item-card");
            const equipBtn = card.querySelector(".equip");

            // 해제 동작
            equipBtn.classList.remove("active");
            equipBtn.textContent = "장착";

            // 해제 버튼 삭제
            btn.remove();
        });
    }

    // 장착 버튼
    document.querySelectorAll(".equip").forEach(button => {
        button.addEventListener("click", () => {

            const itemType = button.closest(".item-card").dataset.type;

            // 같은 type 의 기존 active 모두 해제
            document.querySelectorAll(`.item-card[data-type="${itemType}"] .equip.active`)
                .forEach(btn => {
                    btn.classList.remove("active");
                    btn.textContent = "장착";

                    let removeBtn = btn.closest(".item-card").querySelector(".unequip");
                    if (removeBtn) removeBtn.remove();
                });

            // 현재 아이템 장착 처리
            button.classList.add("active");
            button.textContent = "장착됨";

            // 해제 버튼 자동 생성
            let itemCard = button.closest(".item-card");
            let unequipBtn = itemCard.querySelector(".unequip");
            if (!unequipBtn) {
                unequipBtn = document.createElement("button");
                unequipBtn.classList.add("btn", "unequip");
                unequipBtn.textContent = "해제";
                unequipBtn.dataset.id = button.dataset.id;
                itemCard.querySelector(".item-actions").appendChild(unequipBtn);

                unequipButtonEvent(unequipBtn);
            }
        });
    });

    // 기존 해제 버튼들
    document.querySelectorAll(".unequip").forEach(b => unequipButtonEvent(b));
});

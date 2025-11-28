document.addEventListener("DOMContentLoaded", () => {

    // 현재 포인트 라벨
    const pointLabel = document.querySelector("#current-point");

    // ================================
    // 1) 아이템 구매 처리
    // ================================
    document.querySelectorAll(".buy-btn").forEach(btn => {

        btn.addEventListener("click", () => {
            const itemNo = btn.dataset.id;

            if (!confirm("이 아이템을 구매하시겠습니까?")) return;

            fetch("/api/mypage/item/buy", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ item_no: itemNo })
            })
            .then(res => res.json())
            .then(data => {

                if (!data.success) {
                    alert(data.msg || "구매 실패");
                    return;
                }

                alert("구매 완료!");

                // ● 포인트 즉시 차감 업데이트
                if (pointLabel && data.new_point !== undefined) {
                    pointLabel.textContent = data.new_point.toLocaleString();
                }

                // ● 카드 “보유중” 상태로 변경
                const card = btn.closest(".item-card-shop");
                card.classList.add("owned");

                btn.disabled = true;
                btn.textContent = "보유중";
                btn.classList.remove("buy-btn");
                btn.classList.add("owned-btn");
            });
        });
    });


    // ================================
    // 2) 필터 기능 (전체 / 아이콘 / 배경이미지)
    // ================================
    document.querySelectorAll(".filter-btn").forEach(btn => {

        btn.addEventListener("click", () => {

            // 버튼 active 변경
            document.querySelectorAll(".filter-btn")
                .forEach(b => b.classList.remove("active"));

            btn.classList.add("active");

            const type = btn.dataset.type;  // all / icon / background

            // 모든 상품 카드
            document.querySelectorAll(".item-card-shop").forEach(card => {
                const cardType = card.dataset.type;

                if (type === "all" || type === cardType) {
                    card.style.display = "flex";
                } else {
                    card.style.display = "none";
                }
            });
        });
    });

});

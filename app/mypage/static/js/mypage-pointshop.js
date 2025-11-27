document.addEventListener("DOMContentLoaded", () => {

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
                if (data.success) {
                    alert("구매 완료!");
                } else {
                    alert(data.msg || "구매 실패");
                }
            });
        });
    });

});

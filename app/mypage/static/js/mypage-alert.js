document.addEventListener("DOMContentLoaded", () => {

    // 개별 삭제
    document.querySelectorAll(".btn-delete").forEach(btn => {
        btn.addEventListener("click", async () => {
            const item = btn.closest(".alert-item");
            const no = item.dataset.no;

            if (!confirm("이 알림을 삭제하시겠습니까?")) return;

            const res = await fetch("/api/alert/delete", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ alert_no: no })
            });

            const data = await res.json();
            if (data.success) {
                item.remove();
            }
        });
    });

    // 전체 삭제
    const deleteAllBtn = document.querySelector(".btn-delete-all");
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener("click", async () => {
            if (!confirm("전체 알림을 삭제하시겠습니까?")) return;

            const res = await fetch("/api/alert/delete-all", {
                method: "POST"
            });

            const data = await res.json();
            if (data.success) {
                document.querySelectorAll(".alert-item").forEach(i => i.remove());
            }
        });
    }

});

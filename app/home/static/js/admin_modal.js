document.addEventListener("DOMContentLoaded", () => {
// ===========================
// 1. 관리자 모달 호출
// ===========================
    const btnAdminModal = document.getElementById("btnAdminModal");
    const adminModal = document.getElementById("adminModal");

    btnAdminModal.addEventListener("click", function() {
        fetch("/admin/modal")  // Flask에서 렌더링해줄 라우트
            .then(response => response.text())
            .then(html => {
                adminModal.innerHTML = html;
                adminModal.style.display = "block";

                // 모달 닫기
                const closeBtn = adminModal.querySelector("#closeModal");
                closeBtn.addEventListener("click", () => {
                    adminModal.style.display = "none";
                });
            });
    });

    // 모달 외부 클릭 시 닫기
    window.addEventListener("click", function(e) {
        if (e.target === adminModal) {
            adminModal.style.display = "none";
        }
    });







});
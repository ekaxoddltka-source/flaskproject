document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("goHomeBtn").addEventListener("click", () => {
        window.location.href = "/";
    });
    const tabs = document.querySelectorAll(".tab-btn");

    // 현재 URL 기준으로 활성화 탭 설정
    const path = window.location.pathname;

    tabs.forEach(tab => {
        const target = tab.getAttribute("data-target");

        // URL 패턴에 따라 활성화 탭 결정
        if (
            (path.includes("admin-users") && target === "tab-users") ||
            (path.includes("admin-report") && target === "tab-reports") ||
            (path.includes("admin-ad") && target === "tab-ads")
        ) {
            tab.classList.add("active");
        } else {
            tab.classList.remove("active");
        }

        // 클릭 시 해당 URL로 이동
        tab.addEventListener("click", () => {
            let url = "/";
            switch (target) {
                case "tab-users":
                    url = "/admin-users";
                    break;
                case "tab-reports":
                    url = "/admin-report";
                    break;
                case "tab-ads":
                    url = "/admin-ad";
                    break;
            }
            window.location.href = url;
        });
    });
});
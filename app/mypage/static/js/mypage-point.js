document.addEventListener("DOMContentLoaded", () => {

    const sortBtns = document.querySelectorAll(".filter-btn");
    const tableBody = document.querySelector(".point-table tbody");

    // 정렬 버튼 클릭 처리
    sortBtns.forEach(btn => {
        btn.addEventListener("click", () => {

            // 버튼 active 스타일 조정
            sortBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const sortType = btn.dataset.sort;
            sortTable(sortType);
        });
    });

    // 정렬 함수 구현
    function sortTable(type) {
        const rows = Array.from(tableBody.querySelectorAll("tr"));

        rows.sort((a, b) => {
            const dateA = new Date(a.children[1].textContent.trim());
            const dateB = new Date(b.children[1].textContent.trim());

            const pointA = parseInt(a.children[3].textContent.replace("+","").replace("-",""));
            const pointB = parseInt(b.children[3].textContent.replace("+","").replace("-",""));

            switch(type) {

                case "newest":
                    return dateB - dateA; // 최근 날짜 우선

                case "oldest":
                    return dateA - dateB; // 오래된 날짜 우선

                case "high":
                    return pointB - pointA; // 포인트 큰 값 우선

                case "low":
                    return pointA - pointB; // 포인트 작은 값 우선
            }
        });

        // 정렬된 줄 다시 넣기
        rows.forEach(r => tableBody.appendChild(r));
    }

});

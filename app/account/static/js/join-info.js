// join-info.js
document.addEventListener("DOMContentLoaded", () => {
    const createTag = (container, name, val) => {
        // 중복 체크
        const exists = Array.from(container.querySelectorAll("input")).some(input => input.value === val);
        if (exists) return;

        const label = document.createElement("label");
        label.classList.add("tag");
        label.innerHTML = `<input type="checkbox" name="${name}" value="${val}" checked> <span>${val}</span>`;

        // 삭제 버튼 기능 추가 (선택 시 클릭으로 삭제)
        label.addEventListener("click", (e) => {
            // 체크박스 클릭시 이벤트 버블 방지
            if (e.target.tagName !== "SPAN") return;
            container.removeChild(label);
        });

        container.appendChild(label);
    };

    // 관심분야 입력
    const interestInput = document.getElementById("interest-input");
    const interestTags = document.getElementById("interest-tags");

    interestInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const val = interestInput.value.trim();
            if (!val) return;
            createTag(interestTags, "interests", val);
            interestInput.value = "";
        }
    });

    // 보유 기술 입력
    const skillInput = document.getElementById("skill-input");
    const skillTags = document.getElementById("skill-tags");

    skillInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const val = skillInput.value.trim();
            if (!val) return;
            createTag(skillTags, "skills", val);
            skillInput.value = "";
        }
    });
});

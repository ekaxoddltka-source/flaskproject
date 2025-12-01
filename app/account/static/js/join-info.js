document.addEventListener("DOMContentLoaded", () => {
    const showMessage = (el, msg, ok=true) => {
        el.textContent = msg;
        el.style.color = ok ? "green" : "red";
    };

    const createTag = (container, name, val) => {
        if (!val) return;
        const exists = Array.from(container.querySelectorAll("input")).some(i => i.value === val);
        if (exists) return;

        const label = document.createElement("label");
        label.classList.add("tag");
        label.innerHTML = `<input type="checkbox" name="${name}" value="${val}" checked> <span>${val}</span>`;
        label.addEventListener("click", e => { if (e.target.tagName === "SPAN") container.removeChild(label); });
        container.appendChild(label);
    };

    // 태그 입력
    const interestInput = document.getElementById("interest-input");
    const interestTags = document.getElementById("interest-tags");
    interestInput.addEventListener("keypress", e => { if (e.key==="Enter"){e.preventDefault();createTag(interestTags,"interests",interestInput.value.trim());interestInput.value="";}});

    const skillInput = document.getElementById("skill-input");
    const skillTags = document.getElementById("skill-tags");
    skillInput.addEventListener("keypress", e => { if (e.key==="Enter"){e.preventDefault();createTag(skillTags,"skills",skillInput.value.trim());skillInput.value="";}});

    // 중복 체크
    const checkDuplicate = (fieldId, fieldName, msgId) => {
        const input = document.getElementById(fieldId);
        const msgEl = document.getElementById(msgId);
        input.addEventListener("input", () => {
            const val = input.value.trim();
            if(!val){msgEl.textContent="";return;}
            fetch("/check-duplicate",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:`field=${fieldName}&value=${encodeURIComponent(val)}`})
            .then(res=>res.json())
            .then(data=>showMessage(msgEl,data.message,data.status==="ok"))
            .catch(()=>showMessage(msgEl,"체크 중 오류 발생",false));
        });
    };
    checkDuplicate("userid","userid","userid-msg");
    checkDuplicate("nickname","nickname","nickname-msg");
    checkDuplicate("email","email","email-msg");

    // 비밀번호 일치 체크
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm-password");
    const pwMsg = document.createElement("div");
    confirmInput.parentNode.insertBefore(pwMsg, confirmInput.nextSibling);
    const checkPasswordMatch = () => {
        if(!confirmInput.value){pwMsg.textContent="";return;}
        showMessage(pwMsg, passwordInput.value===confirmInput.value ? "비밀번호가 일치합니다." : "비밀번호가 일치하지 않습니다.", passwordInput.value===confirmInput.value);
    };
    passwordInput.addEventListener("input", checkPasswordMatch);
    confirmInput.addEventListener("input", checkPasswordMatch);
});

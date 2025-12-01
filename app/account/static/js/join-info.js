document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.querySelector("#join");
    console.log(submitBtn)
    submitBtn.disabled = true;

    // 상태 저장
    const fields = {
        userid: false,
        nickname: false,
        email: false,
        passwordMatch: false
    };

    // 메시지 표시
    const showMessage = (el, msg, ok=true) => {
        el.textContent = msg;
        el.style.color = ok ? "green" : "red";
    };

    // 등록 버튼 활성화 체크
    const updateSubmitStatus = () => {
        console.log("work")
        // 모든 필드 상태가 true이고, 필수 입력 값이 존재해야 활성화
        const allValid = Object.values(fields).every(v => v === true);
        const requiredInputs = ["userid", "password", "confirm-password", "name", "nickname", "email"];
        const allFilled = requiredInputs.every(id => document.getElementById(id).value.trim() !== "");
        console.log(allValid, allFilled)
        submitBtn.disabled = !(allValid && allFilled);
    };

    // 태그 입력
    const createTag = (container, name, val) => {
        if (!val) return;
        const exists = Array.from(container.querySelectorAll("input")).some(i => i.value === val);
        if (exists) return;

        const label = document.createElement("label");
        label.classList.add("tag");
        label.innerHTML = `<input type="checkbox" name="${name}" value="${val}" checked> <span>${val}</span>`;
        label.addEventListener("click", e => { 
            if (e.target.tagName === "SPAN") container.removeChild(label); 
        });
        container.appendChild(label);
    };

    // 관심분야 / 보유 기술 입력
    const interestInput = document.getElementById("interest-input");
    const interestTags = document.getElementById("interest-tags");
    interestInput.addEventListener("keypress", e => {
        if (e.key === "Enter") {
            e.preventDefault();
            createTag(interestTags, "interests", interestInput.value.trim());
            interestInput.value = "";
        }
    });

    const skillInput = document.getElementById("skill-input");
    const skillTags = document.getElementById("skill-tags");
    skillInput.addEventListener("keypress", e => {
        if (e.key === "Enter") {
            e.preventDefault();
            createTag(skillTags, "skills", skillInput.value.trim());
            skillInput.value = "";
        }
    });

    // 중복 체크
    const checkDuplicate = (fieldId, fieldName, msgId) => {
        const input = document.getElementById(fieldId);
        const msgEl = document.getElementById(msgId);

        input.addEventListener("input", () => {
            const val = input.value.trim();
            if (!val) {
                msgEl.textContent = "";
                fields[fieldName] = false;
                updateSubmitStatus();
                return;
            }

            fetch("/check-duplicate", {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                body: `field=${fieldName}&value=${encodeURIComponent(val)}`
            })
            .then(res => res.json())
            .then(data => {
                const ok = data.status === "ok";
                showMessage(msgEl, data.message, ok);
                fields[fieldName] = ok;
                updateSubmitStatus();
            })
            .catch(() => {
                showMessage(msgEl, "체크 중 오류 발생", false);
                fields[fieldName] = false;
                updateSubmitStatus();
            });
        });
    };

    checkDuplicate("userid", "userid", "userid-msg");
    checkDuplicate("nickname", "nickname", "nickname-msg");
    checkDuplicate("email", "email", "email-msg");

    // 비밀번호 일치 체크
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm-password");
    const pwMsg = document.createElement("div");
    confirmInput.parentNode.insertBefore(pwMsg, confirmInput.nextSibling);

    const checkPasswordMatch = () => {
        const password = passwordInput.value.trim();
        const confirm = confirmInput.value.trim();

        if (!confirm) {
            pwMsg.textContent = "";
            fields.passwordMatch = false;
            updateSubmitStatus();
            return;
        }

        const match = password === confirm;
        showMessage(pwMsg, match ? "비밀번호가 일치합니다." : "비밀번호가 일치하지 않습니다.", match);
        fields.passwordMatch = match;
        updateSubmitStatus();
    };

    passwordInput.addEventListener("input", checkPasswordMatch);
    confirmInput.addEventListener("input", checkPasswordMatch);

    // 필수 입력값 체크 (아이디, 이름, 닉네임, 이메일, 비밀번호)
    const requiredInputs = ["userid", "password", "confirm-password", "name", "nickname", "email"];
    requiredInputs.forEach(id => {
        document.getElementById(id).addEventListener("input", updateSubmitStatus);
    });
});

document.addEventListener("DOMContentLoaded", () => {

    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm-password");
    const pwMessage = document.getElementById("pw-message");

    const nickname = document.getElementById("nickname");
    const email = document.getElementById("email");

    // 닉네임 버튼 / 이메일 버튼은 각 input이 속한 .input-group 안의 button 찾기
    const nicknameBtn = nickname.parentElement.querySelector("button");
    const emailBtn = email.parentElement.querySelector("button");

    /* ---------------------------------------
     * 1) 비밀번호 확인 안내 문구
     * --------------------------------------- */
    function checkPasswordMatch() {
        const pw = password.value.trim();
        const pw2 = confirmPassword.value.trim();

        if (!pw && !pw2) {
            pwMessage.textContent = "";
            return;
        }

        if (pw === pw2) {
            pwMessage.textContent = "비밀번호가 일치합니다.";
            pwMessage.style.color = "green";
        } else {
            pwMessage.textContent = "비밀번호가 일치하지 않습니다.";
            pwMessage.style.color = "red";
        }
    }

    password.addEventListener("input", checkPasswordMatch);
    confirmPassword.addEventListener("input", checkPasswordMatch);

    /* ---------------------------------------
     * 2) 닉네임 중복확인 (프론트 더미)
     * --------------------------------------- */
    if (nicknameBtn) {
        nicknameBtn.addEventListener("click", () => {
            if (nickname.value.trim() === "") {
                alert("닉네임을 입력해주세요!");
                return;
            }
            alert("사용 가능한 닉네임입니다. (테스트용)");
        });
    }

    /* ---------------------------------------
 * 3) 이메일 인증 (프론트 더미)
 * --------------------------------------- */
if (emailBtn) {
    emailBtn.addEventListener("click", () => {

        if (email.value.trim() === "") {
            alert("이메일을 입력해주세요!");
            return;
        }

        alert("인증번호가 발송되었습니다. (테스트용)");

        // 이미 생성되어 있으면 또 만들지 않음
        if (!document.getElementById("email-code")) {

            // 인증번호 입력창
            const codeInput = document.createElement("input");
            codeInput.type = "text";
            codeInput.id = "email-code";
            codeInput.placeholder = "인증번호를 입력하세요";
            codeInput.style.marginTop = "8px";

            // 인증번호 입력창 추가
            const wrap = document.getElementById("email-auth-wrap");
            wrap.appendChild(codeInput);

            /* ⭐⭐⭐ 여기부터 추가 (확인 버튼 생성) ⭐⭐⭐ */
            const confirmBtn = document.createElement("button");
            confirmBtn.id = "email-code-confirm";
            confirmBtn.textContent = "확인";
            confirmBtn.style.marginLeft = "8px";
            confirmBtn.style.padding = "7px 12px";
            confirmBtn.style.borderRadius = "6px";
            confirmBtn.style.border = "1px solid #3DADFF";
            confirmBtn.style.background = "#fff";
            confirmBtn.style.color = "#3DADFF";
            confirmBtn.style.cursor = "pointer";

            wrap.appendChild(confirmBtn);

            /* ⭐⭐⭐ 확인 버튼 클릭 이벤트 ⭐⭐⭐ */
            confirmBtn.addEventListener("click", () => {
                const codeVal = codeInput.value.trim();

                if (codeVal === "") {
                    alert("인증번호를 입력하세요.");
                    return;
                }

                // 테스트용 코드
                if (codeVal === "123456") {
                    alert("인증 완료!");
                    confirmBtn.textContent = "✓ 인증됨";
                    confirmBtn.disabled = true;
                    confirmBtn.style.background = "#3DADFF";
                    confirmBtn.style.color = "#fff";
                } else {
                    alert("인증번호가 일치하지 않습니다.");
                }
            });
            /* ⭐⭐⭐ 추가 코드 끝 ⭐⭐⭐ */
        }
    });
}

    /* ---------------------------------------
     * 4) 취소 버튼 → 폼 초기화
     * --------------------------------------- */
    const cancelBtn = document.querySelector(".form-actions button[type='button']");
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            password.value = "";
            confirmPassword.value = "";
            nickname.value = "";
            email.value = "";
            pwMessage.textContent = "";

            const codeBox = document.getElementById("email-code");
            if (codeBox) codeBox.remove();
        });
    }

    /* ---------------------------------------
     * 5) 최종 제출 시 유효성 검사
     * --------------------------------------- */
    const form = document.querySelector(".edit-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();

            if (password.value !== confirmPassword.value) {
                alert("비밀번호가 일치하지 않습니다.");
                confirmPassword.focus();
                return;
            }
            if (nickname.value.trim() === "") {
                alert("닉네임을 입력해주세요.");
                nickname.focus();
                return;
            }
            if (email.value.trim() === "") {
                alert("이메일을 입력해주세요.");
                email.focus();
                return;
            }

            alert("정보가 수정되었습니다. (백엔드 연동은 나중에)");
        });
    }

});

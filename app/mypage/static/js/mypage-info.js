document.addEventListener("DOMContentLoaded", () => {

    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm-password");
    const pwMessage = document.getElementById("pw-message");

    const nickname = document.getElementById("nickname");
    const email = document.getElementById("email");

    // 닉네임 중복확인 버튼 (닉네임 input 옆 버튼)
    const nicknameBtn = nickname.parentElement.querySelector("button");

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
     * 2) 닉네임 중복확인 (백엔드 연동)
     * --------------------------------------- */
    if (nicknameBtn) {
        nicknameBtn.addEventListener("click", async () => {

            const nick = nickname.value.trim();
            if (!nick) {
                alert("닉네임을 입력해주세요.");
                return;
            }

            const res = await fetch("/api/mypage/check-nickname", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ nickname: nick })
            });

            const data = await res.json();
            if (!data.success) {
                alert(data.msg);
                return;
            }

            alert(data.exists ? "이미 사용 중인 닉네임입니다." : "사용 가능한 닉네임입니다.");
        });
    }


    /* ---------------------------------------
     * 3) 취소 버튼 → 초기화
     * --------------------------------------- */
    const cancelBtn = document.querySelector(".form-actions button[type='button']");
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            password.value = "";
            confirmPassword.value = "";
            nickname.value = nickname.dataset.original; 
            email.value = email.dataset.original;

            pwMessage.textContent = "";
        });
    }


    /* ---------------------------------------
     * 4) 최종 제출 → 백엔드 정보수정 API 호출
     * --------------------------------------- */
    const form = document.querySelector(".edit-form");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // 비밀번호 검증
        if (password.value.trim() || confirmPassword.value.trim()) {
            if (password.value !== confirmPassword.value) {
                alert("비밀번호가 일치하지 않습니다.");
                confirmPassword.focus();
                return;
            }
        }

        // 닉네임 검증
        if (nickname.value.trim() === "") {
            alert("닉네임을 입력해주세요.");
            nickname.focus();
            return;
        }

        // 이메일 검증
        if (email.value.trim() === "") {
            alert("이메일을 입력해주세요.");
            email.focus();
            return;
        }

        const body = {
            password: password.value.trim(),
            nickname: nickname.value.trim(),
            email: email.value.trim()
        };

        const res = await fetch("/api/mypage/update-profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.msg);
            return;
        }

        alert("회원 정보가 수정되었습니다.");
        window.location.href = "/mypage-posts";
    });

});

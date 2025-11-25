// app/mypage/static/js/mypage-withdraw.js

document.addEventListener("DOMContentLoaded", () => {

    const agreeCheck = document.getElementById("agree-check");
    const btnWithdraw = document.getElementById("btn-withdraw");

    const popup = document.getElementById("withdrawal-popup");
    const completePopup = document.getElementById("withdrawal-complete");

    /* ----------------------------------------------------
       1) 회원탈퇴 버튼
       ---------------------------------------------------- */
    btnWithdraw.addEventListener("click", () => {
        if (!agreeCheck.checked) {
            alert("회원탈퇴 약관에 동의해야 합니다.");
            return;
        }
        popup.classList.remove("hidden");
    });

    /* ----------------------------------------------------
       2) 탈퇴 확인 버튼(API 연동)
       ---------------------------------------------------- */
    window.confirmWithdrawal = async function () {
        const id = document.getElementById("withdraw-id").value.trim();
        const pw = document.getElementById("withdraw-pw").value.trim();

        if (!id || !pw) {
            alert("아이디와 비밀번호를 입력해주세요.");
            return;
        }

        const res = await fetch("/api/mypage/withdraw", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ id, pw })
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.msg);
            return;
        }

        popup.classList.add("hidden");
        completePopup.classList.remove("hidden");
    };

    window.closeWithdrawalPopup = function () {
        popup.classList.add("hidden");
    };

    window.goToHome = function () {
        location.href = "/";
    };
});

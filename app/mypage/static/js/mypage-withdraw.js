document.addEventListener("DOMContentLoaded", () => {

    const agreeCheck = document.getElementById("agree-check");
    const btnWithdraw = document.getElementById("btn-withdraw");

    const popup = document.getElementById("withdrawal-popup");
    const completePopup = document.getElementById("withdrawal-complete");

    /* ----------------------------------------------------
       1) 회원탈퇴 버튼 클릭 시 → 약관 동의 체크 확인
       ---------------------------------------------------- */
    btnWithdraw.addEventListener("click", () => {
        if (!agreeCheck.checked) {
            alert("회원탈퇴 약관에 동의해야 합니다.");
            return;
        }

        // 탈퇴 확인 모달 열기
        popup.classList.remove("hidden");
    });



    /* ----------------------------------------------------
       2) 탈퇴 확인 모달 내부 버튼들
       ---------------------------------------------------- */

    // 확인 버튼 작동
    window.confirmWithdrawal = function () {
        const id = document.getElementById("withdraw-id").value.trim();
        const pw = document.getElementById("withdraw-pw").value.trim();

        if (id === "" || pw === "") {
            alert("아이디와 비밀번호를 입력해주세요.");
            return;
        }

        // 백엔드 연동 전까지는 테스트용
        alert("회원 정보가 확인되었습니다. 회원탈퇴를 진행합니다.");

        popup.classList.add("hidden");      // 입력 모달 닫기
        completePopup.classList.remove("hidden"); // 완료 모달 열기
    };

    // 취소 버튼 누르면 닫기
    window.closeWithdrawalPopup = function () {
        popup.classList.add("hidden");
    };


    /* ----------------------------------------------------
       3) 탈퇴 완료 후 홈으로 이동 (테스트용)
       ---------------------------------------------------- */
    window.goToHome = function () {
        // 실제 배포 시 → location.href = "/"; 로 변경
        location.href = "/";
    };

});

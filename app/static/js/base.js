document.addEventListener("DOMContentLoaded", () => {
    // ===========================
    // 1. ID 기억하기 / 쿠키 저장,삭제 기능
    // ===========================
    const REMEMBER_ID_KEY = "rememberedId";  // 쿠키 이름
    const loginIdInput = document.querySelector("input[name='username']");
    const rememberMeCheckbox = document.getElementById("rememberMe");
    const loginForm = document.querySelector(".login-box form");

    function setCookie(name, value, days) {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days*24*60*60*1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/";
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i=0;i<ca.length;i++) {
            let c = ca[i].trim();
            if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length));
        }
        return null;
    }

    function deleteCookie(name) {
        setCookie(name, "", -1);
    }

    if (loginIdInput && rememberMeCheckbox && loginForm) {
        const savedId = getCookie(REMEMBER_ID_KEY);
        if (savedId) {
            loginIdInput.value = savedId;
            rememberMeCheckbox.checked = true;
        }

        loginForm.addEventListener("submit", () => {
            const id = loginIdInput.value.trim();
            if (rememberMeCheckbox.checked) {
                setCookie(REMEMBER_ID_KEY, id, 30); // 30일간 저장
            } else {
                deleteCookie(REMEMBER_ID_KEY);
            }
        });
    }

    // ===========================
    // 2. 마이페이지 버튼이동, 아이콘 요약풍선 기능
    // ===========================
    const btnMyPage = document.getElementById("btnMyPage");
    if (btnMyPage) {
        btnMyPage.addEventListener("click", function() {
            window.location.href = this.dataset.url;
        });
    }

    const icons = document.querySelectorAll("header .icons button");
    let activeBalloon = null;

    if (icons.length > 0) {
        icons.forEach(btn => {
            btn.addEventListener("click", () => {
                const tooltip = btn.getAttribute("data-tooltip");

                // 기존 풍선 제거
                if (activeBalloon) {
                    activeBalloon.remove();
                    activeBalloon = null;
                }

                if (btn.classList.contains('active-balloon')) {
                    btn.classList.remove('active-balloon');
                    return;
                }

                // 새 풍선 생성
                const balloon = document.createElement("div");
                balloon.className = "balloon";
                balloon.textContent = `${tooltip} 요약 정보가 표시됩니다.`;
                document.body.appendChild(balloon);
                btn.classList.add('active-balloon');

                const rect = btn.getBoundingClientRect();
                balloon.style.position = "absolute";
                balloon.style.top = `${rect.bottom + window.scrollY + 8}px`;
                balloon.style.left = `${rect.left + window.scrollX}px`;

                activeBalloon = balloon;

                function closeBalloon(ev) {
                    if (!btn.contains(ev.target) && !balloon.contains(ev.target)) {
                        balloon.remove();
                        activeBalloon = null;
                        btn.classList.remove('active-balloon');
                        document.removeEventListener("click", closeBalloon);
                    }
                }
                document.addEventListener("click", closeBalloon);
            });
        });
    }

    // ===========================
    // 3. 공지사항 실시간 갱신
    // ===========================
    function loadLatestNotice() {
        fetch("/api/latest_notice")  // Flask에서 만들어줄 API
            .then(response => response.json())
            .then(data => {
                const el = document.getElementById("latestNotice");
                if (el && data.title) {
                    el.textContent = data.title;   // 화면 텍스트 교체
                }
            })
            .catch(err => console.error("공지사항 불러오기 오류:", err));
    }

    // 첫 로딩 때 한번 실행
    loadLatestNotice();

    // 주기적 갱신 (5초마다)
    setInterval(loadLatestNotice, 5000);


});

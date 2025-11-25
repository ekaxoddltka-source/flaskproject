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

// ===========================
// 4. 사이드바 탭 전환 기능
// ===========================
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;

    // 모든 패널/탭 버튼
    const tabs = Array.from(document.querySelectorAll(".tab-button"));
    const panels = Array.from(document.querySelectorAll(".tab-panel"));

    // 현재 페이지 URL
    const currentURL = window.location.pathname + window.location.search;

    // 1) 모든 리스트 li 순회
    panels.forEach(panel => {
        const lis = panel.querySelectorAll("ul li");
        lis.forEach(li => {
            const a = li.querySelector("a");
            if (!a) return;

            const linkPath = new URL(a.href).pathname;
            const currentPath = window.location.pathname;

             if (linkPath === currentPath) {
                li.classList.add("selected");


                // 패널 보여주기
                panels.forEach(p => p.classList.add("hidden"));
                panel.classList.remove("hidden");

                // 탭 버튼 활성화
                const panelId = panel.id; // panel-chat, panel-mypage 등
                const tab = document.querySelector(`.tab-button[data-target="${panelId}"]`);
                if (tab) {
                    document.querySelectorAll(".tab-button").forEach(t => t.classList.remove("active"));
                    tab.classList.add("active");
                    tabs.forEach(t => t.setAttribute("aria-selected", "false"));
                    tab.setAttribute("aria-selected", "true");
                }
            }
        });
    });

    // 2) 기존 탭 클릭 기능
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.target;
            const activePanel = document.getElementById(target);

            // 탭 활성화
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            // 패널 토글
            panels.forEach(panel => panel.classList.add("hidden"));
            if (activePanel) activePanel.classList.remove("hidden");

            // 접근성
            tabs.forEach(t => t.setAttribute("aria-selected", "false"));
            tab.setAttribute("aria-selected", "true");
            panels.forEach(panel => panel.setAttribute("aria-hidden", "true"));
            if (activePanel) activePanel.setAttribute("aria-hidden", "false");
        });
    });

    // 3) 리스트 클릭 시 선택 표시
    sidebar.addEventListener("click", e => {
        const li = e.target.closest("li");
        if (!li) return;
        const list = li.closest("ul");
        if (!list) return;

        // 같은 리스트 내 selected 제거
        list.querySelectorAll("li").forEach(item => item.classList.remove("selected"));
        li.classList.add("selected");
    });

// ===========================
// 5. 실시간 채팅
// ===========================
    const socket = io(); // 서버와 연결

    // DOM 요소
    const userCountEl = document.getElementById('user-count');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');

    // ----------------------------------------
    // 접속자 수 업데이트
    // ----------------------------------------
    socket.on('update_user_count', count => {
        userCountEl.textContent = count;
    });

    // ----------------------------------------
    // 직전 5개 메시지 로드
    // ----------------------------------------
    socket.on('load_recent_messages', messages => {
        chatMessages.innerHTML = ''; // 초기화
        messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.textContent = `${msg.id} : ${msg.chat_content}   ${formatDate(msg.chat_created_at)}`;
            chatMessages.appendChild(msgDiv);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    // ----------------------------------------
    // 새로운 메시지 수신
    // ----------------------------------------
    socket.on('receive_message', msg => {
        const msgDiv = document.createElement('div');
        msgDiv.textContent = `${msg.id} : ${msg.chat_content}   ${msg.chat_created_at}`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // 메시지 5개 유지
        while (chatMessages.children.length > 5) {
            chatMessages.removeChild(chatMessages.firstChild);
        }
    });

    // ----------------------------------------
    // 메시지 전송
    // ----------------------------------------
    const sendMessage = () => {
        const message = chatInput.value.trim();
        if (!message) return;
        socket.emit('send_message', { message });
        chatInput.value = '';
    };

    sendBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') sendMessage();
    });

    // ----------------------------------------
    // 날짜 포맷 함수
    // ----------------------------------------
    function formatDate(datetimeStr) {
        // DB에서 받은 문자열이 'YYYY-MM-DD HH:MM:SS' 형태라고 가정
        return datetimeStr;
    }







});

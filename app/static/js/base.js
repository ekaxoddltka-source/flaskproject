function loadSidebarAd() {
    const box = document.getElementById("sidebar-ad");
    if (!box) return;

    fetch("/api/recommend_ads")
        .then(r => r.json())
        .then(ads => {

            // ----- 추천 광고 없음 → 기본 광고 고정 -----
            if (!ads || ads.length === 0) {
                box.innerHTML = `
                    <a href="https://www.eduwill.net/sites/home" target="_blank">
                        <img src="/static/images/adbaner.jpg"
                             style="width:100%; border-radius:8px;">
                    </a>
                `;
                return;
            }

            // ----- 추천 광고 있으면 표시 -----
            const ad = ads[0];
            box.innerHTML = `
                <a href="${ad.url}" target="_blank" class="ad-link">
                    <img src="${ad.image}" alt="${ad.title}" 
                        style="width:100%; border-radius:8px;">
                </a>
            `;

            logAdView(ad.ad_id);
            box.querySelector(".ad-link").addEventListener("click", () => {
                logAdClick(ad.ad_id);
            });

        })
        .catch(() => {
            // ----- API 에러 → 기본 광고 -----
            box.innerHTML = `
                <a href="https://www.eduwill.net/sites/home" target="_blank">
                    <img src="/static/images/adbaner.jpg"
                         style="width:100%; border-radius:8px;">
                </a>
            `;
        });
}


function logAdView(adId) {
    fetch("/api/ad/view", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ ad_id: adId })
    });
}

function logAdClick(adId) {
    fetch("/api/ad/click", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ ad_id: adId })
    });
}





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

    // 주기적 갱신 (10초마다)
    setInterval(loadLatestNotice, 10000);

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
    const socket = io();

    const userCountEl = document.getElementById('user-count');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatTopicText = document.getElementById('chatTopicText');
    const currentUserId = window.currentUserId || ''; 

    // ID 기반 색상 생성 함수
    function getColorFromId(id) {
        const colors = ["#3DADFF","#FF7F50","#32CD32","#FFB6C1","#9370DB","#FFA500","#00CED1"];
        let hash = 0;
        for (let i = 0; i < id.length; i++) {
            hash = id.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % colors.length;
        return colors[index];
    }

    // 메시지 div 생성 함수
    function appendMessage(msg) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('chat-message');

        // 내 메시지 / 타인 메시지 구분
        if (msg.id === currentUserId) {
            msgDiv.classList.add('my-message');
        } else {
            msgDiv.classList.add('other-message');
        }

        msgDiv.innerHTML = `
            <span class="chat-id" style="color:${getColorFromId(msg.id)}">${msg.id} :</span>
            <span class="chat-content">${msg.chat_content}</span>
            <span class="timestamp">${msg.chat_created_at}</span>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // 메시지 20개 이상이면 제거
        while (chatMessages.children.length > 30) {
            chatMessages.removeChild(chatMessages.firstChild);
        }
    }

    // 연결 후 추천 토픽 요청
    socket.on('connect', () => {
        socket.emit("request_topic");
    });
    
    socket.on('load_recent_messages', data => {
        const messages = data.messages;
        const canChat = data.canChat;

        chatMessages.innerHTML = '';
        messages.forEach(msg => appendMessage(msg));

        if (!canChat) {
            chatInput.disabled = true;
            sendBtn.disabled = true;
            chatInput.placeholder = "로그인 후 채팅 가능합니다.";
        }
    });

    socket.on('update_user_count', count => {
        userCountEl.textContent = count;
    });

    socket.on('receive_message', msg => appendMessage(msg));

    // 메시지 전송
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

    // ⭐ 추천 토픽 수신
    socket.on("recommend_topic", data => {
        const { topics } = data;
        let topicText = "";
        if(Array.isArray(topics)) topicText = topics.join(", ");
        else if(topics && typeof topics==="object") topicText = Object.values(topics).join(", ");
        else if(topics) topicText = String(topics);
        chatTopicText.textContent = topicText || "불러오는 중...";
    });

// ===========================
// 6. 인라인 검색창
// ===========================
    function updateQueryAndReload(changedKey, changedValue, { resetPage = true } = {}) {
        const params = new URLSearchParams(window.location.search);

        if (changedValue === null || changedValue === undefined || String(changedValue).trim() === "") {
            // 값이 빈 문자열이면 파라미터 자체 제거 (원하면 주석 처리)
            params.delete(changedKey);
        } else {
            params.set(changedKey, changedValue);
        }

        // (선택) 빈 검색어 키워드 완전 제거: keyword 존재하지만 빈값이면 제거
        if (params.has("keyword") && params.get("keyword").trim() === "") {
            params.delete("keyword");
            params.delete("search_type");
        }

        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.location.href = newUrl;
    }

    // ---------- top / feed 셀렉트 처리 ----------
    const topSelectEl = document.getElementById("topSelect");
    const feedSelectEl = document.getElementById("feedSelect");

    if (topSelectEl) {
        topSelectEl.addEventListener("change", function() {
            const selectedTop = this.value;
            updateQueryAndReload("top", selectedTop);
        });
    }

    if (feedSelectEl) {
        feedSelectEl.addEventListener("change", function() {
            const selectedFeed = this.value;
            updateQueryAndReload("feed", selectedFeed);
        });
    }

    // ---------- 검색 버튼 / 인라인 검색창 (중복 생성 방지, 기존 URL 보존) ----------
    (function setupInlineSearch() {
        const searchBtn = document.getElementById("btnSearchToggle");
        if (!searchBtn) return;

        let searchBox = null;

        function createSearchBox() {
            // 기존 URL에서 값 채우기
            const params = new URLSearchParams(window.location.search);
            const currentType = params.get("search_type") || "board_title";
            const currentKeyword = params.get("keyword") || "";

            const wrapper = document.createElement("div");
            wrapper.className = "inline-search-box";
            wrapper.innerHTML = `
                <select id="inlineSearchType">
                    <option value="board_title">제목</option>
                    <option value="board_content">내용</option>
                    <option value="id">작성자</option>
                    <option value="tag">해시태그</option>
                </select>
                <input type="text" placeholder="검색어 입력..." id="inlineSearchInput">
                <div style="display:flex; gap:6px; margin-top:6px;">
                    <button type="button" id="inlineSearchSubmit">검색</button>
                    <button type="button" id="inlineSearchClose">닫기</button>
                </div>
            `;
            // 반영
            wrapper.querySelector("#inlineSearchType").value = currentType;
            wrapper.querySelector("#inlineSearchInput").value = currentKeyword;

            return wrapper;
        }

        function closeSearchBox() {
            if (searchBox) {
                searchBox.remove();
                searchBox = null;
                document.removeEventListener("click", handleOutsideClick);
                document.removeEventListener("keydown", handleEsc);
            }
        }

        function handleOutsideClick(e) {
            if (searchBox && !searchBox.contains(e.target) && e.target !== searchBtn) {
                closeSearchBox();
            }
        }

        function handleEsc(e) {
            if (e.key === "Escape") {
                closeSearchBox();
            }
        }

        function openSearchBox() {
            if (searchBox) {
                // 이미 열려있으면 포커스
                searchBox.querySelector("#inlineSearchInput").focus();
                return;
            }
            searchBox = createSearchBox();

            const parent = searchBtn.parentElement || document.body;
            parent.appendChild(searchBox);

            const input = searchBox.querySelector("#inlineSearchInput");
            const typeSelect = searchBox.querySelector("#inlineSearchType");
            const submit = searchBox.querySelector("#inlineSearchSubmit");
            const close = searchBox.querySelector("#inlineSearchClose");

            input.focus();

            function doSearch() {
                const keyword = input.value.trim();
                const type = typeSelect.value;

                if (!keyword) {
                    alert("검색어를 입력하세요.");
                    input.focus();
                    return;
                }

                const params = new URLSearchParams(window.location.search);
                params.set("search_type", type);
                params.set("keyword", keyword);
                params.set("page", "1");

                window.location.href = `${window.location.pathname}?${params.toString()}`;
            }

            submit.addEventListener("click", doSearch);
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") doSearch();
            });

            // 닫기 버튼 클릭
            close.addEventListener("click", closeSearchBox);

            // 외부 클릭 및 ESC 키 이벤트 등록 (setTimeout으로 초기 이벤트 충돌 방지)
            setTimeout(() => {
                document.addEventListener("keydown", handleEsc);
            }, 0);
        }

        // 클릭 토글
        searchBtn.addEventListener("click", (e) => {
            e.preventDefault();
            openSearchBox();
        });
    })();

    loadSidebarAd();





});

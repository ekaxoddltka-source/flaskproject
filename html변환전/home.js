document.addEventListener("DOMContentLoaded", () => {


	let category = 0;
	let sort = "latest";
	
	
    // === 상수 정의 ===
    const REMEMBER_ID_KEY = "rememberedId";
    const POST_BODY_MAX_LENGTH = 100;

    // 현재 페이지의 컨텍스트 경로 계산 (예: "/app" 또는 "")
    const contextPath = window.location.pathname.split('/')[1] ? `/${window.location.pathname.split('/')[1]}` : '';

    // === 유틸리티 함수 ===

    /**
     * HTML 엔티티 이스케이프: XSS 방지.
     * @param {string} str 이스케이프할 문자열
     * @returns {string} 이스케이프된 문자열
     */
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * 쿠키 값을 설정하는 함수
     * @param {string} name 쿠키 이름
     * @param {string} value 쿠키 값
     * @param {number} days 만료 기간 (일 단위). 0으로 설정하면 즉시 삭제.
     */
    function setCookie(name, value, days) {
        let expires = "";
        if (days >= 0) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + value + expires + "; path=/";
    }

    /**
     * 쿠키 값을 가져오는 함수
     * @param {string} name 쿠키 이름
     * @returns {string|null} 쿠키 값 또는 null
     */
    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // === DOM 요소 캐싱 ===
    const loginBtn = document.getElementById("loginBtn");
    const loginIdInput = document.getElementById("loginId");
    const loginPwInput = document.getElementById("loginPw"); // 추가: loginPw 엘리먼트를 캐싱
    const rememberMeCheckbox = document.getElementById("rememberMe");
    const iconButtons = document.querySelectorAll("header .icons button");
    const topButtons = document.querySelectorAll(".top-buttons button");
    const feedButtons = document.querySelectorAll(".feed-buttons button");
    const writeBtn = document.getElementById("writeBtn");
    const reportModal = document.getElementById("reportModal");
    const reportForm = document.getElementById("reportForm");
    const cancelBtn = document.getElementById("cancelBtn");
    let activeBalloon = null; // 아이콘 버튼 툴팁/풍선
    let searchBox = null; // 인라인 검색창

    // === 초기화: 아이디 기억하기 (Remember Me) 로직 ===
    if (loginIdInput && rememberMeCheckbox) {
        const rememberedId = getCookie(REMEMBER_ID_KEY);
        if (rememberedId) {
            loginIdInput.value = rememberedId;
            rememberMeCheckbox.checked = true;
        }
    }

    // === 1. 로그인 기능 처리 ===
    if (loginBtn && loginIdInput && loginPwInput && rememberMeCheckbox) {
        loginBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const id = loginIdInput.value.trim();
            const pw = loginPwInput.value.trim();
            const rememberMe = rememberMeCheckbox.checked;

            if (!id || !pw) {
                alert("아이디와 비밀번호를 입력하세요.");
                return;
            }

            fetch(`${contextPath}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `id=${encodeURIComponent(id)}&pw=${encodeURIComponent(pw)}`
            })
            .then(res => res.text())
            .then(result => {
                if (result.trim() === 'true') {
                    // 로그인 성공 시 ID 기억하기 쿠키 처리
                    setCookie(REMEMBER_ID_KEY, id, rememberMe ? 30 : 0);
                    alert("로그인 성공!");
                    window.location.href = `${contextPath}/home`;
                } else {
                    alert("아이디 또는 비밀번호가 일치하지 않습니다.");
                    loginIdInput.value = "";
                    loginPwInput.value = "";
                    loginIdInput.focus();
                }
            })
            .catch(err => {
                console.error('로그인 중 오류 발생:', err);
                alert('로그인 처리 중 오류가 발생했습니다.');
            });
        });
    }

    // === 2. 헤더 아이콘 버튼 (마이페이지, 로그아웃, 풍선말) ===
    iconButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            const tooltip = btn.getAttribute("data-tooltip");

            if (tooltip === "마이페이지") {
                window.location.href = `${contextPath}/mypage`;
                return;
            }

            if (tooltip === "로그아웃") {
                if (!confirm('로그아웃 하시겠습니까?')) return;
                fetch(`${contextPath}/logout`, { method: 'POST' })
                    .then(() => {
                        // 로그아웃 시 ID 기억하기 쿠키는 유지됨
                        alert("로그아웃 되었습니다.");
                        window.location.href = `${contextPath}/home`;
                    })
                    .catch(err => {
                        console.error('로그아웃 중 오류 발생:', err);
                        alert('로그아웃 처리 중 오류가 발생했습니다.');
                    });
                return;
            }

            // 풍선말 표시 로직
            if (activeBalloon) {
                activeBalloon.remove();
                activeBalloon = null;
            }
            if (btn.classList.contains('active-balloon')) { // 현재 버튼이 활성화되어 있으면 닫기
                btn.classList.remove('active-balloon');
                return;
            }
            
            // 새 풍선말 생성
            const balloon = document.createElement("div");
            balloon.className = "balloon";
            balloon.textContent = `${tooltip} 요약 정보가 표시됩니다.`;
            document.body.appendChild(balloon);
            btn.classList.add('active-balloon'); // 현재 버튼 활성화 표시

            const rect = btn.getBoundingClientRect();
            balloon.style.position = "absolute";
            // 스크롤 위치를 고려하여 위치 지정
            balloon.style.top = `${rect.bottom + window.scrollY + 8}px`; 
            balloon.style.left = `${rect.left + window.scrollX}px`;

            activeBalloon = balloon;

            // 풍선말 외부 클릭 시 닫기
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

    // === 3. 정렬 버튼 상태 및 인라인 검색창 ===
    // 버튼 활성화 함수
    function setActive(buttons, clicked) {
        buttons.forEach(btn => btn.classList.remove("active"));
        clicked.classList.add("active");
    }
    
    // 초기 활성화 상태 설정
    if (topButtons.length > 0) topButtons[0].classList.add("active");
    if (feedButtons.length > 0) feedButtons[0].classList.add("active");
    
    // 이벤트 리스너 연결
    /*topButtons.forEach(btn => {
        btn.addEventListener("click", () => setActive(topButtons, btn));
    });*/
    feedButtons.forEach(btn => {
        btn.addEventListener("click", () => setActive(feedButtons, btn));
    });

    // '검색순' 버튼에 대한 인라인 검색창 토글 로직
    const searchBtn = Array.from(topButtons).find(
        btn => btn.textContent.includes("검색순")
    );

    if (searchBtn) {
        searchBtn.parentElement.style.position = "relative"; // 검색창 위치 기준 설정

        searchBtn.addEventListener("click", (e) => {
            // 정렬 버튼 활성화
            setActive(topButtons, searchBtn);

            // 이미 열려 있으면 닫고 종료
            if (searchBox) {
                searchBox.remove();
                searchBox = null;
                return;
            }

            // 검색창 생성 및 DOM 추가
            searchBox = document.createElement("div");
            searchBox.className = "inline-search-box";
            searchBox.innerHTML = `
                <select id="inlineSearchType">
                    <option value="title">제목</option>
                    <option value="content">내용</option>
                    <option value="author">작성자</option>
                    <option value="hashtag">해시태그</option>
                </select>
                <input type="text" placeholder="검색어 입력..." id="inlineSearchInput">
                <div style="display:flex; gap:6px;">
                    <button id="inlineSearchSubmit">검색</button>
                    <button id="inlineSearchClose">닫기</button>
                </div>
            `;
            searchBtn.parentElement.appendChild(searchBox);

            // 검색창 내부 요소 이벤트 연결
            const typeSelect = searchBox.querySelector("#inlineSearchType");
            const input = searchBox.querySelector("#inlineSearchInput");
            const submit = searchBox.querySelector("#inlineSearchSubmit");
            const close = searchBox.querySelector("#inlineSearchClose");

            input.focus();

            submit.addEventListener("click", () => {
                const keyword = input.value.trim();
                const type = typeSelect.value;
                if (!keyword) {
                    alert("검색어를 입력하세요.");
                    input.focus();
                    return;
                }
                alert(`'${keyword}'를 [${type}]에서 검색합니다. (실제 검색 API 연동 필요)`);
                // 실제 검색 로직 (API 연동 등)
                // searchBox.remove();
                // searchBox = null;
            });

            close.addEventListener("click", () => {
                searchBox.remove();
                searchBox = null;
            });
        });
    }

    // === 4. 사이드바 탭 (채팅-메뉴) 기능 ===
    const tabButtons = document.querySelectorAll('.sidebar-tabs .tab-button');
    const panels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // 버튼 상태 토글
            tabButtons.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');

            // 패널 표시/숨김
            panels.forEach(p => {
                p.classList.add('hidden');
                p.setAttribute('aria-hidden', 'true');
            });
            const target = document.getElementById(btn.dataset.target);
            if (target) {
                target.classList.remove('hidden');
                target.setAttribute('aria-hidden', 'false');
            }
        });
    });

    // === 5. 게시글 통합 더보기 (본문 확장 + 이미지 토글 + 댓글 토글) ===
    document.querySelectorAll(".post").forEach(post => {
        const body = post.querySelector(".bnote");
        const moreBtn = post.querySelector(".more");
        const imageBox = post.querySelector(".post-images");
        const comments = post.querySelector(".comments");
        const commentForm = post.querySelector(".comment-form");
        post.commentList = post.querySelector('.comments');   // 댓글 리스트
        post.commentFormEl = post.querySelector('.comment-form'); // 댓글 입력 폼
        post.answerList = post.querySelector('.answers .answer-list'); // 답변 리스트
        post.answerFormEl = post.querySelector('.answer-form'); // 답변 입력 폼
        

        if (!body || !moreBtn) return;

        const fullText = body.textContent.trim();
        const needsTruncation = fullText.length > POST_BODY_MAX_LENGTH;
        const shortText = needsTruncation 
            ? fullText.substring(0, POST_BODY_MAX_LENGTH) + "..."
            : fullText.padEnd(POST_BODY_MAX_LENGTH, " "); // 짧아도 길이를 맞춤 (UI/레이아웃 안정화 목적)

        body.textContent = shortText;
        let expanded = false;

        // 더보기 버튼이 필요 없는 경우 숨김
        if (!needsTruncation && !imageBox && !comments) {
             moreBtn.style.display = 'none';
             return;
        }

        moreBtn.addEventListener("click", (e) => {
            e.preventDefault();
            expanded = !expanded;

            // 본문 확장/축소
            body.textContent = expanded ? fullText : shortText;

            // 이미지 토글
            if (imageBox) {
                imageBox.style.display = expanded ? "flex" : "none";
            }

            // 댓글 + 입력창 토글
            if (comments && commentForm) {
                comments.style.display = expanded ? "block" : "none";
                commentForm.style.display = expanded ? "flex" : "none";
            }

            // 버튼 텍스트 변경
            moreBtn.textContent = expanded ? "접기" : "더보기";
        });
    });

    // === 6. 닉네임 드롭다운 ===
    document.addEventListener('click', (e) => {
        const clickedDropdown = e.target.closest('.nick.dropdown');
        document.querySelectorAll('.nick.dropdown.open')
            .forEach(d => {
                // 클릭된 드롭다운이 아니면 닫기
                if (d !== clickedDropdown) d.classList.remove('open');
            });
        if (clickedDropdown) {
            clickedDropdown.classList.toggle('open');
        }
    });

    // === 7. 신고 모달 (Report Modal) 기능 ===
    if (reportModal) {
        const closeBtn = reportModal.querySelector(".close");
        let currentPostId = null;

        // 신고 버튼 클릭 시 모달 열기
        document.querySelectorAll(".report").forEach(btn => {
            btn.addEventListener("click", (e) => {
                currentPostId = e.target.dataset.postId;
                reportModal.style.display = "block";
            });
        });

        // 닫기 버튼/취소 버튼 클릭 시 모달 닫기
        if (closeBtn) closeBtn.addEventListener("click", () => reportModal.style.display = "none");
        if (cancelBtn) cancelBtn.addEventListener("click", () => reportModal.style.display = "none");

        // 모달 외부 클릭 시 닫기
        window.addEventListener("click", (e) => {
            if (e.target === reportModal) reportModal.style.display = "none";
        });

        // 신고 폼 제출 처리
        if (reportForm) {
            reportForm.addEventListener("submit", (e) => {
                e.preventDefault();
                const reason = reportForm.querySelector("input[name='reason']:checked");
                if (!reason) {
                    alert("신고 사유를 선택해주세요.");
                    return;
                }
                alert(`게시글 ${currentPostId}번이 '${reason.value}' 사유로 신고되었습니다. (실제 신고 API 연동 필요)`);
                reportModal.style.display = "none";
                reportForm.reset();
            });
        }
    }

// 8. === 추천/비추천 (게시글 + 댓글) ===
const postsContainer = document.getElementById('postContainer');
postsContainer.addEventListener('click', e => {
    const btn = e.target.closest('.post-up, .post-down, .comment-up, .comment-down');
    if (!btn) return;

    let type, action;

    if (btn.classList.contains('post-up')) { type = 'post'; action = 'like'; }
    else if (btn.classList.contains('post-down')) { type = 'post'; action = 'dislike'; }
    else if (btn.classList.contains('comment-up')) { type = 'comment'; action = 'like'; }
    else if (btn.classList.contains('comment-down')) { type = 'comment'; action = 'dislike'; }
    else return;

    const id = btn.dataset.id;
    if (!id) return;

    fetch(`${contextPath}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `type=${type}&action=${action}&id=${id}`
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert(data.message || '오류가 발생했습니다.');
            return;
        }

        if (type === 'post') {
            const postEl = btn.closest('.post');
            const postUpBtn = postEl.querySelector('.post-up');
            const postDownBtn = postEl.querySelector('.post-down');

            if (action === 'like') postUpBtn.textContent = `추천 ${data.count} 👍`;
            else postDownBtn.textContent = `비추천 ${data.count} 👎`;
        } else if (type === 'comment') {
            btn.textContent = `${data.count} ${action === 'like' ? '👍' : '👎'}`;
        }

        // 사용자에게 알림
        alert(`${type === 'post' ? '게시글' : '댓글'}을 ${action === 'like' ? '추천' : '비추천'} 하셨습니다.`);
    })
    .catch(err => {
        console.error(err);
        alert('서버 요청 중 오류가 발생했습니다.');
    });
});


    // === 9. 답변 토글 및 채택 기능 ===
    // 답변 토글 버튼
    document.addEventListener('click', e => {
	    const btn = e.target.closest('.answer-toggle .answer-btn');
	    if (!btn) return;
	
	    const post = btn.closest('.post');
	    const answers = post.querySelector('.answers');
	    if (answers) answers.classList.toggle('show');
	});

    // 답변 채택 버튼
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.a-choice');
        if (!btn) return;

        e.preventDefault();
        if (!confirm('답안을 채택하시겠습니까?')) return;

        const answerItem = btn.closest('.answer-item');
        const textDiv = answerItem.querySelector('.a-text');
        
        // 채택 라벨 추가 (이미 채택된 상태가 아닌 경우에만)
        if (textDiv && !textDiv.querySelector('.chosen-label')) {
            const label = document.createElement('span');
            label.className = 'chosen-label';
            label.textContent = '채택된 답안';
            textDiv.prepend(label);
        }
        
        // 버튼 상태 변경
        btn.textContent = '채택 완료';
        btn.disabled = true;
        btn.classList.add('disabled');
        alert("답변이 채택되었습니다.");
        // 실제 채택 API 연동
    });

    // === 10. 글쓰기 버튼 이벤트 ===
    if (writeBtn) {
        writeBtn.addEventListener("click", () => {
            window.location.href = contextPath + "/write"; // 실제 경로로 변경
        });
    }

    // === 11. 게시글 삭제 + 댓글/답변 CRUD 기능 ===
	document.addEventListener('click', function(e) {
	    const target = e.target;
	
	    // ===== 1) 게시글 삭제 =====
	    if (target.classList.contains('delete-btn') && target.dataset.type === 'post') {
	        const boardNo = target.dataset.boardNo;
	        if (!boardNo) return;
	
	        if (confirm('정말로 이 게시글을 삭제하시겠습니까?')) {
	            fetch(`${contextPath}/deleteBoard`, {
	                method: "POST",
	                headers: { "Content-Type": "application/x-www-form-urlencoded" },
	                body: "boardNo=" + encodeURIComponent(boardNo)
	            })
	            .then(res => res.text())
	            .then(result => {
	                switch (result.trim()) {
	                    case "SUCCESS":
	                        alert("게시글이 삭제되었습니다.");
	                        location.reload();
	                        break;
	                    case "NOT_LOGIN":
	                        alert("로그인이 필요합니다.");
	                        break;
	                    case "NO_PERMISSION":
	                        alert("삭제 권한이 없습니다.");
	                        break;
	                    default:
	                        alert("삭제 중 오류가 발생했습니다.");
	                }
	            })
	            .catch(() => alert("서버 요청 중 문제가 발생했습니다."));
	        }
	        return;
	    }
	
	    // ===== 2) 댓글/답변 삭제 =====
	    if (target.classList.contains('delete-btn') && (target.dataset.type === 'comment' || target.dataset.type === 'answer')) {
	        const type = target.dataset.type;
	        const item = target.closest(`.${type}-item`);
	        if (!item) return;
	
	        const confirmMsg = type === 'comment' ? '이 댓글을 삭제하시겠습니까?' : '이 답변을 삭제하시겠습니까?';
	        if (!confirm(confirmMsg)) return;
	
	        const id = item.dataset.id;
	        
	        fetch(`${contextPath}/delete`, {
	            method: "POST",
	            headers: { "Content-Type": "application/x-www-form-urlencoded" },
	            body: `id=${encodeURIComponent(id)}`
	        })
	        .then(res => res.json())
	        .then(data => {
	            if(data.success) {
	                item.remove();
	                alert(`${type === 'comment' ? '댓글' : '답변'}이 삭제되었습니다.`);
	            } else {
	                alert(data.message || '삭제 실패');
	            }
	        })
	        .catch(() => alert('서버 요청 중 문제가 발생했습니다.'));
	        return;
	    }
	
	    // ===== 3) 댓글/답변 수정 모드 활성화 =====
	    if (target.classList.contains('edit-btn')) {
	        const commentItem = target.closest('.comment-item');
	        const answerItem = target.closest('.answer-item');
	        const item = commentItem || answerItem;
	        if (!item) return;
	
	        const isComment = !!commentItem;
	        const post = item.closest('.post');
	        const textElSelector = isComment ? '.c-text' : '.a-text';
	        const formSelector = isComment ? '.comment-form' : '.answer-form';
	        const submitBtnSelector = isComment ? '.submit-comment' : 'button[type="submit"]';
	
	        const textEl = item.querySelector(textElSelector);
	        const form = post.querySelector(formSelector);
	        const textarea = form ? form.querySelector('textarea') : null;
	        const submitBtn = form ? form.querySelector(submitBtnSelector) : null;
	
	        if (textEl && textarea && submitBtn) {
	            if (!isComment) {
	                const answers = post.querySelector('.answers');
	                if (answers) answers.classList.add('show');
	            }
	
	            textarea.value = textEl.textContent.trim();
	            textarea.dataset.editing = "true";
	            textarea.dataset.targetId = item.dataset.id;
	            textarea.dataset.editType = isComment ? "comment" : "answer";
	            submitBtn.textContent = "수정완료";
	            textarea.focus();
	        }
	        return;
	    }
	
	    // ===== 4) 댓글/답변 작성 및 수정 완료 =====
const isCommentSubmit = target.classList.contains('submit-comment');
const isAnswerSubmit = target.type === 'submit' && target.closest('.answer-form');

if (isCommentSubmit || isAnswerSubmit) {
    e.preventDefault();
    const form = target.closest(isCommentSubmit ? '.comment-form' : '.answer-form');
    const textarea = form.querySelector('textarea');
    const submitBtn = target;
    const isEditing = textarea.dataset.editing === "true";
    const editType = textarea.dataset.editType;

    if (!textarea.value.trim()) {
        alert(isCommentSubmit ? '댓글 내용을 입력해주세요.' : '답변 내용을 입력해주세요.');
        textarea.focus();
        return;
    }

    // 수정 모드
    if (isEditing && ((isCommentSubmit && editType === "comment") || (isAnswerSubmit && editType === "answer"))) {
        const targetId = textarea.dataset.targetId;
        const post = form.closest('.post');
        const targetSelector = isCommentSubmit ? `.comment-item[data-id="${targetId}"]` : `.answer-item[data-id="${targetId}"]`;
        const textElSelector = isCommentSubmit ? '.c-text' : '.a-text';
        const targetItem = post.querySelector(targetSelector);
        const targetText = targetItem ? targetItem.querySelector(textElSelector) : null;

        if (targetText) {
        
            fetch(`${contextPath}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `id=${encodeURIComponent(targetId)}&content=${encodeURIComponent(textarea.value.trim())}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    targetText.textContent = textarea.value.trim();
                    alert(`${isCommentSubmit ? '댓글' : '답변'}이 수정되었습니다.`);

                    textarea.dataset.editing = "false";
                    textarea.dataset.targetId = "";
                    textarea.dataset.editType = "";
                    textarea.value = "";
                    submitBtn.textContent = isCommentSubmit ? "작성" : "등록";
                } else {
                    alert(data.message || '수정 실패');
                }
            })
            .catch(() => alert('서버 요청 중 문제가 발생했습니다.'));
        }
    } 
    // 신규 작성 모드
    else {
        if (!confirm("등록하시겠습니까?")) return;

        const post = form.closest('.post');
        const postId = post.dataset.id;
        const content = textarea.value.trim();

        const api = isCommentSubmit ? `${contextPath}/addComment` : `${contextPath}/addAnswer`;
        const bodyData = `boardNo=${encodeURIComponent(postId)}&content=${encodeURIComponent(content)}`;

        fetch(api, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: bodyData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (isCommentSubmit) {
                    // 댓글 DOM 추가
                    const commentList = post.querySelector('.comments');
                    const newItem = document.createElement('div');
                    newItem.className = 'comment-item';
                    newItem.dataset.id = data.id;
                    newItem.innerHTML = `
                        <span class="c-text">${escapeHtml(content)}</span>
					    <div class="c-votes">
					        <span class="comment-up" data-id="${data.id}">0 👍</span>
					        <span class="comment-down" data-id="${data.id}">0 👎</span>
					    </div>
					    <div class="comment-actions">
					        <span class="edit-btn">수정</span>
					        <span class="delete-btn" data-type="comment">삭제</span>
					    </div>
                    `;
                    commentList.appendChild(newItem);
                } else {
                    // 답변 DOM 추가
                    const answerList = post.querySelector('.answers .answer-list');
                    const newItem = document.createElement('div');
                    newItem.className = 'answer-item';
                    newItem.dataset.id = data.id;
                    newItem.innerHTML = `
                        <div class="a-text">${escapeHtml(content)}</div>
                        <div class="a-footer">
                            <span class="author">by ${data.author}</span>
                            <div class="answer-actions">
                                <span class="edit-btn">수정</span>
                                <span class="delete-btn" data-type="answer">삭제</span>
                            </div>
                            <button class="a-choice">채택</button>
                        </div>
                    `;
                    answerList.appendChild(newItem);
                    post.querySelector('.answers').classList.add('show');
                }

                textarea.value = '';
                alert(`${isCommentSubmit ? '댓글' : '답변'}이 작성되었습니다.`);
            } else {
                alert(data.message || '작성 실패');
            }
        })
        .catch(() => alert('서버 요청 중 문제가 발생했습니다.'));
    }
}
	});
    
    // === 12. 공지사항 실시간 갱신 (jQuery 사용) ===
    if (window.jQuery) {
        function updateNotice() {
            // $.ajax는 jQuery를 사용하므로 window.jQuery가 있는지 확인 후 실행
            $.ajax({
                url: `${contextPath}/latestNotice`,
                method: 'GET',
                dataType: 'text',
                success: function(data) {
                    $('.notice-note').text(data);
                },
                error: function(err) {
                    console.error('공지사항 불러오기 실패:', err);
                }
            });
        }

        updateNotice(); // 페이지 로드 시 즉시 갱신
        setInterval(updateNotice, 10000); // 10초마다 갱신
    }
    
	// === 13. 카테고리별 게시글 필터링 (개선, 텍스트 매핑 유지) ===
	const postContainer = document.getElementById("postContainer");
	const feedButtonsFragment = document.querySelectorAll(".feed-buttons button");
	
	// --- 이벤트 위임: 게시글 내 "더보기" 버튼 및 닉네임 드롭다운 ---
	postContainer.addEventListener("click", (e) => {
	    // 1) "더보기" 버튼
	    const moreBtn = e.target.closest(".more");
	    if (moreBtn) {
	        const post = moreBtn.closest(".post");
	        if (!post) return;
	
	        const body = post.querySelector(".bnote");
	        const imageBox = post.querySelector(".post-images");
	        const comments = post.querySelector(".comments");
	        const commentForm = post.querySelector(".comment-form");
	
	        if (!body) return;
	
	        if (!body.dataset.fullText) body.dataset.fullText = body.textContent.trim();
	        const fullText = body.dataset.fullText;
	
	        const isExpanded = moreBtn.classList.toggle("expanded");
	        body.textContent = isExpanded ? fullText : (fullText.length > 100 ? fullText.substring(0, 100) + "..." : fullText);
	
	        if (imageBox) imageBox.style.display = isExpanded ? "flex" : "none";
	        if (comments && commentForm) {
	            comments.style.display = isExpanded ? "block" : "none";
	            commentForm.style.display = isExpanded ? "flex" : "none";
	        }
	
	        moreBtn.textContent = isExpanded ? "접기" : "더보기";
	        return;
	    }
	
	    // 2) 닉네임 드롭다운
	    const dropdown = e.target.closest(".nick.dropdown");
	    if (dropdown) {
	        e.stopPropagation();
	        dropdown.classList.toggle("open");
	    }
	});
	
	
	topButtons.forEach(btn => {
        btn.addEventListener("click", () => {
        	const sortMap = {
	            "최신순": "latest",
	            "조회순": "hit",
	            "추천순": "like"
	        };
	        
	        const sortText = btn.textContent.trim();
	        sort = sortMap[sortText] || "latest";
	        
	        topButtons.forEach(b => b.classList.remove("active"));
        	btn.classList.add("active");
	        
	        fetch(`${contextPath}/home/posts?category=${category}&sort=${sort}`)
	            .then(res => {
	                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
	                return res.text();
	            })
	            .then(html => {
	                postContainer.innerHTML = html;
	                // 새로 로드된 게시글 dataset 초기화
	                postContainer.querySelectorAll(".bnote").forEach(b => b.dataset.fullText = b.textContent.trim());
	            })
	            .catch(err => alert("게시글 로드 실패: " + err.message));
        });
    });
	
	// --- feed 버튼 클릭 시 AJAX 호출 (기존 텍스트 기반 매핑 유지) ---
	feedButtonsFragment.forEach(btn => {
	    btn.addEventListener("click", () => {
	        const categoryMap = {
	            "전체": 0,
	            "자유": 1,
	            "코딩테스트": 3,
	            "Q&A": 2
	        };
	        const categoryText = btn.textContent.trim();
	        category = categoryMap[categoryText] || 0;
	
	        // 버튼 활성화
	        feedButtonsFragment.forEach(b => b.classList.remove("active"));
	        btn.classList.add("active");
	
	        fetch(`${contextPath}/home/posts?category=${category}&sort=${sort}`)
	            .then(res => {
	                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
	                return res.text();
	            })
	            .then(html => {
	                postContainer.innerHTML = html;
	                // 새로 로드된 게시글 dataset 초기화
	                postContainer.querySelectorAll(".bnote").forEach(b => b.dataset.fullText = b.textContent.trim());
	            })
	            .catch(err => alert("게시글 로드 실패: " + err.message));
	    });
	});
	
	// --- 외부 클릭 시 모든 드롭다운 닫기 ---
	document.addEventListener("click", () => {
	    postContainer.querySelectorAll(".nick.dropdown.open")
	        .forEach(d => d.classList.remove("open"));
	});
	
	// ===== 14. 실시간 채팅 =====
	const chatPanel = document.getElementById("panel-chat");
	const messages = chatPanel.querySelector(".messages");
	const chatInput = chatPanel.querySelector(".chat-input input");
	const sendBtn = chatPanel.querySelector(".chat-input button");
	
	const loc = window.location;
	const wsProtocol = loc.protocol === "https:" ? "wss:" : "ws:";
	const wsUrl = `${wsProtocol}//${loc.host}${contextPath}/ws-chat`;
	
	let socket; // 전역 WebSocket 객체
	
	// ===== WebSocket 연결 함수 =====
	function connectWebSocket() {
	
	    socket = new WebSocket(wsUrl);
	
	    socket.onopen = () => {
	     console.log("웹소켓 연결됨");
	    };
	
	    socket.onmessage = (event) => {
	    console.log("서버 메시지 수신:", event.data); // 🔥 여기 추가
	        try {
	            const data = JSON.parse(event.data);
	            console.log("파싱 후 객체:", data);
	            
	            

				if (Object.prototype.hasOwnProperty.call(data, "userCount")) {
		            console.log("실시간 접속자 수 수신:", data.userCount);
		            const userCountEl = document.getElementById("user-count");
		            if (userCountEl) {
		                userCountEl.textContent = data.userCount;
		            }
		            return; // 여기서 종료 (채팅 메시지 아님)
		        }
	            
	            // 2) 일반 채팅 메시지 처리
      		    if (data.id && data.chatContent && data.chatCreatedAt) {
	            const div = document.createElement("div");
	            div.classList.add("chat-message");
	            div.innerHTML = `
	                <strong>${data.id}</strong>: ${data.chatContent}
	                <span class="timestamp">${new Date(data.chatCreatedAt).toLocaleTimeString()}</span>
	            `;
	            messages.appendChild(div);
	            messages.scrollTop = messages.scrollHeight; }
	        } catch (err) {
	            console.error("메시지 처리 오류:", err);
	            console.error("원본 데이터:", event.data);
	        }
	    };
	
	    socket.onclose = () => {
	        setTimeout(connectWebSocket, 1000); // 자동 재연결
	    };
	
	    socket.onerror = (err) => {
	        console.error("웹소켓 오류:", err);
	    };
	}
	
	// ===== 메시지 전송 =====
	function sendMessage() {
	    const content = chatInput.value.trim();
	    if (!content) return;
	    
	if (socket.readyState === WebSocket.OPEN) { 
	    const chat = {
	        chatContent: content,
	        chatCreatedAt: new Date().toISOString()
	    };
		socket.send(JSON.stringify(chat));
		
		// 입력창 초기화
        chatInput.value = "";
        chatInput.focus(); // 선택 상태 유지
        } else {
        console.warn("웹소켓이 연결되지 않았습니다. 메시지를 전송할 수 없습니다.");
    }
	}
	
	// ===== 이벤트 등록 =====
	sendBtn.addEventListener("click", sendMessage);
	chatInput.addEventListener("keydown", (e) => {
	    if (e.key === "Enter") sendMessage();
	});
	
	// ===== 초기 연결 =====
	connectWebSocket();
	
	// ===== 페이지 종료 시 WebSocket 닫기 =====
	window.addEventListener("beforeunload", () => {
	    if (socket) socket.close();
	});
	
	
});
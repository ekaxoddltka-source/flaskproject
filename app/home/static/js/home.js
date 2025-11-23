document.addEventListener("DOMContentLoaded", () => {

// ===========================
// 1. 게시글 통합 더보기 (본문 확장 + 이미지 토글 + 댓글 토글)
// ===========================
    document.querySelectorAll(".post").forEach(post => {
        const POST_BODY_MAX_LENGTH = 100;
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

// ===========================
// 2. 닉네임 드롭다운
// =========================== 
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

// ===========================
// 3. 신고모달
// =========================== 
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
            reportForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const reason = reportForm.querySelector("input[name='reason']:checked");
                if (!reason) {
                    alert("신고 사유를 선택해주세요.");
                    return;
                }

                // 문자열 → DB용 정수 매핑
                const categoryMap = {
                    "욕설/비방": 1,
                    "스팸/광고": 2,
                    "음란물": 3,
                    "도배": 4
                };

                const reportCategory = categoryMap[reason.value];

                // POST 요청으로 서버에 신고 전달
                try {
                    const response = await fetch("/report", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            board_no: currentPostId,
                            report_category: reportCategory,
                            report_content: reason.value
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        alert("신고가 접수되었습니다.");
                        reportModal.style.display = "none";
                        reportForm.reset();
                    } else {
                        alert(data.msg || "신고 처리 중 오류가 발생했습니다.");
                        reportModal.style.display = "none";
                        reportForm.reset();
                    }
                } catch (err) {
                    console.error(err);
                    alert("서버와 통신 중 오류가 발생했습니다.");
                }
            });
        }
    }

// ===========================
// 4. 게시글/답변/댓글 삭제
// =========================== 
    document.addEventListener('click', function(e) {

        const target = e.target;

        // 삭제 버튼이 아닌 경우 무시
        if (!target.classList.contains('delete-btn')) return;

        const type = target.dataset.type;   // 'post', 'comment', 'answer'
        const id = target.dataset.id;

        // 필수 데이터 없으면 종료
        if (!type || !id) {
            console.error("삭제 정보 누락", type, id);
            return;
        }

        // 삭제 확인 메시지
        let confirmMsg = "";
        if (type === "post") confirmMsg = "게시글을 삭제하시겠습니까?";
        if (type === "comment") confirmMsg = "이 댓글을 삭제하시겠습니까?";
        if (type === "answer") confirmMsg = "이 답변을 삭제하시겠습니까?";

        if (!confirm(confirmMsg)) return;

        // 삭제 요청 URL 결정
        let url = "";
        if (type === "post") url = "/post/delete";
        if (type === "comment") url = "/comment/delete";
        if (type === "answer") url = "/answer/delete";

        // POST 요청 (JSON)
        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ id: id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(`${type === 'post' ? '게시글' : type === 'comment' ? '댓글' : '답변'}이 삭제되었습니다.`);

                // 화면에서도 제거
                if (type === "post") {
                    const postEl = target.closest(".post");
                    if (postEl) postEl.remove();
                } else {
                    const itemEl = target.closest(`.${type}-item`);
                    if (itemEl) itemEl.remove();
                }

            } else {
                alert(data.msg || "삭제 실패");
            }
        })
        .catch(err => {
            console.error(err);
            alert("삭제 처리 중 오류가 발생했습니다.");
        });

    });

// ===========================
// 5. 답변/댓글 수정
// =========================== 
    document.addEventListener('click', function(e) {
        const target = e.target;
        if (!target.classList.contains('edit-btn')) return;

        const commentItem = target.closest('.comment-item');
        const answerItem = target.closest('.answer-item');
        const item = commentItem || answerItem;
        if (!item) return;

        const isComment = !!commentItem;
        const post = item.closest('.post');
        const textSelector = isComment ? '.c-text' : '.a-text';
        const formSelector = isComment ? '.comment-form' : '.answer-form';
        const submitBtnSelector = isComment ? '.submit-comment' : 'button[type="submit"]';

        const textEl = item.querySelector(textSelector);
        const form = post.querySelector(formSelector);
        const textarea = form.querySelector('textarea');
        const submitBtn = form.querySelector(submitBtnSelector);

        if (!textEl || !textarea || !submitBtn) return;

        // 수정 모드 세팅
        textarea.value = textEl.textContent.trim();
        textarea.dataset.editing = "true";
        textarea.dataset.targetId = item.dataset.id;
        textarea.dataset.editType = isComment ? "comment" : "answer";
        submitBtn.textContent = "수정완료";
        textarea.focus();
    });

    // 댓글/답변 작성 및 수정
    document.addEventListener('click', function(e) {
        const target = e.target;
        const isCommentSubmit = target.classList.contains('submit-comment');
        const isAnswerSubmit = target.closest('.answer-form');

        if (!isCommentSubmit && !isAnswerSubmit) return;

        e.preventDefault();
        const form = target.closest(isCommentSubmit ? '.comment-form' : '.answer-form');
        const textarea = form.querySelector('textarea');
        const submitBtn = target;

        if (!textarea.value.trim()) {
            alert(isCommentSubmit ? '댓글 내용을 입력해주세요.' : '답변 내용을 입력해주세요.');
            textarea.focus();
            return;
        }

        const isEditing = textarea.dataset.editing === "true";
        const editType = textarea.dataset.editType;
        const post = form.closest('.post');

        if (isEditing) {
            const targetId = textarea.dataset.targetId;
            const url = editType === 'comment' ? '/comment/update' : '/answer/update';

            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `id=${encodeURIComponent(targetId)}&content=${encodeURIComponent(textarea.value.trim())}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // 수정된 내용만 해당 DOM에 반영
                    const itemSelector = editType === 'comment' 
                        ? `.comment-item[data-id="${targetId}"] .c-text` 
                        : `.answer-item[data-id="${targetId}"] .a-text`;
                    const textEl = post.querySelector(itemSelector);
                    if (textEl) textEl.textContent = textarea.value.trim();

                    // textarea 초기화
                    textarea.value = '';
                    textarea.dataset.editing = 'false';
                    textarea.dataset.targetId = '';
                    textarea.dataset.editType = '';
                    submitBtn.textContent = isCommentSubmit ? "작성" : "등록";

                    alert(`${editType === 'comment' ? '댓글' : '답변'}이 수정되었습니다.`);
                } else {
                    alert(data.msg || '수정 실패');
                }
            })
            .catch(() => alert('서버 요청 중 문제가 발생했습니다.'));
            return;
        }

        // ===== 새 작성 모드 =====
        if (!confirm("등록하시겠습니까?")) return;

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
    });






});
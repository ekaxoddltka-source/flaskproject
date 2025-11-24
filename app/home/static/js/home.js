document.addEventListener("DOMContentLoaded", () => {

    function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

        moreBtn.addEventListener("click", async (e) => {
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

            // === 조회수 증가 ===
            if (expanded) {  // 처음 확장할 때만 조회수 증가
                const postId = post.dataset.id;  // dataset.id → board_no
                const hitEl = post.querySelector('.hit');

                fetch(`/post/hit/${postId}`, { method: "POST" })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && hitEl) {
                            hitEl.textContent = `조회수: ${data.hit}`; // UI 바로 갱신
                        }
                    })
                    .catch(err => console.error(err));
            }
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
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.a-choice');
        if (!btn) return;

        const post = btn.closest('.post');
        const post_author_id = parseInt(post.dataset.authorId, 10);
        const login_user_id = parseInt(post.dataset.loginUserId, 10);

        if (login_user_id !== post_author_id) {
            alert("게시글 작성자만 답변을 채택할 수 있습니다.");
            return;
        }

        if (!confirm("답안을 채택하시겠습니까?")) return;

        const answerItem = btn.closest('.answer-item');
        const answerId = answerItem.dataset.id;

        try {
            const res = await fetch("/answer/accept", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ answerId })
            });
            const data = await res.json();

            if (data.success) {
                // 기존 채택 해제
                post.querySelectorAll('.answer-item .chosen-label').forEach(label => label.remove());
                post.querySelectorAll('.answer-item .a-choice').forEach(b => {
                    b.textContent = "채택";
                    b.disabled = false;
                    b.classList.remove('disabled');
                });

                // 현재 선택 답변 표시
                const textDiv = answerItem.querySelector('.a-text');
                const label = document.createElement('span');
                label.className = 'chosen-label';
                label.textContent = '채택된 답안';
                textDiv.prepend(label);

                btn.textContent = '채택 완료';
                btn.disabled = true;
                btn.classList.add('disabled');

                alert(data.msg);
            } else {
                alert(data.msg || "채택 실패");
            }
        } catch (err) {
            console.error(err);
            alert("서버 요청 중 오류가 발생했습니다.");
        }
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
const reportModal = document.getElementById("reportModal");
const reportForm = document.getElementById("reportForm");
const cancelBtn = document.getElementById("cancelBtn");
const closeBtn = reportModal ? reportModal.querySelector(".close") : null;

// report 버튼들이 페이지에 있을 경우에만 처리
if (reportModal) {
    let currentPostId = null;

    // 신고 버튼 클릭 시 (버튼 내부의 요소를 클릭해도 항상 currentTarget이 버튼으로 나옵니다)
    document.querySelectorAll(".report").forEach(btn => {
        btn.addEventListener("click", (e) => {
            // 안전하게 data 속성 가져오기
            currentPostId = e.currentTarget.dataset.postId || e.currentTarget.dataset.id || null;

            if (!currentPostId) {
                // 데이터가 없는 경우 경고만 남기고 모달을 열지 않음
                console.warn("report button has no data-post-id:", e.currentTarget);
                return;
            }

            reportModal.style.display = "block";

            // 모달이 열리면 폼의 첫 입력에 포커스
            if (reportForm) {
                const firstInput = reportForm.querySelector("input[name='reason']");
                if (firstInput) firstInput.focus();
            }
        });
    });

    // 닫기 버튼 (X)
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            reportModal.style.display = "none";
        });
    }

    // 취소 버튼 (id="cancelBtn")
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            reportModal.style.display = "none";
        });
    }

    // 모달 바깥 클릭으로 닫기
    window.addEventListener("click", (e) => {
        if (e.target === reportModal) reportModal.style.display = "none";
    });

    // ESC 키로 닫기 (선택적)
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && reportModal.style.display === "block") {
            reportModal.style.display = "none";
        }
    });

    // 신고 폼 제출 처리
    if (reportForm) {
        reportForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const reasonEl = reportForm.querySelector("input[name='reason']:checked");
            if (!reasonEl) {
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

            const reportCategory = categoryMap[reasonEl.value] || 0;

            // 안전성: currentPostId 항상 체크
            if (!currentPostId) {
                alert("신고할 게시글 정보가 없습니다.");
                reportModal.style.display = "none";
                return;
            }

            try {
                const response = await fetch("/report", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        board_no: currentPostId,
                        report_category: reportCategory,
                        report_content: reasonEl.value
                    })
                });

                // response가 json이 아닐 가능성 대비
                const data = await response.json();

                if (data.success) {
                    alert("신고가 접수되었습니다.");
                    reportForm.reset();
                    reportModal.style.display = "none";
                } else {
                    alert(data.msg || "신고 처리 중 오류가 발생했습니다.");
                    reportForm.reset();
                    reportModal.style.display = "none";
                }
            } catch (err) {
                console.error("report submit error:", err);
                alert("서버와 통신 중 오류가 발생했습니다.");
            }
        });
    }
} else {
    // reportModal이 없으면 아무 동작도 하지 않음 (에러 발생하지 않음)
    // console.log("reportModal 없음 — 신고 기능 비활성화");
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
// 5. 답변/댓글 신규작성/수정
// =========================== 
    document.addEventListener('click', function(e) {
        const target = e.target;
        if (!target.classList.contains('edit-btn')) return;

        // 댓글인지 답변인지 확인
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

        // textarea에 기존 내용 불러오기
        textarea.value = textEl.textContent.trim();

        // 수정 모드 표시
        textarea.dataset.editing = "true";
        textarea.dataset.targetId = item.dataset.id;
        textarea.dataset.editType = isComment ? "comment" : "answer";

        submitBtn.textContent = "수정완료";
        textarea.focus();

        // 폼 표시 (댓글 폼은 기본 display:none)
        if (isComment) form.style.display = "flex";
    });
     // 댓글/답변 수정 저장
    document.addEventListener('click', function(e) {
        const target = e.target;

        // 댓글 submit
        if (target.classList.contains('submit-comment')) {
            e.preventDefault();
            handleSubmit(target.closest('.comment-form'), 'comment');
        }

        // 답변 submit
        if (target.closest('.answer-form') && target.closest('.answer-form').contains(target) && target.type === 'submit') {
            e.preventDefault();
            handleSubmit(target.closest('.answer-form'), 'answer');
        }
    });

    async function handleSubmit(form, type) {
    const textarea = form.querySelector('textarea');
    const submitBtn = form.querySelector(type === 'comment' ? '.submit-comment' : 'button[type="submit"]');
    const content = textarea.value.trim();

    if (!content) {
        alert(type === 'comment' ? '댓글 내용을 입력해주세요.' : '답변 내용을 입력해주세요.');
        textarea.focus();
        return;
    }

    const isEditing = textarea.dataset.editing === "true";
    const targetId = textarea.dataset.targetId;

    const post = form.closest('.post');
    const postId = post.dataset.id;

    // 공통 fetch 옵션
    const options = (url, bodyData) => ({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
    });

    try {
        if (isEditing && targetId) {
            // 수정
            const url = type === 'comment' ? '/comment/update' : '/answer/update';
            const payload = {id: targetId,content: content,boardNo: postId };
            const res = await fetch(url, options(url, payload));
            const data = await res.json();

            if (data.success) {
                const textSelector = type === 'comment' 
                    ? `.comment-item[data-id="${targetId}"] .c-text`
                    : `.answer-item[data-id="${targetId}"] .a-text`;
                const textEl = post.querySelector(textSelector);
                if (textEl) textEl.textContent = content;

                // 초기화
                textarea.value = '';
                textarea.dataset.editing = "false";
                textarea.dataset.targetId = '';
                submitBtn.textContent = type === 'comment' ? '작성' : '등록';
                alert(`${type === 'comment' ? '댓글' : '답변'}이 수정되었습니다.`);
            } else {
                alert(data.msg || '수정 실패');
            }
        } else {
            // 신규 작성
            const url = type === 'comment' ? '/addComment' : '/addAnswer';
            const res = await fetch(url, options(url, { boardNo: postId, content }));
            const data = await res.json();

            if (data.success) {
                if (type === 'comment') {
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
                            <span class="delete-btn" data-type="comment" data-id="${data.id}">삭제</span>
                        </div>
                    `;
                    commentList.appendChild(newItem);

                    const commentCountEl = post.querySelector('.comment');
                    if (commentCountEl) {
                        let count = parseInt(commentCountEl.textContent.replace(/\D/g, '')) || 0;
                        count += 1;
                        commentCountEl.textContent = `댓글 ${count}개`;
                    }
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
                                <span class="delete-btn" data-type="answer" data-id="${data.id}">삭제</span>
                            </div>
                            <button class="a-choice">채택</button>
                        </div>
                    `;
                    answerList.appendChild(newItem);
                    post.querySelector('.answers').classList.add('show');
                }
                textarea.value = '';
                alert(`${type === 'comment' ? '댓글' : '답변'}이 작성되었습니다.`);
            } else {
                alert(data.message || '작성 실패');
            }
        }
    } catch (err) {
        console.error(err);
        alert('서버 요청 중 오류가 발생했습니다.');
    }
}

// ===========================
// 6. 게시글+댓글 추천/비추천 기능
// =========================== 
    document.querySelectorAll(".posts").forEach(container => {
        container.addEventListener('click', e => {
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

            fetch('/vote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, action, id })
            })
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    alert(data.msg || '오류가 발생했습니다.');
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
    });


});
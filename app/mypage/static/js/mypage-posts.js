function formatDate(isoString) {
    const date = new Date(isoString);
    const pad = (n) => n.toString().padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function renderPost(post, loginUserId) {
    // 게시판 이름
    const categoryMap = {
        1: "자유게시판",
        2: "Q&A",
        3: "코딩테스트",
        4: "공지사항",
        5: "이용약관",
        6: "개인정보처리방침"
    };
    const categoryName = categoryMap[post.boardCategory] || "미분류";

    // 파일 HTML
    let filesHtml = "";
    if (post.files && post.files.length > 0) {
        filesHtml = post.files.map(file => 
            `<a href="/download?no=${file.fileNo}" class="upload">${file.logicalFileName}</a>`
        ).join("");
    } else {
        filesHtml = `<span class="upload">첨부파일 없음</span>`;
    }

    // 이미지 미리보기
    let imagesHtml = "";
    if (post.files && post.files.length > 0) {
        imagesHtml = post.files.map(file => {
            const ext = file.fileExt.toLowerCase();
            if (["jpg", "png", "gif"].includes(ext)) {
                return `<img src="/download?no=${file.fileNo}" alt="${file.logicalFileName}">`;
            }
            return "";
        }).join("");
    }

    // 태그 HTML
    let tagNames = [];
    let tagsHtml = "";
    if (post.tags && post.tags.length > 0) {
        tagsHtml = post.tags.map(tag => {
            if (!tagNames.includes(tag.tagName)) {
                tagNames.push(tag.tagName);
                return `<a href="/tags/${tag.tagName}">#${tag.tagName}</a>`;
            }
            return "";
        }).join("");
    }

    // 답안 HTML (commentAnswerType == 2)
    let answersHtml = "";
    if ((post.boardCategory === 2 || post.boardCategory === 3) && post.comments) {
        const answerItems = post.comments.filter(a => a.commentAnswerType === 2).map(answer => {
            return `
            <div class="answer-item" data-id="${answer.commentAnswerNo}">
                <div class="a-text">
                    ${answer.answerAccepted ? '<span class="chosen-label">채택된 답안</span>' : ''}
                    ${answer.commentAnswerContent}
                </div>
                <div class="a-footer">
                    <span class="author">by ${answer.commenterNick}</span>
                    ${loginUserId === answer.commenterId ? `
                    <div class="answer-actions">
                        <span class="edit-btn">수정</span>
                        <span class="delete-btn" data-type="answer" data-id="${answer.commentAnswerNo}">삭제</span>
                    </div>` : ''}
                    <button class="a-choice ${answer.answerAccepted ? 'disabled' : ''}" ${answer.answerAccepted ? 'disabled' : ''}>
                        ${answer.answerAccepted ? '채택 완료' : '채택'}
                    </button>
                </div>
            </div>`;
        }).join("");

        answersHtml = `
        <div class="answer-toggle">
            <button class="answer-btn">답안 작성 / 모아보기</button>
        </div>
        <div class="answers">
            <div class="answer-list">${answerItems}</div>
            <form class="answer-form">
                <textarea placeholder="답안을 작성해보세요..." required></textarea>
                <button type="submit">등록</button>
            </form>
        </div>`;
    }

    // 댓글 HTML (commentAnswerType == 1)
    let commentsHtml = "";
    if (post.comments && post.comments.length > 0) {
        commentsHtml = post.comments.filter(c => c.commentAnswerType === 1).map(comment => {
            return `
            <div class="comment-item" data-id="${comment.commentAnswerNo}">
                <span class="c-text">${comment.commentAnswerContent}</span>
                <div class="c-votes">
                    <span class="comment-up" data-id="${comment.commentAnswerNo}">${comment.commentLikeCount} 👍</span>
                    <span class="comment-down" data-id="${comment.commentAnswerNo}">${comment.commentDislikeCount} 👎</span>
                </div>
                ${loginUserId === comment.commenterId ? `
                <div class="comment-actions">
                    <span class="edit-btn">수정</span>
                    <span class="delete-btn" data-type="comment" data-id="${comment.commentAnswerNo}">삭제</span>
                </div>` : ''}
            </div>`;
        }).join("");
    }

    // 최종 HTML
    const postHtml = `
    <div class="post" data-id="${post.boardNo}" data-author-id="${post.id}" data-login-user-id="${loginUserId}">
        <div class="post-header">
            <span class="kind">[ ${categoryName} ]</span>
            <span class="title">${post.boardTitle}</span>
            <span class="nick dropdown">
                작성자: 
                ${post.icon 
                    ? `<img src="/mypage/static/${post.icon}" alt="아이콘" class="user-icon">` 
                    : `<img src="/mypage/static/icons/default.png" alt="기본 아이콘" class="user-icon">`
                }
                ${post.nick}
                <ul class="dropdown-menu">
                    <li><a href="#">프로필 보기</a></li>
                    <li><a href="#">팔로우 하기</a></li>
                    <li><a href="#">메세지 보내기</a></li>
                    <li><a href="#">차단하기</a></li>
                </ul>
            </span>
            <span class="hit">조회수: ${post.hit.toLocaleString()}</span>
            <span class="wdate">작성일: ${formatDate(post.boardCreatedAt)}</span>
        </div>

        <div class="post-body">
            ${filesHtml}
            <div class="bnote">${post.boardContent}</div>
            <div class="post-images" style="display: none;">${imagesHtml}</div>
            <br>
            <div class="tag">${tagsHtml}</div>
        </div>

        ${answersHtml}

        <div class="post-footer">
            <span class="comment">댓글 ${post.comments ? post.comments.filter(c => c.commentAnswerType === 1).length : 0}개</span>
            <div class="votes">
                <span class="post-up" data-id="${post.boardNo}">추천 ${post.boardLike} 👍</span>
                <span class="post-down" data-id="${post.boardNo}">비추천 ${post.boardDislike} 👎</span>
            </div>
            <div class="post-actions">
                ${loginUserId === post.id ? `
                <a href="/update/${post.boardNo}" class="edit-btn">수정</a>
                <span class="delete-btn" data-type="post" data-id="${post.boardNo}">삭제</span>` : ''}
            </div>
            <a href="#" class="more">더보기</a>
        </div>

        <br>

        <div class="comments">${commentsHtml}</div>
        <div class="comment-form" style="display: none;">
            <textarea placeholder="댓글을 입력하세요..."></textarea>
            <button type="button" class="submit-comment">작성</button>
        </div>
    </div>`;

    return postHtml;
}

let loginUserId = document.querySelector(".post")?.dataset.loginUserId || null;

// ------------------------------------------------- DOM로드 시작 ------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", async() => {

     try {
        const res = await fetch("/api/me");
        if (res.ok) {
            const data = await res.json();
            if (data.id) { // 값이 있으면 갱신
                loginUserId = data.id;
            }
        }
    } catch (err) {
        console.error("loginUserId fetch error:", err);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    const POST_BODY_MAX_LENGTH = 100;

    // 신고 모달
    const reportModal = document.getElementById("reportModal");
    const reportForm = document.getElementById("reportForm");
    const cancelBtn = document.getElementById("cancelBtn");
    const closeBtn = reportModal ? reportModal.querySelector(".close") : null;

    let currentPostId = null;

    // ===========================
    // 1. 게시글 본문 초기화
    // ===========================
    function initPostBody(post) {
        const body = post.querySelector(".bnote");
        const moreBtn = post.querySelector(".more");
        const imageBox = post.querySelector(".post-images");
        const comments = post.querySelector(".comments");
        const commentForm = post.querySelector(".comment-form");

        if (!body || !moreBtn) return;

        const fullText = body.textContent.trim();
        const needsTruncation = fullText.length > POST_BODY_MAX_LENGTH;

        const shortText = needsTruncation
            ? fullText.substring(0, POST_BODY_MAX_LENGTH) + "..."
            : fullText;

        body.textContent = shortText;

        if (!needsTruncation && !imageBox && !comments) {
            moreBtn.style.display = "none";
            return;
        }

        moreBtn.dataset.short = shortText;
        moreBtn.dataset.full = fullText;
        moreBtn.dataset.expanded = "false";
    }

    document.querySelectorAll(".post").forEach(initPostBody);


    // ===========================
    // 2. 공통 클릭 이벤트 (이벤트 위임)
    // ===========================
    document.addEventListener("click", async (e) => {

        // ------- (0) 이미지 미리보기 -------
        const img = e.target.closest(".post-images img");
        if (img) {
            openImagePreview(img.src);
            return;  // 다른 이벤트와 충돌 방지
        }

        // ------- (1) 더보기 -------
        const moreBtn = e.target.closest(".more");
        if (moreBtn) {
            e.preventDefault();
            const post = moreBtn.closest(".post");
            if (!post) return;

            const body = post.querySelector(".bnote");
            const imageBox = post.querySelector(".post-images");
            const comments = post.querySelector(".comments");
            const commentForm = post.querySelector(".comment-form");

            const expanded = moreBtn.dataset.expanded === "true";
            moreBtn.dataset.expanded = (!expanded).toString();

            body.textContent = expanded ? moreBtn.dataset.short : moreBtn.dataset.full;
            if (imageBox) imageBox.style.display = expanded ? "none" : "flex";
            if (comments) comments.style.display = expanded ? "none" : "block";
            if (commentForm) commentForm.style.display = expanded ? "none" : "flex";

            moreBtn.textContent = expanded ? "더보기" : "접기";

            // 조회수 증가 (첫 확장 시)
            if (!expanded) {
                const postId = post.dataset.id;
                const hitEl = post.querySelector(".hit");

                fetch(`/post/hit/${postId}`, { method: "POST" })
                    .then(r => r.json())
                    .then(d => {
                        if (d.success && hitEl) hitEl.textContent = `조회수: ${d.hit}`;
                    });

                fetch("/api/log/view", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ board_no: postId })
                }).catch(console.error);
            }
            return;
        }


        // ------- (2) 답변 토글 -------
        const answerToggleBtn = e.target.closest(".answer-toggle .answer-btn");
        if (answerToggleBtn) {
            const post = answerToggleBtn.closest(".post");
            const answers = post?.querySelector(".answers");
            if (answers) answers.classList.toggle("show");
            return;
        }


        // ------- (3) 답변 채택 -------
        const aChoiceBtn = e.target.closest(".a-choice");
        if (aChoiceBtn) {
            const post = aChoiceBtn.closest(".post");
            if (!post) return;

            const post_author_id = parseInt(post.dataset.authorId, 10);
            const login_user_id = parseInt(post.dataset.loginUserId, 10);

            if (login_user_id !== post_author_id) {
                alert("게시글 작성자만 답변을 채택할 수 있습니다.");
                return;
            }

            if (!confirm("답안을 채택하시겠습니까?")) return;

            const answerItem = aChoiceBtn.closest(".answer-item");
            const answerId = answerItem?.dataset.id;
            if (!answerId) return;

            try {
                const res = await fetch("/answer/accept", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ answerId })
                });

                const data = await res.json();
                if (!data.success) return alert(data.msg || "채택 실패");

                post.querySelectorAll(".chosen-label").forEach(el => el.remove());
                post.querySelectorAll(".a-choice").forEach(btn => {
                    btn.textContent = "채택";
                    btn.disabled = false;
                    btn.classList.remove("disabled");
                });

                const textDiv = answerItem.querySelector(".a-text");
                const label = document.createElement("span");
                label.className = "chosen-label";
                label.textContent = "채택된 답안";
                textDiv.prepend(label);

                aChoiceBtn.textContent = "채택 완료";
                aChoiceBtn.disabled = true;
                aChoiceBtn.classList.add("disabled");
                alert(data.msg);

            } catch (err) {
                console.error(err);
                alert("서버 요청 오류");
            }
            return;
        }


        // ------- (4) 닉네임 드롭다운 -------
        const clickedDropdown = e.target.closest(".nick.dropdown");
        if (clickedDropdown) {
            document.querySelectorAll(".nick.dropdown.open")
                .forEach(d => { if (d !== clickedDropdown) d.classList.remove("open"); });

            clickedDropdown.classList.toggle("open");
            return;
        }


        // ------- (5) 삭제 -------
        const deleteBtn = e.target.closest(".delete-btn");
        if (deleteBtn) {
            const type = deleteBtn.dataset.type;
            const id = deleteBtn.dataset.id;
            if (!type || !id) return;

            let msg = type === "post" ? "게시글을 삭제하시겠습니까?"
                : type === "comment" ? "댓글을 삭제하시겠습니까?"
                    : "답변을 삭제하시겠습니까?";

            if (!confirm(msg)) return;

            const url =
                type === "post" ? "/post/delete" :
                type === "comment" ? "/comment/delete" :
                "/answer/delete";

            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id })
                });
                const data = await res.json();

                if (!data.success) return alert(data.msg || "삭제 실패");

                alert(
                    type === "post"
                        ? "게시글이 삭제되었습니다."
                        : type === "comment"
                            ? "댓글이 삭제되었습니다."
                            : "답변이 삭제되었습니다."
                );

                const itemEl =
                    type === "post" ? deleteBtn.closest(".post") :
                    deleteBtn.closest(`.${type}-item`);

                itemEl?.remove();

            } catch (err) {
                console.error(err);
                alert("삭제 중 오류");
            }
            return;
        }


        // ------- (6) 수정 버튼 -------
        const editBtn = e.target.closest(".edit-btn");
        if (editBtn) {
            const commentItem = editBtn.closest(".comment-item");
            const answerItem = editBtn.closest(".answer-item");
            const item = commentItem || answerItem;
            if (!item) return;

            const isComment = !!commentItem;
            const post = item.closest(".post");

            const textEl = item.querySelector(isComment ? ".c-text" : ".a-text");
            const form = post.querySelector(isComment ? ".comment-form" : ".answer-form");
            const textarea = form?.querySelector("textarea");
            const submitBtn = form?.querySelector(isComment ? ".submit-comment" : "button[type='submit']");

            if (!textEl || !textarea || !submitBtn) return;

            textarea.value = textEl.textContent.trim();
            textarea.dataset.editing = "true";
            textarea.dataset.targetId = item.dataset.id;
            textarea.dataset.editType = isComment ? "comment" : "answer";
            submitBtn.textContent = "수정완료";

            textarea.focus();
            if (isComment) form.style.display = "flex";
            return;
        }


        // ------- (7) 댓글/답변 제출 -------
        const target = e.target;
        const isCommentSubmit = target.classList.contains("submit-comment");
        const isAnswerSubmit = target.closest(".answer-form") && target.type === "submit";

        if (isCommentSubmit || isAnswerSubmit) {
            e.preventDefault();

            // form 찾기
            let form;
            if (isCommentSubmit) {
                // 댓글은 div.comment-form
                form = target.closest(".comment-form");
            } else {
                // 답변은 form.answer-form
                form = target.closest("form");
            }

            const type = isCommentSubmit ? "comment" : "answer";
            handleSubmit(form, type);
            return;
        }


        // ------- (8) 추천 / 비추천 -------
        const voteBtn = e.target.closest(".post-up, .post-down, .comment-up, .comment-down");
        if (voteBtn) {
            const id = voteBtn.dataset.id;
            if (!id) return;

            let type, action;

            if (voteBtn.classList.contains("post-up")) { type = "post"; action = "like"; }
            else if (voteBtn.classList.contains("post-down")) { type = "post"; action = "dislike"; }
            else if (voteBtn.classList.contains("comment-up")) { type = "comment"; action = "like"; }
            else if (voteBtn.classList.contains("comment-down")) { type = "comment"; action = "dislike"; }
            else return;

            try {
                const res = await fetch("/vote", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ type, action, id })
                });

                const data = await res.json();
                if (!data.success) return alert(data.msg || "오류 발생");

                if (type === "post") {
                    const post = voteBtn.closest(".post");
                    const up = post?.querySelector(".post-up");
                    const down = post?.querySelector(".post-down");

                    if (action === "like") up.textContent = `추천 ${data.count} 👍`;
                    else down.textContent = `비추천 ${data.count} 👎`;
                } else {
                    voteBtn.textContent = `${data.count} ${action === "like" ? "👍" : "👎"}`;
                }

                alert(`${type === "post" ? "게시글" : "댓글"}을 ${action === "like" ? "추천" : "비추천"} 하셨습니다.`);

            } catch (err) {
                console.error(err);
                alert("서버 오류");
            }
            return;
        }


        // ------- (9) 신고 모달 -------
        const reportBtn = e.target.closest(".report");
        if (reportBtn && reportModal && reportForm) {
            currentPostId = reportBtn.dataset.postId || reportBtn.dataset.id;
            if (!currentPostId) return;

            reportModal.style.display = "block";
            reportForm.querySelector("input[name='reason']")?.focus();
            return;
        }


        // ------- 모달 X / 취소 -------
        if ((e.target === closeBtn || e.target === cancelBtn) && reportModal) {
            reportModal.style.display = "none";
            return;
        }
    });


    // ===========================
    // 3. 신고 모달 전용 이벤트
    // ===========================
    window.addEventListener("click", (e) => {
        if (reportModal && e.target === reportModal) {
            reportModal.style.display = "none";
        }
    });

    window.addEventListener("keydown", (e) => {
        if (reportModal && e.key === "Escape" && reportModal.style.display === "block") {
            reportModal.style.display = "none";
        }
    });

    if (reportForm) {
        reportForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const reasonEl = reportForm.querySelector("input[name='reason']:checked");
            if (!reasonEl) return alert("신고 사유를 선택해주세요.");

            if (!currentPostId) {
                alert("신고할 게시글 정보가 없습니다.");
                reportModal.style.display = "none";
                return;
            }

            const categoryMap = {
                "욕설/비방": 1,
                "스팸/광고": 2,
                "음란물": 3,
                "도배": 4
            };

            const reportCategory = categoryMap[reasonEl.value] || 0;

            try {
                const res = await fetch("/report", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        board_no: currentPostId,
                        report_category: reportCategory,
                        report_content: reasonEl.value
                    })
                });

                const data = await res.json();
                alert(data.success ? "신고가 접수되었습니다." : (data.msg || "신고 처리 중 오류 발생"));

            } catch (err) {
                console.error("report submit error:", err);
                alert("서버와 통신 중 오류");
            } finally {
                reportForm.reset();
                reportModal.style.display = "none";
            }
        });
    }


    // ===========================
    // 4. 댓글/답변 submit 처리
    // ===========================
    async function handleSubmit(form, type) {
        if (!form) return;

        const textarea = form.querySelector("textarea");
        if (!textarea) return;

        const submitBtn = form.querySelector(
            type === "comment" ? ".submit-comment" : "button[type='submit']"
        );

        const content = textarea.value.trim();
        if (!content) {
            alert(type === "comment" ? "댓글 내용을 입력해주세요." : "답변 내용을 입력해주세요.");
            textarea.focus();
            return;
        }

        const isEditing = textarea.dataset.editing === "true";
        const targetId = textarea.dataset.targetId;

        const post = form.closest(".post");
        const postId = post?.dataset.id;

        const options = (body) => ({
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        try {
            // 수정 모드
            if (isEditing && targetId) {
                const url = type === "comment" ? "/comment/update" : "/answer/update";
                const res = await fetch(url, options({ id: targetId, content, boardNo: postId }));
                const data = await res.json();

                if (!data.success) return alert(data.msg || "수정 실패");

                const selector =
                    type === "comment"
                        ? `.comment-item[data-id="${targetId}"] .c-text`
                        : `.answer-item[data-id="${targetId}"] .a-text`;

                const textEl = post.querySelector(selector);
                if (textEl) textEl.innerHTML = escapeHtml(content);

                textarea.value = "";
                textarea.dataset.editing = "false";
                textarea.dataset.targetId = "";
                submitBtn.textContent = type === "comment" ? "작성" : "등록";

                alert(`${type === "comment" ? "댓글" : "답변"} 수정 완료`);
                return;
            }

            // 신규 작성
            const url = type === "comment" ? "/addComment" : "/addAnswer";
            const res = await fetch(url, options({ boardNo: postId, content }));
            const data = await res.json();

            if (!data.success) return alert(data.msg || "작성 실패");

            if (type === "comment") {
                const commentList = post.querySelector(".comments");
                const newItem = document.createElement("div");
                newItem.className = "comment-item";
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
                commentList?.appendChild(newItem);

                const commentCountEl = post.querySelector(".comment");
                if (commentCountEl) {
                    let count = parseInt(commentCountEl.textContent.replace(/\D/g, "")) || 0;
                    count++;
                    commentCountEl.textContent = `댓글 ${count}개`;
                }

            } else {
                const answerList = post.querySelector(".answers .answer-list");
                const newItem = document.createElement("div");
                newItem.className = "answer-item";
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
                answerList?.appendChild(newItem);
                post.querySelector(".answers")?.classList.add("show");
            }

            textarea.value = "";
            alert(`${type === "comment" ? "댓글" : "답변"} 작성 완료`);

        } catch (err) {
            console.error(err);
            alert("서버 요청 오류");
        }
    }


    // ===========================
    // 5. 인피니티 스크롤
    // ===========================
    let page = 1;
    const perPage = 10;
    let loading = false;
    let reachedEnd = false; // 더 이상 데이터가 없음을 표시

    const container = document.querySelector('.posts-wrapper') || window; // posts-wrapper 우선
    const postsContainer = document.querySelector('.posts'); // 실제 포스트를 append할 곳
    const scrollTopBtn = document.getElementById("scrollTopBtn"); // 맨위로 버튼

    async function loadMorePosts() {
        if (loading || reachedEnd) return;
        loading = true;

        // 항상 최신 값 읽기
        const urlParams = new URLSearchParams(window.location.search);
        const currentTopFilter = urlParams.get('top') || '최신순';
        const currentFeedFilter = urlParams.get('feed') || '전체';
        const currentSearchType = urlParams.get('search_type') || '';
        const currentKeyword = urlParams.get('keyword') || '';

        let tagName = null;
        const pathMatch = window.location.pathname.match(/^\/tags\/(.+)/);
        if (pathMatch) {
            tagName = decodeURIComponent(pathMatch[1]);
        }

        try {
        let fetchUrl =
            `/load_more_posts?page=${page + 1}&per_page=${perPage}` +
            `&top=${encodeURIComponent(currentTopFilter)}` +
            `&feed=${encodeURIComponent(currentFeedFilter)}` +
            `&search_type=${encodeURIComponent(currentSearchType)}` +
            `&keyword=${encodeURIComponent(currentKeyword)}`;

        if (tagName) {
            fetchUrl += `&tag_name=${encodeURIComponent(tagName)}`;
        }

        const res = await fetch(fetchUrl);
        if (!res.ok) throw new Error('네트워크 응답 실패');

        const data = await res.json();
        if (!Array.isArray(data) || data.length === 0) {
            reachedEnd = true;
            return;
        }

            page += 1;

            data.forEach(post => {
                const html = renderPost(post, loginUserId);
                postsContainer.insertAdjacentHTML('beforeend', html);
                const newPostEl = postsContainer.querySelector(`.post[data-id="${post.boardNo}"]`);
                if (newPostEl) initPostBody(newPostEl);
            });
        } catch (err) {
            console.error('loadMorePosts error', err);
        } finally {
            loading = false;
        }
    }

    // 스크롤 핸들러 (posts-wrapper 용)
    // 스크롤 핸들러 (인피니티 + 맨위로 버튼)
    function onContainerScroll() {
        const isWindow = container === window;
        const scrollTop = isWindow ? window.scrollY : container.scrollTop;
        const clientHeight = isWindow ? window.innerHeight : container.clientHeight;
        const scrollHeight = isWindow ? document.body.offsetHeight : container.scrollHeight;

        // ======================
        // 인피니티 스크롤
        // ======================
        if (scrollTop + clientHeight >= scrollHeight - 100) {
            loadMorePosts();
        }

        // ======================
        // 맨 위로 버튼 표시
        // ======================
        if (scrollTopBtn) {
            scrollTopBtn.style.display = scrollTop > 300 ? "flex" : "none";
        }
    }

    // 스크롤 이벤트 등록
    if (container === window) {
        window.addEventListener('scroll', onContainerScroll, { passive: true });
    } else {
        container.addEventListener('scroll', onContainerScroll, { passive: true });
    }

    // 맨 위로 버튼 클릭
    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', () => {
            if (container === window) {
                window.scrollTo({ top: 0, behavior: "smooth" });
            } else {
                container.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }


    
});

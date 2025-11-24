document.addEventListener("DOMContentLoaded", () => {
    
    document.querySelectorAll(".btn-more").forEach(btn => {

        btn.addEventListener("click", () => {
            const id = btn.dataset.id;
            const box = document.getElementById(`detail-${id}`);

            // 이미 로딩했다면 토글만
            if (box.dataset.loaded === "1") {
                box.style.display = box.style.display === "none" ? "block" : "none";
                return;
            }

            // AJAX 요청
            fetch(`/api/mypage/post/${id}`)
                .then(res => res.json())
                .then(data => {

                    box.innerHTML = `
                        <div class="body">${data.post.board_content}</div>
                        <div class="tags">
                            ${data.tags.map(t => `#${t.tag_name}`).join(" ")}
                        </div>
                        <div class="comments">
                            ${data.comments.map(c =>
                                `<div class="comment">${c.comment_answer_content}</div>`
                            ).join("")}
                        </div>
                    `;
                    box.dataset.loaded = "1";
                });
        });

    });

    /* ============================================================
     * 0) 정렬 기능 (조회순 / 추천순 / 팔로우순)
     * ============================================================ */
    const sortBtns = document.querySelectorAll(".sort-btn");

    sortBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const type = btn.dataset.sort;

            alert(`정렬: ${type} (백엔드 연동 예정)`);

            // 아래 부분은 API 생기면 실제 정렬로 대체됨
            // ex) window.location = `/mypage-posts?sort=${type}`;
        });
    });


    /* ============================================================
     * 1) 드롭다운 메뉴
     * ============================================================ */
    document.querySelectorAll(".post .nick").forEach(nick => {
        nick.addEventListener("click", () => {
            const menu = nick.querySelector(".dropdown-menu");
            menu.classList.toggle("show");
        });
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".nick")) {
            document.querySelectorAll(".dropdown-menu.show")
                .forEach(m => m.classList.remove("show"));
        }
    });


    /* ============================================================
     * 2) 답안 토글(Q&A / 코테)
     * ============================================================ */
    document.querySelectorAll(".answer-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const panel = btn.closest(".post").querySelector(".answers");
            if (panel) panel.classList.toggle("show");
        });
    });


    /* ============================================================
     * 3) 댓글 입력창 열기/닫기
     * ============================================================ */
    document.querySelectorAll(".more").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const post = btn.closest(".post");
            const commentForm = post.querySelector(".comment-form");

            commentForm.style.display =
                commentForm.style.display === "none" ? "flex" : "none";
        });
    });


    /* ============================================================
     * 4) 댓글 작성 (테스트용)
     * ============================================================ */
    document.querySelectorAll(".submit-comment").forEach(btn => {
        btn.addEventListener("click", () => {
            const form = btn.closest(".comment-form");
            const textarea = form.querySelector("textarea");
            const text = textarea.value.trim();

            if (text === "") {
                alert("댓글을 입력하세요.");
                return;
            }

            // 실제라면 → POST /api/comments
            alert("댓글이 등록되었습니다. (테스트용)");

            textarea.value = "";
        });
    });


/* ============================================================
 * 5) 좋아요 / 싫어요 증가 (백엔드 연동 + 1인1회 토글)
 * ============================================================ */

// 추천
document.querySelectorAll(".post-up").forEach(btn => {
    btn.addEventListener("click", async () => {
        const id = btn.dataset.id;

        const res = await fetch("/api/post/like", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ board_no: id })
        });

        const data = await res.json();

        if (data.success) {
            btn.innerHTML = `추천 ${data.board_like} 👍`;
            const down = btn.closest(".votes").querySelector(".post-down");
            down.innerHTML = `비추천 ${data.board_dislike} 👎`;

            // 버튼 스타일 처리 (선택 / 비선택)
            if (data.vote === 1) {      // 추천 상태
                btn.classList.add("active");
                down.classList.remove("active");
            } else {                      // 취소됨
                btn.classList.remove("active");
            }
        }
    });
});

// 비추천
document.querySelectorAll(".post-down").forEach(btn => {
    btn.addEventListener("click", async () => {
        const id = btn.dataset.id;

        const res = await fetch("/api/post/dislike", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ board_no: id })
        });

        const data = await res.json();

        if (data.success) {
            btn.innerHTML = `비추천 ${data.board_dislike} 👎`;
            const up = btn.closest(".votes").querySelector(".post-up");
            up.innerHTML = `추천 ${data.board_like} 👍`;

            // 버튼 스타일 처리
            if (data.vote === -1) {      // 비추천 상태
                btn.classList.add("active");
                up.classList.remove("active");
            } else {                      // 취소됨
                btn.classList.remove("active");
            }
        }
    });
});



    // 댓글 추천 / 비추천
    document.querySelectorAll(".comment-up").forEach(btn => {
        btn.addEventListener("click", () => {
            const current = parseInt(btn.textContent.match(/\d+/)[0]);
            btn.innerHTML = `${current + 1} 👍`;
        });
    });

    document.querySelectorAll(".comment-down").forEach(btn => {
        btn.addEventListener("click", () => {
            const current = parseInt(btn.textContent.match(/\d+/)[0]);
            btn.innerHTML = `${current + 1} 👎`;
        });
    });


    /* ============================================================
     * 6) 답안 채택 기능 (프론트)
     * ============================================================ */
    document.querySelectorAll(".a-choice").forEach(btn => {
        btn.addEventListener("click", () => {
            const answerItem = btn.closest(".answer-item");
            const allChoices = answerItem.parentElement.querySelectorAll(".a-choice");

            allChoices.forEach(b => {
                b.textContent = "채택";
                b.classList.remove("selected");
            });

            btn.textContent = "채택됨";
            btn.classList.add("selected");

            alert("채택 완료! (백엔드 연동 예정)");
        });
    });


    /* ============================================================
     * 7) 게시글 삭제
     * ============================================================ */
    document.querySelectorAll(".delete-btn[data-type='post']").forEach(btn => {
        btn.addEventListener("click", () => {
            const boardNo = btn.dataset.boardNo;

            if (!confirm(`게시글 ${boardNo} 을(를) 삭제하시겠습니까?`)) return;

            alert("삭제완료 (백엔드 연동 예정)");

            btn.closest(".post").remove();
        });
    });


    /* ============================================================
     * 8) 신고 모달
     * ============================================================ */
    const modal = document.getElementById("reportModal");
    const closeBtn = document.querySelector(".modal .close");
    const cancelBtn = document.getElementById("cancelBtn");

    document.querySelectorAll(".report").forEach(btn => {
        btn.addEventListener("click", () => {
            modal.style.display = "block";
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener("click", () => modal.style.display = "none");
    }
    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => modal.style.display = "none");
    }

    window.addEventListener("click", (e) => {
        if (e.target === modal) modal.style.display = "none";
    });


});

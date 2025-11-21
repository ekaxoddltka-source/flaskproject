document.addEventListener("DOMContentLoaded", () => {

    /* ============================================
       요소 선택
    ============================================ */
    const selectAll = document.getElementById("select-all");
    const messageChecks = document.querySelectorAll(".message-check");
    const deleteSelectedBtn = document.querySelector(".btn-delete-selected-message");
    const deleteModal = document.getElementById("delete-confirm-modal");
    const modalConfirm = document.getElementById("modal-confirm-btn");
    const modalCancel = document.getElementById("modal-cancel-btn");

    const messagePanel = document.getElementById("messages-panel");
    const chatPanel = document.getElementById("chat-panel");
    const chatBox = document.getElementById("chat-box");
    const replyInput = document.getElementById("reply-input");


    /* ============================================
       1) 전체 선택 체크박스
    ============================================ */
    if (selectAll) {
        selectAll.addEventListener("change", () => {
            messageChecks.forEach(chk => chk.checked = selectAll.checked);
        });
    }

    /* ============================================
       2) 개별 메시지 → 체크 해제 시 전체선택 자동 해제
    ============================================ */
    messageChecks.forEach(chk => {
        chk.addEventListener("change", () => {
            if (!chk.checked) selectAll.checked = false;
        });
    });


    /* ============================================
       3) 개별 삭제 버튼
    ============================================ */
    document.querySelectorAll(".btn-delete").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation(); // 더보기와 충돌 방지
            
            const item = btn.closest(".message-item");

            deleteModal.classList.remove("hidden");

            modalConfirm.onclick = () => {
                item.remove();
                deleteModal.classList.add("hidden");
            };

            modalCancel.onclick = () => {
                deleteModal.classList.add("hidden");
            };
        });
    });


    /* ============================================
       4) 선택 삭제 버튼
    ============================================ */
    deleteSelectedBtn.addEventListener("click", () => {
        const selected = [...messageChecks].filter(chk => chk.checked);

        if (selected.length === 0) {
            alert("삭제할 메시지를 선택해주세요.");
            return;
        }

        deleteModal.classList.remove("hidden");

        modalConfirm.onclick = () => {
            selected.forEach(chk => chk.closest(".message-item").remove());
            deleteModal.classList.add("hidden");
        };

        modalCancel.onclick = () => {
            deleteModal.classList.add("hidden");
        };
    });


    /* ============================================
       5) 더보기 → 대화창(panel-switch)
    ============================================ */
    document.querySelectorAll(".btn-more").forEach(btn => {
        btn.addEventListener("click", () => {

            // 메시지 내용 채팅창에 로드 (테스트용)
            chatBox.innerHTML = `
                <div class="chat-bubble">상대 메시지 내용</div>
                <div class="chat-bubble sent">내가 보낸 메시지</div>
            `;

            // 패널 전환
            messagePanel.classList.add("hidden");
            chatPanel.classList.remove("hidden");
        });
    });


    /* ============================================
       6) 채팅 입력 → 전송 버튼
    ============================================ */
    window.sendReply = function () {
        const msg = replyInput.value.trim();
        if (!msg) return;

        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble", "sent");
        bubble.textContent = msg;

        chatBox.appendChild(bubble);
        replyInput.value = "";
    };


    /* ============================================
       7) 뒤로가기 버튼 → 메시지 리스트로 복귀
    ============================================ */
    window.goBackToList = function () {
        chatPanel.classList.add("hidden");
        messagePanel.classList.remove("hidden");
    };
});

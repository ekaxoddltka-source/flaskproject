document.addEventListener("DOMContentLoaded", () => {

    
    /* ------------------------------
       기존 변수들
    ------------------------------ */
    const selectAll = document.getElementById("select-all");
    const deleteSelectedBtn = document.querySelector(".btn-delete-selected-message");
    const deleteModal = document.getElementById("delete-confirm-modal");
    const modalConfirm = document.getElementById("modal-confirm-btn");
    const modalCancel = document.getElementById("modal-cancel-btn");

    const messagePanel = document.getElementById("messages-panel");
    const chatPanel = document.getElementById("chat-panel");
    const chatBox = document.getElementById("chat-box");
    const replyInput = document.getElementById("reply-input");
    const chatPartnerName = document.getElementById("chat-partner-name");

    let currentRoomNo = null;
    let currentPartnerId = null;
    let currentPartnerNick = null;

    /* ------------------------------
       1) 전체 선택 체크
    ------------------------------ */
    const getMessageChecks = () =>
        Array.from(document.querySelectorAll(".message-check"));

    if (selectAll) {
        selectAll.addEventListener("change", () => {
            getMessageChecks().forEach(chk => chk.checked = selectAll.checked);
        });
    }

    function bindIndividualChecks() {
        getMessageChecks().forEach(chk => {
            chk.addEventListener("change", () => {
                if (!chk.checked && selectAll) selectAll.checked = false;
            });
        });
    }
    bindIndividualChecks();

    /* ------------------------------
       3) 모달
    ------------------------------ */
    function openDeleteModal(onConfirm) {
        deleteModal.classList.remove("hidden");

        modalConfirm.onclick = async () => {
            await onConfirm();
            deleteModal.classList.add("hidden");
        };

        modalCancel.onclick = () => {
            deleteModal.classList.add("hidden");
        };
    }

    /* ------------------------------
       4) 개별 삭제
    ------------------------------ */
    async function deleteRooms(roomNos) {
        try {
            const res = await fetch("/api/mypage/messages/delete-room", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ room_nos: roomNos })
            });

            const data = await res.json();
            return data.success;

        } catch (err) {
            console.error(err);
            return false;
        }
    }

    function bindDeleteButtons() {
        document.querySelectorAll(".btn-delete").forEach(btn => {
            btn.onclick = () => {
                const item = btn.closest(".message-item");
                const roomNo = item.dataset.roomNo;

                openDeleteModal(async () => {
                    const ok = await deleteRooms([roomNo]);
                    if (ok) item.remove();
                });
            };
        });
    }
    bindDeleteButtons();

    /* ------------------------------
       6) 선택 삭제
    ------------------------------ */
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener("click", () => {
            const selected = getMessageChecks().filter(chk => chk.checked);

            if (!selected.length) {
                alert("삭제할 대화방을 선택해주세요.");
                return;
            }

            const roomNos = [...new Set(selected.map(chk => chk.dataset.roomNo))];

            openDeleteModal(async () => {
                const ok = await deleteRooms(roomNos);
                if (ok) {
                    selected.forEach(chk => chk.closest(".message-item").remove());
                }
            });
        });
    }

    /* ------------------------------
       7) 메시지 로딩
    ------------------------------ */
    async function loadRoomMessages(roomNo) {
        chatBox.innerHTML = "<div class='chat-info'>메시지를 불러오는 중...</div>";

        try {
            const res = await fetch(`/api/mypage/messages/room/${roomNo}`);
            const data = await res.json();

            if (!data.success) return;

            chatBox.innerHTML = "";
            data.messages.forEach(msg => {
                const bubble = document.createElement("div");
                bubble.classList.add("chat-bubble");
                bubble.classList.add(msg.is_me ? "sent" : "received");
                bubble.textContent = msg.content;
                chatBox.appendChild(bubble);
            });

            chatBox.scrollTop = chatBox.scrollHeight;

        } catch (err) {
            console.error(err);
        }
    }

    /* ------------------------------
       8) 더보기 → 채팅 이동
    ------------------------------ */
    function bindMoreButtons() {
        document.querySelectorAll(".btn-more").forEach(btn => {
            btn.onclick = async () => {
                const item = btn.closest(".message-item");

                currentRoomNo = item.dataset.roomNo;
                currentPartnerId = item.dataset.partnerId;
                currentPartnerNick = item.dataset.partnerNick;

                chatPartnerName.textContent = `(${currentPartnerNick})`;

                messagePanel.classList.add("hidden");
                chatPanel.classList.remove("hidden");

                await loadRoomMessages(currentRoomNo);
            };
        });
    }
    bindMoreButtons();

    /* ------------------------------
       9) 메시지 전송
    ------------------------------ */
    window.sendReply = async function() {
        const msg = replyInput.value.trim();
        if (!msg) return;

        const res = await fetch("/api/mypage/messages/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                room_no: Number(currentRoomNo),
                receiver_id: currentPartnerId,
                content: msg
            })
        });

        const data = await res.json();
        if (!data.success) return;

        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble", "sent");
        bubble.textContent = msg;
        chatBox.appendChild(bubble);

        replyInput.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;

        updateRoomPreview();
    };

    /* ------------------------------
       10) 뒤로가기
    ------------------------------ */
    window.goBackToList = function () {
        chatPanel.classList.add("hidden");
        messagePanel.classList.remove("hidden");
    };

    /* ------------------------------
       11) 리스트 갱신
    ------------------------------ */
    async function updateRoomPreview() {
        try {
            const res = await fetch("/mypage-message");
            const html = await res.text();

            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");

            const newList = doc.querySelector(".message-list");
            const oldList = document.querySelector(".message-list");

            if (newList && oldList) {
                oldList.innerHTML = newList.innerHTML;
            }

            bindMoreButtons();
            bindDeleteButtons();
            bindIndividualChecks();

        } catch (err) {
            console.error("리스트 갱신 오류", err);
        }
    }

    /* ------------------------------
       0) Socket.IO 연결 + DM Join
    ------------------------------ */
    const socket = io();

    socket.on("connect", () => {
        socket.emit("join_dm");
        console.log("join_dm emitted after connect");
    });

    socket.on("dm_receive", msg => {
        if (msg.room_no == currentRoomNo) {
            const bubble = document.createElement("div");
            bubble.classList.add("chat-bubble", "received");
            bubble.textContent = msg.content;
            chatBox.appendChild(bubble);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        updateRoomPreview();
    });


});

// app/mypage/static/js/mypage-message.js

document.addEventListener("DOMContentLoaded", () => {

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

    // 체크박스 최신 목록
    const getMessageChecks = () =>
        Array.from(document.querySelectorAll(".message-check"));


    /* ============================================
       1) 전체 선택 체크박스
    ============================================ */
    if (selectAll) {
        selectAll.addEventListener("change", () => {
            getMessageChecks().forEach(chk => chk.checked = selectAll.checked);
        });
    }

    /* ============================================
       2) 개별 체크박스 → 전체선택 자동 해제
    ============================================ */
    function bindIndividualChecks() {
        getMessageChecks().forEach(chk => {
            chk.addEventListener("change", () => {
                if (!chk.checked && selectAll) selectAll.checked = false;
            });
        });
    }
    bindIndividualChecks();


    /* ============================================
       3) 모달 열기 헬퍼
    ============================================ */
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


    /* ============================================
       4) 대화방 삭제 API
    ============================================ */
    async function deleteRooms(roomNos) {
        try {
            const res = await fetch("/api/mypage/messages/delete-room", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ room_nos: roomNos })
            });

            if (!res.ok) {
                alert("삭제 중 오류가 발생했습니다.");
                return false;
            }

            const data = await res.json();
            if (!data.success) {
                alert(data.msg || "삭제 중 오류가 발생했습니다.");
                return false;
            }

            return true;

        } catch (err) {
            console.error(err);
            alert("삭제 중 오류가 발생했습니다.");
            return false;
        }
    }


    /* ============================================
       5) 개별 삭제 버튼 바인딩
    ============================================ */
    function bindDeleteButtons() {
        document.querySelectorAll(".btn-delete").forEach(btn => {
            btn.onclick = () => {
                const item = btn.closest(".message-item");
                if (!item) return;

                const roomNo = item.dataset.roomNo;

                openDeleteModal(async () => {
                    const ok = await deleteRooms([roomNo]);
                    if (ok) item.remove();
                });
            };
        });
    }
    bindDeleteButtons();


    /* ============================================
       6) 선택 삭제 버튼
    ============================================ */
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener("click", () => {
            const selected = getMessageChecks().filter(chk => chk.checked);

            if (selected.length === 0) {
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


    /* ============================================
       7) 대화방 메시지 로드
    ============================================ */
    async function loadRoomMessages(roomNo) {

        chatBox.innerHTML = "<div class='chat-info'>메시지를 불러오는 중...</div>";

        try {
            const res = await fetch(`/api/mypage/messages/room/${roomNo}`);

            if (!res.ok) {
                alert("메시지 불러오기 실패");
                return;
            }

            const data = await res.json();
            if (!data.success) {
                alert(data.msg || "메시지 불러오기 실패");
                return;
            }

            chatBox.innerHTML = "";

            data.messages.forEach(msg => {
    const bubble = document.createElement("div");
    bubble.classList.add("chat-bubble");

    if (msg.is_me) {
        bubble.classList.add("sent");     // 내가 보낸 메시지
    } else {
        bubble.classList.add("received"); // 상대방 메시지
    }

    bubble.textContent = msg.content;
    chatBox.appendChild(bubble);
});


            chatBox.scrollTop = chatBox.scrollHeight;

        } catch (err) {
            console.error(err);
            alert("메시지 불러오기 실패");
        }
    }


    /* ============================================
       8) 메시지 패널 → 채팅 패널 이동
    ============================================ */
    function bindMoreButtons() {
        document.querySelectorAll(".btn-more").forEach(btn => {
            btn.onclick = async () => {
                const item = btn.closest(".message-item");
                const roomNo = item.dataset.roomNo;
                const partnerId = item.dataset.partnerId;
                const partnerNick = item.dataset.partnerNick;

                currentRoomNo = roomNo;
                currentPartnerId = partnerId;
                currentPartnerNick = partnerNick;

                chatPartnerName.textContent = `(${partnerNick})`;

                messagePanel.classList.add("hidden");
                chatPanel.classList.remove("hidden");

                await loadRoomMessages(roomNo);
            };
        });
    }
    bindMoreButtons();


    /* ============================================
       9) 메시지 전송 (전역)
    ============================================ */
    window.sendReply = async function () {
        const msg = replyInput.value.trim();
        if (!msg) return;

        try {
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

            if (!data.success) {
                alert(data.msg || "전송 오류");
                return;
            }

            // 화면에 추가
            const bubble = document.createElement("div");
            bubble.classList.add("chat-bubble", "sent");
            bubble.textContent = msg;
            chatBox.appendChild(bubble);

            replyInput.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;

            // 리스트 갱신
            await updateRoomPreview();

        } catch (err) {
            console.error(err);
            alert("메시지 전송 중 오류가 발생했습니다.");
        }
    };


    /* ============================================
       10) 뒤로가기
    ============================================ */
    window.goBackToList = function () {
        chatPanel.classList.add("hidden");
        messagePanel.classList.remove("hidden");
    };


    /* ============================================
       11) 메시지 리스트 자동 갱신
    ============================================ */
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

            // 갱신 후 다시 이벤트 바인딩
            bindMoreButtons();
            bindDeleteButtons();
            bindIndividualChecks();

        } catch (err) {
            console.error("리스트 갱신 중 오류", err);
        }
    }

});
const socket = io();
socket.emit("join_dm");

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


// app/mypage/static/js/mypage-room.js

document.addEventListener("DOMContentLoaded", () => {

    const roomNo = Number(document.body.dataset.roomNo);
    const partnerId = document.body.dataset.partnerId;
    const userId = document.body.dataset.userId;

    const chatBox = document.getElementById("chat-box");
    const replyInput = document.getElementById("reply-input");
    const sendBtn = document.getElementById("send-btn");

    if (!roomNo || !partnerId) {
        console.error("room 정보 로딩 오류");
        return;
    }

    /* ------------------------------
       1) Socket.IO 연결
    ------------------------------ */
    const socket = io();

    socket.on("connect", () => {
        socket.emit("join_dm");
    });

    socket.on("dm_receive", msg => {
        if (msg.room_no == roomNo) {
            appendMessage(msg.content, false);
            scrollToBottom();
        }
    });

    /* ------------------------------
       2) 메시지 로드
    ------------------------------ */
    async function loadRoomMessages() {
        chatBox.innerHTML = "<div class='chat-info'>로딩 중...</div>";

        try {
            const res = await fetch(`/api/mypage/messages/room/${roomNo}`);
            const data = await res.json();

            chatBox.innerHTML = "";

            if (!data.success) return;

            data.messages.forEach(msg => {
                appendMessage(msg.content, msg.is_me);
            });

            scrollToBottom();

        } catch (err) {
            console.error(err);
        }
    }

    loadRoomMessages();

    /* ------------------------------
       3) 메시지 전송
    ------------------------------ */
    async function sendMessage() {
    const msg = replyInput.value.trim();
    if (!msg) return;

    replyInput.value = "";
    resizeTextarea(replyInput);

    // ❌ 원본 메시지 즉시 출력 금지
    // appendMessage(msg, true);

    try {
        const res = await fetch("/api/mypage/messages/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                room_no: roomNo,
                receiver_id: partnerId,
                content: msg
            })
        });

        const data = await res.json();

        // ⭕ 서버가 필터링한 메시지를 출력
        appendMessage(data.content, true);
        scrollToBottom();

    } catch (err) {
        console.error("메시지 전송 실패", err);
    }
    }

    sendBtn.addEventListener("click", sendMessage);

    replyInput.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    /* ------------------------------
       4) 메시지 DOM
    ------------------------------ */
    function appendMessage(content, isMe) {
        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble", isMe ? "sent" : "received");
        bubble.textContent = content;
        chatBox.appendChild(bubble);
    }

    /* ------------------------------
       5) 스크롤
    ------------------------------ */
    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    /* ------------------------------
       6) textarea 자동 높이 조절
    ------------------------------ */
    function resizeTextarea(el) {
        el.style.height = "auto";
        el.style.height = (el.scrollHeight) + "px";
    }

    window.autoResize = resizeTextarea;

});

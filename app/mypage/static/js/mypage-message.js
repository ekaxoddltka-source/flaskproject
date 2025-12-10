document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       SECTION 1 — 메시지 리스트: 전체 선택 / 삭제
    ============================================================ */

    const selectAll = document.getElementById("select-all");
    const deleteSelectedBtn = document.querySelector(".btn-delete-selected-message");

    const deleteModal = document.getElementById("delete-confirm-modal");
    const modalConfirm = document.getElementById("modal-confirm-btn");
    const modalCancel = document.getElementById("modal-cancel-btn");

    const getMessageChecks = () =>
        Array.from(document.querySelectorAll(".message-check"));


    /* 전체 선택 */
    selectAll?.addEventListener("change", () => {
        getMessageChecks().forEach(chk => chk.checked = selectAll.checked);
    });

    /* 개별 체크 → 전체 체크 해제 */
    function bindIndividualChecks() {
        getMessageChecks().forEach(chk => {
            chk.addEventListener("change", () => {
                if (!chk.checked) selectAll.checked = false;
            });
        });
    }
    bindIndividualChecks();


    /* 삭제 모달 */
    function openDeleteModal(onConfirm) {
        deleteModal.classList.remove("hidden");

        modalConfirm.onclick = async () => {
            await onConfirm();
            deleteModal.classList.add("hidden");
        };

        modalCancel.onclick = () => deleteModal.classList.add("hidden");
    }


    /* 삭제 API */
    async function deleteRooms(roomNos) {
        try {
            const res = await fetch("/api/mypage/messages/delete-room", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ room_nos: roomNos })
            });

            const data = await res.json();
            return data.success === true;

        } catch (err) {
            console.error(err);
            return false;
        }
    }


    /* 개별 삭제 버튼 */
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



    /* 선택 삭제 버튼 */
    deleteSelectedBtn?.addEventListener("click", () => {
        const selected = getMessageChecks().filter(chk => chk.checked);

        if (selected.length === 0) {
            alert("삭제할 대화방을 선택해주세요.");
            return;
        }

        const roomNos = [...new Set(selected.map(chk => chk.dataset.roomNo))];

        openDeleteModal(async () => {
            const ok = await deleteRooms(roomNos);
            if (ok) selected.forEach(chk => chk.closest(".message-item").remove());
        });
    });





    /* ============================================================
       SECTION 2 — 새 메시지 모달
    ============================================================ */

    const modal = document.getElementById("new-message-modal");
    const openBtn = document.getElementById("open-new-message");
    const closeBtn = document.getElementById("close-new-message");

    const searchInput = document.getElementById("search-user-input");
    const searchResult = document.getElementById("search-result");

    const followList = document.getElementById("follow-list");
    const followToggle = document.getElementById("toggle-follow-list");

    const msgContent = document.getElementById("new-message-content");
    const sendBtn = document.getElementById("send-new-message");

    let selectedUserId = null;



    /* 모달 열기 */
    openBtn?.addEventListener("click", () => {
        modal.classList.remove("hidden");
    });

    /* 모달 닫기 */
    closeBtn?.addEventListener("click", () => {
        modal.classList.add("hidden");
        resetModal();
    });



    function resetModal() {
        selectedUserId = null;
        searchInput.value = "";
        msgContent.value = "";
        searchResult.innerHTML = "";

        followList.classList.remove("open");
        followList.classList.add("closed");

        followToggle.classList.remove("rotate");
        clearSelectedUsers();
    }



    /* ============================================================
       유저 선택 기능
    ============================================================ */

    function clearSelectedUsers() {
        document.querySelectorAll(".user-item")
            .forEach(i => i.classList.remove("selected"));
    }

    function bindUserSelect() {
        document.querySelectorAll(".user-item").forEach(item => {
            item.addEventListener("click", () => {
                clearSelectedUsers();
                item.classList.add("selected");

                selectedUserId = item.dataset.userId;
                searchInput.value = item.dataset.nick;
            });
        });
    }
    bindUserSelect();



    /* ============================================================
       1) 전체 유저 검색 기능
    ============================================================ */

    searchInput?.addEventListener("input", async () => {
        const keyword = searchInput.value.trim();

        if (!keyword) {
            searchResult.innerHTML = "";
            selectedUserId = null;
            return;
        }

        const res = await fetch("/api/mypage/search-user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword })
        });

        const users = await res.json();

        searchResult.innerHTML = users.map(u => `
            <div class="user-item" data-user-id="${u.id}" data-nick="${u.nick}">
                <span class="nick">${u.nick}</span>
            </div>
        `).join("");

        bindUserSelect();
    });




    /* ============================================================
       2) 팔로우 목록 드롭다운 (애니메이션 추가)
    ============================================================ */

    followToggle?.addEventListener("click", () => {
        const isOpen = followList.classList.contains("open");

        if (isOpen) {
            followList.classList.remove("open");
            followList.classList.add("closed");
            followToggle.classList.remove("rotate");
        } else {
            followList.classList.add("open");
            followList.classList.remove("closed");
            followToggle.classList.add("rotate");
        }
    });



    /* ============================================================
       3) 메시지 전송
    ============================================================ */

    sendBtn?.addEventListener("click", async () => {
        if (!selectedUserId) {
            alert("보낼 유저를 선택하세요.");
            return;
        }

        const content = msgContent.value.trim();
        if (!content) {
            alert("메시지를 입력하세요.");
            return;
        }

        const res = await fetch("/api/mypage/message/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                target_id: selectedUserId,
                content
            })
        });

        const data = await res.json();

        if (data.success) {
            window.location.href = `/mypage-message/room/${data.room_no}`;
        }
    });

});

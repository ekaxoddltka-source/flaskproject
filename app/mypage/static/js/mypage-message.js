// app/mypage/static/js/mypage-message.js

document.addEventListener("DOMContentLoaded", () => {

    /* ------------------------------------------------------------
       공통 체크박스 / 삭제 기능
    ------------------------------------------------------------ */

    const selectAll = document.getElementById("select-all");
    const deleteSelectedBtn = document.querySelector(".btn-delete-selected-message");

    const deleteModal = document.getElementById("delete-confirm-modal");
    const modalConfirm = document.getElementById("modal-confirm-btn");
    const modalCancel = document.getElementById("modal-cancel-btn");

    // 체크박스 최신 목록
    const getMessageChecks = () =>
        Array.from(document.querySelectorAll(".message-check"));


    /* ------------------------------------------------------------
       1) 전체 선택 체크박스
    ------------------------------------------------------------ */
    if (selectAll) {
        selectAll.addEventListener("change", () => {
            getMessageChecks().forEach(chk => chk.checked = selectAll.checked);
        });
    }

    /* ------------------------------------------------------------
       2) 개별 체크박스 → 전체 선택 해제
    ------------------------------------------------------------ */
    function bindIndividualChecks() {
        getMessageChecks().forEach(chk => {
            chk.addEventListener("change", () => {
                if (!chk.checked) selectAll.checked = false;
            });
        });
    }
    bindIndividualChecks();


    /* ------------------------------------------------------------
       3) 삭제 모달 헬퍼
    ------------------------------------------------------------ */
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


    /* ------------------------------------------------------------
       4) 삭제 API
    ------------------------------------------------------------ */
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


    /* ------------------------------------------------------------
       5) 개별 삭제 버튼
    ------------------------------------------------------------ */
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


    /* ------------------------------------------------------------
       6) 선택 삭제 버튼
    ------------------------------------------------------------ */
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

});

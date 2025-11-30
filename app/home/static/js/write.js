document.addEventListener("DOMContentLoaded", () => {

  // 파일 업로드 처리 (여러 파일 + 삭제 버튼)
  const fileUpload = document.getElementById("fileUpload");
  const fileListContainer = document.querySelector(".file-name"); // 기존 span 활용
  let selectedFiles = []; // 실제로 서버에 전송할 파일 목록

  if (fileUpload && fileListContainer) {

    fileUpload.addEventListener("change", function () {
      selectedFiles = Array.from(this.files);
      renderFileList();
    });

    // 기존 서버 파일 삭제 처리
    const existingFileElements = document.querySelectorAll(".existing-files li");
    existingFileElements.forEach(li => {
      const fileNo = li.dataset.fileNo; // li에 data-file-no 속성이 있어야 함
      if (!fileNo) return;

      // 버튼 생성
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "X";
      btn.className = "delete-file-btn";
      btn.style.background = "red";
      btn.style.color = "#fff";
      btn.style.border = "none";
      btn.style.borderRadius = "50%";
      btn.style.width = "18px";
      btn.style.height = "18px";
      btn.style.cursor = "pointer";
      btn.style.fontSize = "12px";

      li.appendChild(btn);

      btn.addEventListener("click", () => {
        if (!confirm("정말 이 파일을 삭제하시겠습니까?")) return;

        fetch(`/delete_file/${fileNo}`, { method: "POST" })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              li.remove();
            } else {
              alert(data.message || "삭제 실패");
            }
          });
      });
    });

    // 새로 선택한 파일 렌더링
    function renderFileList() {
      fileListContainer.innerHTML = "";

      if (selectedFiles.length === 0) {
        fileListContainer.textContent = "선택된 파일 없음";
        return;
      }

      selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement("div");
        fileItem.className = "file-item";
        fileItem.style.display = "inline-flex";
        fileItem.style.alignItems = "center";
        fileItem.style.gap = "6px";
        fileItem.style.marginRight = "8px";

        const fileName = document.createElement("span");
        fileName.textContent = file.name;

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.textContent = "X";
        removeBtn.style.background = "red";
        removeBtn.style.color = "#fff";
        removeBtn.style.border = "none";
        removeBtn.style.borderRadius = "50%";
        removeBtn.style.width = "18px";
        removeBtn.style.height = "18px";
        removeBtn.style.cursor = "pointer";
        removeBtn.style.fontSize = "12px";
        removeBtn.addEventListener("click", () => {
          selectedFiles.splice(index, 1);
          renderFileList();
        });

        fileItem.appendChild(fileName);
        fileItem.appendChild(removeBtn);
        fileListContainer.appendChild(fileItem);
      });
    }

    // 폼 제출 시 FormData에 selectedFiles만 포함
    const form = document.querySelector(".write-form");
    if (form) {
      form.addEventListener("submit", function () {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => dataTransfer.items.add(file));
        fileUpload.files = dataTransfer.files;
      });
    }
  }

  // 5. 카테고리 별 추가 필드 처리
  const category = document.getElementById("category");
  const extra = document.getElementById("extraCategory");

  if (category && extra) {
    // renderExtra 정의 (대체/확장됨)
    function renderExtra(catValue, targetValue = null) {
      extra.innerHTML = ""; // 초기화

      if (catValue === "3") {
        // Q&A
        extra.innerHTML = `
          <label for="lang">언어선택</label>
          <select id="lang" name="lang">
            <option>JAVA</option>
            <option>파이썬</option>
            <option>C</option>
            <option>C++</option>
            <option>PHP/JSP</option>
            <option>HTML/CSS/JS</option>
          </select>

          <label for="level">난이도</label>
          <select id="level" name="level">
            <option>상</option>
            <option>중</option>
            <option>하</option>
          </select>
        `;
        return;
      }

      if (catValue === "2") {
        // 코딩테스트
        extra.innerHTML = `
          <label for="tech">관련기술</label>
          <select id="tech" name="tech">
            <option>리눅스/서버/설치/설정</option>
            <option>Mysql/Oracle/Query/DB</option>
            <option>PHP관련/함수/프레임웍</option>
            <option>HTML/JS/CSS/jQuery/Ajax</option>
            <option>모바일앱/하이브리드앱</option>
            <option>기타개발관련/ASP/JSP</option>
          </select>

          <label for="target">질문대상</label>
          <select id="target" name="target">
            <option value="member">회원</option>
            <option value="admin">관리자</option>
          </select>

          <label for="point">포인트</label>
          <input type="number" id="point" name="point" min="0" placeholder="보유포인트 : 54,200P">
        `;

        const targetElem = document.getElementById("target");

        // 안전하게 값 설정
        if (targetValue && targetElem) {
          targetElem.value = targetValue;
        }

        // 공통: target 변경시 처리 (사용자 -> 관리자 전환)
        if (targetElem) {
          targetElem.addEventListener("change", function onBaseTargetChange() {
            if (this.value === "admin") {
              // 관리자 UI로 교체
              renderAdminUI();
            }
            // 사용자가 다시 member 선택했을 때는 자동 복구 (renderExtra 호출)
            // 관리자 UI에서 다시 member 클릭 시 renderAdminUI 내부에서 복구 로직을 붙여줌
          });
        }

        // 만약 로드시 targetValue가 'admin'이면 즉시 관리자 UI 렌더
        if (targetValue === "admin") {
          renderAdminUI();
        }

        return;
      }

      // 기타 카테고리: 아무 추가 필드 없음
      extra.innerHTML = "";
    }

    // 별도 함수: 관리자 선택 시 보여줄 UI와 이벤트 처리
    function renderAdminUI() {
      extra.innerHTML = `
        <label for="target">질문대상</label>
        <select id="target" name="target">
          <option value="member">회원</option>
          <option value="admin" selected>관리자</option>
        </select>

        <label for="inquiry">문의분류</label>
        <select id="inquiry" name="inquiry">
          <option value="bug">버그/개선 문의</option>
          <option value="policy">이용약관 문의</option>
          <option value="sanction">제재사유 문의</option>
        </select>
      `;

    // 새로 생성된 target에 이벤트 연결 (member로 바꾸면 Q&A 기본 UI 복구)
      const newTarget = document.getElementById("target");
      if (newTarget) {
        newTarget.addEventListener("change", function () {
          if (this.value === "member") {
            // member 선택 시 Q&A 기본 UI로 복구 (member 기본값 유지)
            renderExtra("2", "member");
            // 그리고 카테고리 select 값도 보장
            const cat = document.getElementById("category");
            if (cat) cat.value = "2";
          }
        });
      }
    }

    // category change 이벤트 (사용자 직접 변경)
    category.addEventListener("change", function () {
      renderExtra(this.value);
    });

    // ===== URL 파라미터에서 초기값 읽기 (여기 위치하면 renderExtra 함수가 이미 정의되어 있음) =====
    const params = new URLSearchParams(window.location.search);
    const catParam = params.get("category"); // ex: 'qna'
    const targetParam = params.get("target"); // ex: 'admin'

    if (catParam) {
      // 카테고리 기본값 설정
      category.value = catParam;
      // renderExtra에 targetParam을 전달하면, renderExtra 내부에서
      // targetParam === 'admin'일 경우 관리자 UI가 바로 렌더됩니다.
      renderExtra(catParam, targetParam);
    }

  } // end if (category && extra)

  //카테고리 7,8번 선택 시 로딩되는 폼
  const categorySelect = document.getElementById("category");
  // normalForm은 id로 찾음 (템플릿에 id 추가 권장)
  let normalForm = document.getElementById("normalWriteForm");
  const itemContainer = document.getElementById("itemWriteContainer");

  // 만약 template에 id를 못 넣는 상황이면 대체 방법으로 첫 번째 write-form 을 사용
  if (!normalForm) {
    const firstForm = document.querySelector("form.write-form");
    if (firstForm) {
      // 감싸는 div를 만들어서 참조 가능하게 함 (안전)
      normalForm = firstForm;
    }
  }

  function loadItemForm(type) {
    // itemContainer가 없으면 생성(안전망)
    if (!itemContainer) return;
    itemContainer.innerHTML = `
        <form class="write-form item-write-form"
              action="/add_item"
              method="post"
              enctype="multipart/form-data">

            <h2>${type === "icon" ? "아이콘 등록" : "배경이미지 등록"}</h2>

            <input type="hidden" name="item_type" value="${type}">

            <div>
                <label>아이템 이름</label>
                <input type="text" name="item_name" required>
            </div>

            <div>
                <label>아이템 가격</label>
                <input type="number" name="item_price" min="0" required>
            </div>

            <div>
                <label>이미지 파일</label>
                <input type="file" name="item_img" accept="image/*" required>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn-submit">등록</button>
                <button type="button" class="btn-cancel" id="itemCancelBtn">취소</button>
            </div>
        </form>
    `;

    // 취소 버튼 동작: 원래 폼 복원
    const cancelBtn = document.getElementById("itemCancelBtn");
    if (cancelBtn) {
      cancelBtn.addEventListener("click", () => {
        // 선택된 카테고리를 일반으로 바꾸고 화면 복구
        if (categorySelect) categorySelect.value = "1";
        if (itemContainer) itemContainer.style.display = "none";
        if (normalForm) normalForm.style.display = "block";
      });
    }
  }

  // 안전하게 이벤트 바인딩 (categorySelect가 없으면 아무 것도 하지 않음)
  if (categorySelect) {
    categorySelect.addEventListener("change", () => {
      const value = Number(categorySelect.value);

      if (value === 7) {
        if (normalForm) normalForm.style.display = "none";
        if (itemContainer) {
          itemContainer.style.display = "block";
          loadItemForm("icon");
        }
      }
      else if (value === 8) {
        if (normalForm) normalForm.style.display = "none";
        if (itemContainer) {
          itemContainer.style.display = "block";
          loadItemForm("background");
        }
      }
      else {
        if (itemContainer) itemContainer.style.display = "none";
        if (normalForm) normalForm.style.display = "block";
      }
    });

    // 페이지 로드시 이미 카테고리가 7 또는 8로 설정돼 있으면 폼을 보여주기
    (function checkInitialCategory() {
      const initVal = Number(categorySelect.value);
      if (initVal === 7) {
        if (normalForm) normalForm.style.display = "none";
        if (itemContainer) {
          itemContainer.style.display = "block";
          loadItemForm("icon");
        }
      } else if (initVal === 8) {
        if (normalForm) normalForm.style.display = "none";
        if (itemContainer) {
          itemContainer.style.display = "block";
          loadItemForm("background");
        }
      }
    })();
  }
  
  const post = window.POST_DATA;

// 동적 폼에 post 값 채우기
function fillDynamicItemForm() {
    if (!post || !itemContainer) return;

    const type = post.boardCategory === 7 ? "icon" :
                 post.boardCategory === 8 ? "background" : null;
    if (!type) return;

    // 이미 폼이 생성되었는지 체크
    const existingForm = itemContainer.querySelector(".item-write-form");
    if (!existingForm) {
        loadItemForm(type);
    }

    const form = itemContainer.querySelector(".item-write-form");
    if (!form) return;

    // 값 채우기
    const nameInput = form.querySelector('input[name="item_name"]');
    const priceInput = form.querySelector('input[name="item_price"]');

    if (nameInput) nameInput.value = post.boardTitle || "";
    if (priceInput) priceInput.value = post.boardContent || "";

    // 이미지 미리보기
    if (post.files && post.files.length > 0) {
        const previewDiv = document.createElement("div");
        previewDiv.innerHTML = `<img src="/uploads/${post.files[0].logicalFileName}" alt="이미지" width="100">`;
        const fileInput = form.querySelector('input[name="item_img"]');
        if (fileInput) form.insertBefore(previewDiv, fileInput);
    }
}

// 페이지 로드 시 카테고리 7/8이면 자동 폼 로드 후 채우기
const initVal = Number(categorySelect.value);
if (initVal === 7 || initVal === 8) {
    if (normalForm) normalForm.style.display = "none";
    if (itemContainer) {
        itemContainer.style.display = "block";
        fillDynamicItemForm();
    }
}

// 카테고리 변경 시도 채우기
categorySelect.addEventListener("change", () => {
    const val = Number(categorySelect.value);
    if (val === 7 || val === 8) {
        if (normalForm) normalForm.style.display = "none";
        if (itemContainer) {
            itemContainer.style.display = "block";
            fillDynamicItemForm();
        }
    } else {
        if (itemContainer) itemContainer.style.display = "none";
        if (normalForm) normalForm.style.display = "block";
    }
});
  

}); // DOMContentLoaded end

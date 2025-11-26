// write.js (수정된 전체 버전)
document.addEventListener("DOMContentLoaded", () => {
  // ✅ body에 write-page 클래스가 없으면 실행하지 않음
  if (!document.body.classList.contains("write-page")) return;

  // 4. 파일 업로드 시 파일명 표시
  const fileUpload = document.getElementById("fileUpload");
  if (fileUpload) {
    fileUpload.addEventListener("change", function () {
      const fileName = this.files.length ? this.files[0].name : "선택된 파일 없음";
      const fileNameSpan = document.querySelector(".file-name");
      if (fileNameSpan) fileNameSpan.textContent = fileName;
    });
  }

  // 5. 카테고리 별 추가 필드 처리
  const category = document.getElementById("category");
  const extra = document.getElementById("extraCategory");

  if (category && extra) {
    // renderExtra 정의 (대체/확장됨)
    function renderExtra(catValue, targetValue = null) {
      extra.innerHTML = ""; // 초기화

      if (catValue === "2") {
        // 코딩테스트
        extra.innerHTML = `
          <label for="lang">언어선택</label>
          <select id="lang" name="lang">
            <option>JAVA</option>
            <option>파이썬</option>
            <option>C</option>
            <option>C++</option>
            <option>PHP</option>
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

      if (catValue === "3") {
        // 기본 Q&A UI (회원/관리자 선택 가능)
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
            renderExtra("3", "member");
            // 그리고 카테고리 select 값도 보장
            const cat = document.getElementById("category");
            if (cat) cat.value = "3";
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

}); // DOMContentLoaded end

document.addEventListener('DOMContentLoaded', function() {
    // 1. 필요한 요소들을 가져옵니다.
    const selectAllCheckbox = document.getElementById('select-all');
    const termsCheckboxes = document.querySelectorAll('.terms-checkbox');
    const requiredCheckboxes = document.querySelectorAll('.terms-section input[required]');
    const nextBtn = document.getElementById('nextBtn');
    const form = document.querySelector('form');

    // 2. '전체 동의' 체크박스 이벤트 리스너
    selectAllCheckbox.addEventListener('change', function() {
        termsCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked; // 모든 체크박스 상태를 '전체 동의'와 동일하게 설정
        });
        checkRequiredTerms(); // 상태 변경 후 필수 약관 충족 여부 확인
    });

    // 3. 개별 체크박스 이벤트 리스너
    termsCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // 개별 체크박스 상태 변경 시 '전체 동의' 체크박스 상태 업데이트
            const allChecked = Array.from(termsCheckboxes).every(cb => cb.checked);
            selectAllCheckbox.checked = allChecked;

            checkRequiredTerms(); // 상태 변경 후 필수 약관 충족 여부 확인
        });
    });

    // 4. 필수 약관 충족 여부를 확인하고 '다음 단계' 버튼을 활성화/비활성화하는 함수
    function checkRequiredTerms() {
        // 필수(required) 체크박스만 배열로 만들어 모두 체크되었는지 확인
        const allRequiredChecked = Array.from(requiredCheckboxes).every(cb => cb.checked);

        if (allRequiredChecked) {
            // 모든 필수 약관이 동의된 경우
            nextBtn.style.pointerEvents = 'auto'; // 클릭 가능하게 변경
            nextBtn.style.opacity = '1.0';        // 시각적으로 활성화
            // nextBtn의 href를 form action으로 설정 (중요: 실제 서버 통신을 위해)
            nextBtn.setAttribute('href', '#'); // 실제 로직에서는 이 버튼을 클릭 시 form.submit()을 유도해야 합니다.
            nextBtn.classList.add('active'); // CSS 클래스 추가로 스타일 변경 가능
        } else {
            // 필수 약관 중 하나라도 동의되지 않은 경우
            nextBtn.style.pointerEvents = 'none'; // 클릭 불가
            nextBtn.style.opacity = '0.5';         // 비활성화
            nextBtn.classList.remove('active');
        }
    }
    
    // 5. '다음 단계' 버튼 클릭 시 폼 제출
    nextBtn.addEventListener('click', function(e) {
        if (nextBtn.style.pointerEvents === 'auto') {
             // <a> 태그의 기본 동작(페이지 이동)을 막고
             e.preventDefault(); 
             // 폼을 제출하도록 처리
             form.action = "/step2"; // form action URL 설정 (HTML form 태그에 이미 있지만, 안전성을 위해)
             form.submit();
        } else {
             e.preventDefault(); // 비활성화 상태에서는 클릭해도 페이지 이동 방지
        }
    });


    // 초기 로드 시 한 번 확인
    checkRequiredTerms();
});
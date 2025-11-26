document.addEventListener('DOMContentLoaded', function() {
    // 1. 요소 가져오기
    const selectAllCheckbox = document.getElementById('select-all');
    const termsCheckboxes = document.querySelectorAll('.terms-checkbox');
    const requiredCheckboxes = document.querySelectorAll('.terms-section input[required]');
    const nextBtn = document.getElementById('nextBtn');
    const form = document.querySelector('form');

    // 2. '전체 동의' 체크박스 이벤트
    selectAllCheckbox.addEventListener('change', function() {
        termsCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        checkRequiredTerms();
    });

    // 3. 개별 체크박스 이벤트
    termsCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const allChecked = Array.from(termsCheckboxes).every(cb => cb.checked);
            selectAllCheckbox.checked = allChecked;
            checkRequiredTerms();
        });
    });

    // 4. 필수 약관 확인 및 버튼 활성화 (핵심 수정 부분)
    function checkRequiredTerms() {
        const allRequiredChecked = Array.from(requiredCheckboxes).every(cb => cb.checked);

        if (allRequiredChecked) {
            // ✅ 수정됨: disabled 속성을 직접 false로 변경해야 클릭이 됩니다.
            nextBtn.disabled = false; 
            
            // 스타일 변경
            nextBtn.style.opacity = '1.0';
            nextBtn.style.cursor = 'pointer'; 
            nextBtn.classList.add('active');
        } else {
            // ✅ 수정됨: 다시 비활성화
            nextBtn.disabled = true;
            
            // 스타일 변경
            nextBtn.style.opacity = '0.5';
            nextBtn.style.cursor = 'not-allowed';
            nextBtn.classList.remove('active');
        }
    }

    
    // 초기 로드 시 상태 확인
    checkRequiredTerms();
});
document.addEventListener('DOMContentLoaded', () => {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm-password');

    function checkPasswordMatch() {
        if (password.value === confirmPassword.value) {
            // 일치
            confirmPassword.style.borderColor = 'green';
            // 사용자에게 피드백을 줄 메시지 요소가 있다면:
            //document.getElementById('password-match-message').textContent = '비밀번호가 일치합니다.';
        } else {
            // 불일치
            confirmPassword.style.borderColor = 'red';
            //document.getElementById('password-match-message').textContent = '비밀번호가 일치하지 않습니다.';
        }
    }

    password.addEventListener('keyup', checkPasswordMatch);
    confirmPassword.addEventListener('keyup', checkPasswordMatch);
});

// 기존 join-info.js 파일의 setupTagInput 함수 수정
function setupTagInput(inputId, tagBoxId, nameAttribute) {
    const input = document.getElementById(inputId);
    const tagBox = document.getElementById(tagBoxId);

    input.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // 폼 제출 방지
            const newTagText = input.value.trim();

            if (newTagText && newTagText.length > 0) {
                
                const newLabel = document.createElement('label');
                newLabel.className = 'tag active'; // 생성 시 active 클래스 부여 (선택)
                
                const newCheckbox = document.createElement('input');
                newCheckbox.type = 'checkbox';
                newCheckbox.name = nameAttribute; 
                newCheckbox.value = newTagText;
                newCheckbox.checked = true; 

                // 💡 새로운 span 요소를 생성하여 텍스트를 감쌉니다.
                const newSpan = document.createElement('span');
                newSpan.textContent = newTagText;

                newLabel.appendChild(newCheckbox);
                newLabel.appendChild(newSpan); // 💡 span 추가
                
                // (선택) active 클래스 토글 로직 추가
                newLabel.addEventListener('click', () => {
                     if (newCheckbox.checked) {
                        newLabel.classList.add('active');
                    } else {
                        newLabel.classList.remove('active');
                    }
                });

                tagBox.appendChild(newLabel);
                input.value = '';
            }
        }
    });
}

// 함수 호출
document.addEventListener('DOMContentLoaded', () => {
    setupTagInput('interest-input', 'interest-tags', 'interests');
    setupTagInput('skill-input', 'skill-tags', 'skills');
});
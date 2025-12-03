// join-find.js

// 아이디 찾기 - 인증코드 전송
document.getElementById("send-code-id").addEventListener("click", function () {
    const name = document.getElementById("name-id").value.trim();
    const email = document.getElementById("email-id").value.trim();

    if (!name || !email) {
        alert("이름과 이메일을 입력해주세요.");
        return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("email", email);

    fetch("/send-id-code", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        alert(data.msg);
    });
});

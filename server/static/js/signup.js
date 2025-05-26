// signup.js

document.addEventListener('DOMContentLoaded', function () {
  const clientIdInput = document.getElementById('client_id');
  const checkIdBtn = document.getElementById('check-id-btn');
  const idCheckMsg = document.getElementById('id-check-msg');

  const passwordInput = document.getElementById('password');
  const passwordConfirmInput = document.getElementById('password-check');
  const pwCheckMsg = document.getElementById('pw-check-msg');

  const form = document.getElementById('signup-form');

  // ID 중복 확인
  checkIdBtn.addEventListener("click", () => {
    const clientId = clientIdInput.value.trim();

    if (!clientId) {
      idCheckMsg.textContent = "아이디를 입력해주세요.";
      idCheckMsg.style.color = "red";
      return;
    }

    fetch(`/check_id?client_id=${encodeURIComponent(clientId)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.available) {
          idCheckMsg.textContent = "사용 가능한 아이디입니다.";
          idCheckMsg.style.color = "green";
        } else {
          idCheckMsg.textContent = "이미 사용 중인 아이디입니다.";
          idCheckMsg.style.color = "red";
        }
      })
      .catch((error) => {
        console.error("ID 중복 확인 오류:", error);
        idCheckMsg.textContent = "서버 오류가 발생했습니다.";
        idCheckMsg.style.color = "red";
      });
  });

  // 비밀번호 실시간 확인
  passwordConfirmInput.addEventListener('input', function () {
    const pw = passwordInput.value;
    const confirmPw = passwordConfirmInput.value;

    if (pw !== confirmPw) {
      pwCheckMsg.textContent = '비밀번호가 일치하지 않습니다.';
      pwCheckMsg.style.color = 'red';
    } else if (pw === '' || confirmPw === '') {
      pwCheckMsg.textContent = '';
    } else {
      pwCheckMsg.textContent = '비밀번호가 일치합니다.';
      pwCheckMsg.style.color = 'green';
    }
  });

  // 회원가입 제출 시 비밀번호 확인
  form.addEventListener('submit', function (event) {
    const pw = passwordInput.value;
    const confirmPw = passwordConfirmInput.value;

    if (pw !== confirmPw) {
      event.preventDefault(); // 제출 방지
      alert("비밀번호가 일치하지 않습니다.");
    }
  });
});

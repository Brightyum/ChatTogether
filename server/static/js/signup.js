document.addEventListener('DOMContentLoaded', function () {
  const clientIdInput = document.getElementById('client_id');
  const checkIdBtn = document.getElementById('check-id-btn');
  const idCheckMsg = document.getElementById('id-check-msg');

  const passwordInput = document.getElementById('password');
  const passwordConfirmInput = document.getElementById('password-confirm');
  const pwCheckMsg = document.getElementById('pw-check-msg');

  //  아이디 중복 확인
  checkIdBtn.addEventListener('click', function () {
    const clientId = clientIdInput.value;
    if (!clientId) {
      idCheckMsg.textContent = '아이디를 입력해주세요.';
      idCheckMsg.style.color = 'red';
      return;
    }

    fetch(`/check_id?client_id=${clientId}`)
      .then(res => res.json())
      .then(data => {
        if (data.exists) {
          idCheckMsg.textContent = '이미 사용 중인 아이디입니다.';
          idCheckMsg.style.color = 'red';
        } else {
          idCheckMsg.textContent = '사용 가능한 아이디입니다.';
          idCheckMsg.style.color = 'green';
        }
      })
      .catch(err => {
        idCheckMsg.textContent = '오류가 발생했습니다.';
        idCheckMsg.style.color = 'red';
      });
  });

  // 비밀번호 확인 실시간 비교
  passwordConfirmInput.addEventListener('input', function () {
    const pw = passwordInput.value;
    const confirmPw = passwordConfirmInput.value;
    if (pw !== confirmPw) {
      pwCheckMsg.textContent = '비밀번호가 일치하지 않습니다.';
      pwCheckMsg.style.color = 'red';
    } else {
      pwCheckMsg.textContent = '비밀번호가 일치합니다.';
      pwCheckMsg.style.color = 'green';
    }
  });
});

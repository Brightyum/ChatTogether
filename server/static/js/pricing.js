// 선택한 요금제를 저장하는 변수
let selectedPlan = null;

// 카드 선택 처리
function selectPlan(selectedCard) {
  const cards = document.querySelectorAll('.card');
  cards.forEach(card => card.classList.remove('selected'));
  selectedCard.classList.add('selected');

  selectedPlan = selectedCard.querySelector('h2').innerText;

  // 버튼 활성화
  document.getElementById('confirmPlan').disabled = false;
}

// 버튼 클릭 시 서버에 선택된 요금제 전달
document.addEventListener('DOMContentLoaded', () => {
  const confirmBtn = document.getElementById('confirmPlan');
  confirmBtn.addEventListener('click', () => {
    if (!selectedPlan) {
      alert('먼저 요금제를 선택해주세요.');
      return;
    }

    fetch('/select_plan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ plan: selectedPlan })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('요금제가 선택되었습니다: ' + selectedPlan);
        window.location.href = '/mypage';
      } else {
        alert('요금제 선택 중 오류: ' + data.message);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('서버 오류가 발생했습니다.');
    });
  });
});

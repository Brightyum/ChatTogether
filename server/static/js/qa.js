function handleSubmit(event) {
  event.preventDefault(); // 폼 새로고침 방지

  const input = document.getElementById("question-input");
  const question = input.value.trim();
  if (!question) return;

  fetch('/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question: question })
  })
  .then(response => response.json())
  .then(data => {
    const answerBox = document.querySelector('.answer-box p');
    answerBox.textContent = data.answer || "답변을 불러오지 못했습니다.";
  })
  .catch(error => {
    console.error("에러 발생:", error);
  });

  input.value = "";
}

 function toggleSidebar() {
      const sidebar = document.getElementById('sidebar');
      const main = document.getElementById('main');
      sidebar.classList.toggle('hidden');
      main.classList.toggle('expanded');
    }

const toggleButton = document.querySelector('.toggle-button');
const sidebar = document.querySelector('.sidebar');

toggleButton.addEventListener('click', () => {
  sidebar.classList.toggle('hidden');
});

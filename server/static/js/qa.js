const mode = document.body.dataset.mode;
const teamId = document.body.dataset.teamId !== "None" ? parseInt(document.body.dataset.teamId) : null;


function handleSubmit(event) {
  event.preventDefault(); // 폼 새로고침 방지

  const input = document.getElementById("question-input");
  const question = input.value.trim();
  if (!question) return;

  // 사용자 질문 로그에 추가
  appendToChatLog("user", question);
  input.value = ""; // 입력창 초기화

  const chatLog = document.getElementById("chat-log");

  // 응답용 placeholder 추가
  const botEntry = document.createElement("div");
  botEntry.classList.add("chat-entry", "bot-entry");
  botEntry.innerHTML = `<strong>🤖 ETA:</strong> <span class="streaming-text"></span>`;
  const streamSpan = botEntry.querySelector(".streaming-text");
  chatLog.appendChild(botEntry);
  chatLog.scrollTop = chatLog.scrollHeight;

 
  // 서버로 스트리밍 요청
  fetch("/stream-ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question: question, mode: mode, team_id: teamId  }),
  })
    .then((response) => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      function readChunk() {
        reader.read().then(({ done, value }) => {
          if (done) return;
          const chunk = decoder.decode(value, { stream: true });
          streamSpan.textContent += chunk;
          chatLog.scrollTop = chatLog.scrollHeight;
          readChunk();
        });
      }

      readChunk();
    })
    .catch((error) => {
      console.error("에러 발생:", error);
      streamSpan.textContent += "\n⚠️ 서버 오류로 응답을 받을 수 없습니다.";
    });
}

// 채팅 로그에 메시지 추가
function appendToChatLog(role, message) {
  const chatLog = document.getElementById("chat-log");

  const entry = document.createElement("div");
  entry.classList.add("chat-entry", role === "user" ? "user-entry" : "bot-entry");
  entry.innerHTML = `<strong>${role === "user" ? "👤 나" : "🤖 ETA"}:</strong> ${message}`;

  chatLog.appendChild(entry);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// 사이드바 토글 기능
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const main = document.getElementById("main");

  sidebar.classList.toggle("collapsed");
  main.classList.toggle("expanded");
}

// 사이드바 아이콘 클릭 시 토글
document.addEventListener("DOMContentLoaded", () => {
  const toggleButton = document.getElementById("toggleSidebar");
  const sidebar = document.getElementById("sidebar");

  toggleButton.addEventListener("click", () => {
    sidebar.classList.toggle("hidden");
  });

  // 폼 제출 이벤트 등록
  const form = document.querySelector(".input-box");
  if (form) {
    form.addEventListener("submit", handleSubmit);
  }
});




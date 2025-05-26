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

  if (toggleButton && sidebar) {
    toggleButton.addEventListener("click", () => {
      sidebar.classList.toggle("hidden");
    });
  }

  // 폼 제출 이벤트 등록
  const form = document.querySelector(".input-box");
  if (form) {
    form.addEventListener("submit", handleSubmit);
  }
});


//프롬프트 선택 이벤트 처리 함수
document.addEventListener("DOMContentLoaded", () => {
  // ⋮ 버튼 (드롭다운 메뉴) 처리
  const dropdowns = document.querySelectorAll(".dropdown");

  dropdowns.forEach(dropdown => {
    const button = dropdown.querySelector(".dropdown-btn");
    const menu = dropdown.querySelector(".dropdown-content");

    button.addEventListener("click", (e) => {
      e.stopPropagation();
      // 다른 메뉴 닫기
      document.querySelectorAll(".dropdown-content").forEach(m => {
        if (m !== menu) m.classList.remove("show");
      });
      menu.classList.toggle("show");
    });
  });

  // 바깥 클릭 시 메뉴 닫기
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown-content").forEach(menu => {
      menu.classList.remove("show");
    });
  });

  // 프롬프트 카드 클릭 시 서버로 전달
  const promptCards = document.querySelectorAll(".prompt-card");
  let selectedPrompt = null;

  promptCards.forEach(card => {
    card.addEventListener("click", (e) => {
      // ⋮ 버튼 및 드롭다운 클릭 시 제외
      if (e.target.classList.contains("dropdown-btn") || e.target.closest(".dropdown-content")) return;

      // 선택 표시: 기존 선택 해제
      promptCards.forEach(el => el.classList.remove("selected"));
      card.classList.add("selected");

      // 선택된 데이터 저장
      const title = card.querySelector(".prompt-title").innerText.trim();
      const descriptionElement = card.querySelector(".prompt-description");
      const content = descriptionElement ? descriptionElement.innerText.trim() : "";

      selectedPrompt = {
        title: title,
        content: content
      };

      // 선택 확인 메시지
      const confirmSelect = confirm(`"${selectedPrompt.title}" 프롬프트를 선택하시겠습니까?`);

      if (confirmSelect) {
        // 서버로 전달
        fetch('/select_prompt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(selectedPrompt)
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            alert(`"${selectedPrompt.title}" 프롬프트가 선택되었습니다.`);
          } else {
            alert('프롬프트 선택 중 오류: ' + data.message);
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('서버 오류가 발생했습니다.');
        });
      } else {
        // 선택 해제
        card.classList.remove("selected");
        selectedPrompt = null;
      }
    });
  });
});

document.querySelectorAll('.team-question').forEach(item => {
  item.addEventListener('click', event => {
    event.preventDefault();
    const topic = event.target.dataset.topic;

    fetch(`/get_conversation_data?topic=${encodeURIComponent(topic)}`)
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const chatLog = document.getElementById("chat-log");
          chatLog.innerHTML = ""; // 기존 대화 내용 비우기

          data.data.forEach(entry => {
            const userMsg = document.createElement("div");
            userMsg.className = "chat-entry user-entry";
            userMsg.innerHTML = `<strong>👤 사용자:</strong> ${entry.Personal_Asw}`;
            chatLog.appendChild(userMsg);

            const botMsg = document.createElement("div");
            botMsg.className = "chat-entry bot-entry";
            botMsg.innerHTML = `<strong>🤖 ETA:</strong> ${entry.Personal_Rsp}`;
            chatLog.appendChild(botMsg);
          });

          chatLog.scrollTop = chatLog.scrollHeight;

          // ✅ 추가: 서버에 대화 기록 등록 요청
          fetch("/load_conversation_to_memory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              conversation_data: data.data,
              team_id: teamId  // 상단 const teamId = ... 선언된 값 사용
            })
          })
          .then(response => response.json())
          .then(result => {
            if (result.success) {
              console.log("✅ 대화 기록이 ChatSystem 메모리에 등록되었습니다.");
            } else {
              console.error("❌ 메모리 등록 실패:", result.message);
            }
          })
          .catch(error => {
            console.error("❌ 메모리 등록 요청 실패:", error);
          });
          // ✅ 추가 끝

        } else {
          alert(data.message);
        }
      });
  });
});
const chatToggle = document.querySelector(".chat-toggle");
const chatbox = document.querySelector(".chatbox");
const messagesBox = document.querySelector(".chatbox-messages");
const inputField = document.getElementById("chat-input");

/* =========================
   TOGGLE CHAT
========================= */
chatToggle.addEventListener("click", () => {
  chatbox.style.display =
    chatbox.style.display === "flex" ? "none" : "flex";
});

/* =========================
   SEND MESSAGE
========================= */
function sendMessage() {
  const message = inputField.value.trim();
  if (!message) return;

  addUserMessage(message);
  inputField.value = "";

  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  })
    .then(res => res.json())
    .then(data => {
      addBotMessage(data.reply);
    })
    .catch(() => {
      addBotMessage("⚠️ Server not responding");
    });
}

/* =========================
   UI HELPERS
========================= */
function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "msg-user";
  div.innerText = text;
  messagesBox.appendChild(div);
  scrollToBottom();
}

function addBotMessage(text) {
  const div = document.createElement("div");
  div.className = "msg-bot";
  div.innerText = text;
  messagesBox.appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  messagesBox.scrollTop = messagesBox.scrollHeight;
}

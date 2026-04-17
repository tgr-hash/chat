# =========================
# 📦 IMPORTS
# =========================
import asyncio
import websockets
import json
import time
import os
PORT = int(os.environ.get("PORT", 8000))
from aiohttp import web

async def main():
    app = web.Application()

    # serve your HTML page
    async def index(request):
        return web.Response(text=HTML, content_type="text/html")

    # websocket endpoint
    async def websocket_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        clients.add(ws)

        ws.name = None  # track username

        # send history
        await ws.send_str(json.dumps(messages))

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)

                 # handle kick
                if data.get("type") == "kick":
                    target = data.get("target")

                    for c in list(clients):
                        if getattr(c, "name", None) == target:
                            await c.send_str(json.dumps([{
                                "type": "kick",
                                "msg": "You were kicked"
                            }]))
                            await c.close()

                    continue
                


                if data.get("type") == "typing":
                    for c in list(clients):
                        if c != ws:
                            await c.send_str(json.dumps({
                                "type": "typing",
                                "name": ws.name
                            }))
                    continue

                if data.get("type") == "private_msg":
                    ws.name = data.get("name", "anon")
                    await send_user_list()

                    target = data.get("target")
                    event = {
                        "name": data.get("name", "anon"),
                        "msg": data.get("msg", ""),
                        "type": "private_msg",
                        "time": time.time(),
                        "color": data.get("color", "#ffffff"),
                        "target": target
                    }

                    recipients = []
                    for c in list(clients):
                        if c == ws or getattr(c, "name", None) == target:
                            recipients.append(c)

                    delivered = set()
                    for c in recipients:
                        if c in delivered:
                            continue
                        await c.send_str(json.dumps([event]))
                        delivered.add(c)

                    continue


                if data.get("type") != "kick":
                    ws.name = data.get("name", "anon")
                    await send_user_list()
                event = {
                  "name": data.get("name", "anon"),
                  "msg": data.get("msg", ""),
                  "type": data.get("type", "msg"),
                  "time": time.time(),
                  "color": data.get("color", "#ffffff")
                }

                messages.append(event)
                save()

                for c in list(clients):
                    await c.send_str(json.dumps([event]))

        clients.remove(ws)
        await send_user_list()
        return ws

    app.router.add_get("/", index)
    app.router.add_get("/ws", websocket_handler)

    # serve static files (games, etc)
    app.router.add_static("/static/", path="Static", show_index=True)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"Running on port {PORT}")

    while True:
        await asyncio.sleep(3600)

# =========================
# ⚙️ CONFIG
# =========================
FILE = "/tmp/messages.json"

clients = set()

async def send_user_list():
    users = [
        {
            "name": getattr(c, "name", None),
        }
        for c in clients
        if getattr(c, "name", None)
    ]

    payload = json.dumps({
        "type": "users",
        "users": users
    })

    for c in list(clients):
        await c.send_str(payload)

# =========================
# 📁 FILE SETUP
# =========================
if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump([], f)

with open(FILE, "r") as f:
    messages = json.load(f)

def save():
    with open(FILE, "w") as f:
        json.dump(messages, f)

async def broadcast(data):
    for c in list(clients):
        try:
            await c.send_str(data)
        except:
            clients.remove(c)

# =========================
# 💬 FRONTEND HTML
# =========================

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Chat</title>

<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans&display=swap" rel="stylesheet">

<style>
body { margin:0; font-family:'Pixelify Sans'; background:white; }

.kickBtn {
  margin-left:auto;
  background:red;
  color:white;
  border:none;
  padding:4px 8px;
  cursor:pointer;
  font-size:10px;
  flex-shrink:0;
}

.kickBtn:hover {
  opacity:0.8;
}

.messageBtn {
  background:black;
  color:white;
  border:none;
  padding:4px 8px;
  cursor:pointer;
  font-size:10px;
  flex-shrink:0;
}

.messageBtn:hover {
  opacity:0.8;
}

#login {
  display:flex;
  justify-content:center;
  align-items:center;
  height:100vh;
  flex-direction:column;
}

#login input {
  margin:10px;
  padding:10px;
}

#login button {
  padding:10px;
  background:black;
  color:white;
  border:none;
}

#chatPage { display:none; }

#chat {
  padding:20px;
  height:85vh;
  overflow-y:auto;
}

#logoutBtn {
  position: fixed;
  top: 10px;
  right: 10px;
  padding: 8px 12px;
  background: black;
  color: white;
  border: none;
  font-family: 'Pixelify Sans';
  cursor: pointer;
  z-index: 1000;
}

#logoutBtn:hover {
  opacity: 0.8;
}

#gameBtn {
  position: fixed;
  top: 50px; /* sits below logout */
  right: 10px;
  padding: 8px 12px;
  background: black;
  color: white;
  border: none;
  font-family: 'Pixelify Sans';
  cursor: pointer;
  z-index: 1000;
}

#gameBtn:hover {
  opacity: 0.8;
}

.msg {
  margin:8px 0;
  padding:10px;
  border-radius:10px;
  max-width:60%;
  background:black;
  color:white;
  display:flex;
  align-items:center;
  gap:8px;
}

.dot {
  width:10px;
  height:10px;
  border-radius:50%;
}

.event {
  margin:6px 0;
  color:gray;
  font-size:12px;
  text-align:center;
}

#bar {
  position:fixed;
  bottom:0;
  width:100%;
  display:flex;
  border-top:1px solid #ddd;
}

#msg {
  flex:1;
  padding:12px;
  border:none;
  outline:none;
}

button {
  padding:12px;
  background:black;
  color:white;
  border:none;
}
</style>
</head>

<body>

<div id="login">
  <h2>Login</h2>
  <input id="name" placeholder="name">
  <input id="pass" type="password" placeholder="password">
  <input id="color" placeholder="#ffffff (optional)">
  <button id="loginBtn">Enter</button>
</div>

<div id="chatPage">
  <button id="logoutBtn">Logout</button>
  <button id="gameBtn">Play game instead</button>
  <div style="display:flex;">
  <div id="sidebar" style="width:280px; border-right:1px solid #ddd; padding:10px;">
    <h3>Users</h3>
    <div id="users"></div>
  </div>

  <div style="flex:1;">
    <div id="privateBanner" style="display:none; margin:12px 20px 0; padding:10px 12px; background:#f3f3f3; border:1px solid #ddd; align-items:center; justify-content:space-between; gap:10px;">
      <span id="privateBannerText"></span>
      <button id="clearPrivateBtn" style="padding:8px 10px;">Back to everyone</button>
    </div>
    <div id="chat"></div>
    <div id="typing" style="font-size:12px; color:gray; padding-left:20px;"></div>
  </div>
</div>

  <div id="bar">
    <input id="msg" placeholder="message...">
    <button onclick="send()">Send</button>
  </div>
</div>

<script>
let name = "";
let color = "#ffffff";
let ws;
let isAdmin = false;
let privateTarget = null;

// =========================
// LOGIN
// =========================
document.getElementById("loginBtn").addEventListener("click", login);

function login(){
  const n = document.getElementById("name").value.trim();
  const p = document.getElementById("pass").value.trim();
  let c = document.getElementById("color").value.trim();

  if(p === "yourdad"){
    alert("admin login");
    isAdmin = true;
  } else if(p === "yourmom"){
    isAdmin = false;
  } else {
    alert("wrong password");
    return;
  }

  if(!n) return;

  if(/^#([0-9A-Fa-f]{6})$/.test(c)){
    color = c;
  }

  name = n;

  localStorage.setItem("chat_name", name);
  localStorage.setItem("chat_color", color);

  startChat();
}

// =========================
// START CHAT
// =========================
function startChat(){
  document.getElementById("login").style.display = "none";
  document.getElementById("chatPage").style.display = "block";

  connectWebSocket();
}

// =========================
// WEBSOCKET
// =========================
function connectWebSocket(){
  ws = new WebSocket(
  (location.protocol === "https:" ? "wss://" : "ws://") +
  location.host +
  "/ws"
);

  ws.onopen = () => {
    console.log("WS CONNECTED");

    ws.send(JSON.stringify({
      type: "event",
      name,
      msg: name + " joined",
      color
    }));
  };

  let isFirstLoad = true;

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const chat = document.getElementById("chat");

  const messages = Array.isArray(data) ? data : [data];

  // 🚫 hide history if not admin
  if(isFirstLoad && !isAdmin){
    isFirstLoad = false;
    return;
  }

  isFirstLoad = false;

  messages.forEach((m, i) => {

  // USER LIST UPDATE
  if(m.type === "users"){
    const usersDiv = document.getElementById("users");
    usersDiv.innerHTML = "";

    m.users.forEach(u => {
      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.marginBottom = "6px";
      row.style.gap = "6px";

      const safeName = JSON.stringify(u.name);
      row.innerHTML = `
        <span class="dot" style="background:white;"></span>
        <span style="flex:1; word-break:break-word;">${u.name}</span>
        ${u.name !== name ? `<button class="messageBtn" onclick='startPrivateMessage(${safeName})'>message</button>` : ""}
        ${isAdmin ? `<button class="kickBtn" onclick='kickUser(${safeName})'>Kick</button>` : ""}
      `;

      usersDiv.appendChild(row);
    });

    return;
  }

  // TYPING INDICATOR
  if(m.type === "typing"){
    const typingDiv = document.getElementById("typing");
    typingDiv.textContent = m.name + " is typing...";

    clearTimeout(window._typingTimeout);
    window._typingTimeout = setTimeout(() => {
      typingDiv.textContent = "";
    }, 1500);

    return;
  }

  if(m.type === "kick"){
    alert("You were kicked");
    logout();
    return;
  }
const div = document.createElement("div");
div.dataset.index = i;

if (m.type === "event") {
  div.className = "event";
  div.textContent = `[${formatTime(m.time)}] ${m.msg}`;
} else {
  div.className = "msg";
  const privateLabel = m.type === "private_msg"
    ? (m.name === name ? ` <span style="font-size:12px; opacity:0.8;">(to ${m.target})</span>` : ` <span style="font-size:12px; opacity:0.8;">(private)</span>`)
    : "";

  div.innerHTML = `
    <span class="dot" style="background:${m.color}"></span>
    <span><b>${m.name}</b>${privateLabel}: ${m.msg}</span>
  `;
}

  if(m.reactions){
    for(const [emoji, count] of Object.entries(m.reactions)){
      reactionHTML += `<span style="margin-left:6px;font-size:12px;">${emoji} ${count}</span>`;
    }
  }

    chat.appendChild(div);
  });

  chat.scrollTop = chat.scrollHeight;
};

  ws.onerror = (err) => {
    console.error("WS error:", err);
  };
}

// =========================
// SEND
// =========================
function kickUser(target){
  if(!isAdmin) return;

  ws.send(JSON.stringify({
    type: "kick",
    target
  }));
}

function startPrivateMessage(target){
  privateTarget = target;
  updatePrivateBanner();
  const msgInput = document.getElementById("msg");
  msgInput.placeholder = `message ${target}...`;
  msgInput.focus();
}

function clearPrivateMessage(){
  privateTarget = null;
  updatePrivateBanner();
  document.getElementById("msg").placeholder = "message...";
}

function updatePrivateBanner(){
  const banner = document.getElementById("privateBanner");
  const text = document.getElementById("privateBannerText");

  if(privateTarget){
    banner.style.display = "flex";
    text.textContent = `Private messaging ${privateTarget}`;
  } else {
    banner.style.display = "none";
    text.textContent = "";
  }
}

function send(){
  const msgEl = document.getElementById("msg");
  const msg = msgEl.value.trim();
  if(!msg) return;

  // =========================
  // COMMAND SYSTEM
  // =========================
  if(msg.startsWith("/")){
    handleCommand(msg);
    msgEl.value = "";
    return;
  }

  ws.send(JSON.stringify({
    type: privateTarget ? "private_msg" : "msg",
    name,
    msg,
    color,
    target: privateTarget
  }));

  msgEl.value = "";
}

function handleCommand(msg){
  const parts = msg.split(" ");
  const cmd = parts[0];

  if(cmd === "/clear"){
    document.getElementById("chat").innerHTML = "";
    return;
  }

  if(cmd === "/help"){
    alert("/clear /help /roll /color");
    return;
  }

  if(cmd === "/roll"){
    const range = parts[1]?.split("-") || ["1","100"];
    const min = parseInt(range[0]);
    const max = parseInt(range[1]);
    const result = Math.floor(Math.random()*(max-min+1))+min;

    ws.send(JSON.stringify({
      type:"msg",
      name:"system",
      msg:`🎲 ${result}`,
      color:"#888"
    }));
    return;
  }

  if(cmd === "/color"){
    const c = parts[1];
    if(/^#([0-9A-Fa-f]{6})$/.test(c)){
      color = c;
      localStorage.setItem("chat_color", color);
    }
    return;
  }
}

// ENTER KEY
let lastTyping = 0;

document.getElementById("msg").addEventListener("keydown", (e) => {
  const now = Date.now();

  if(now - lastTyping > 500){
    ws.send(JSON.stringify({
      type: "typing",
      name
    }));
    lastTyping = now;
  }
  if(e.key === "Enter"){
    e.preventDefault();
    send();
  }
});

document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("clearPrivateBtn").addEventListener("click", clearPrivateMessage);
document.getElementById("gameBtn").addEventListener("click", () => {
  window.location.href = "/static/games.html";
});

function logout(){
  // send leave event
  if(ws){
    ws.send(JSON.stringify({
      type: "event",
      name,
      msg: name + " left",
      color
    }));
    ws.close();
  }

  // clear local storage
  localStorage.removeItem("chat_name");
  localStorage.removeItem("chat_color");

  // reset UI
  document.getElementById("chatPage").style.display = "none";
  document.getElementById("login").style.display = "flex";

  // clear chat visually (optional but cleaner)
  document.getElementById("chat").innerHTML = "";
  document.getElementById("users").innerHTML = "";
  document.getElementById("typing").textContent = "";
  clearPrivateMessage();

  // reset state
  name = "";
  color = "#ffffff";
}

// =========================
// AUTO LOGIN
// =========================
window.onload = () => {
  const savedName = localStorage.getItem("chat_name");
  const savedColor = localStorage.getItem("chat_color");

  if(savedName){
    name = savedName;
    color = savedColor || "#ffffff";
    startChat();
  }
};

// =========================
// TIME FORMAT
// =========================
function formatTime(t){
  const d = new Date(t * 1000);
  return isNaN(d) ? "" : d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });
}
</script>

<!-- Floating AI Assistant Widget: paste near the end of your page, just before </body> -->
<div class="oa-widget" id="oaWidget">
  <div class="oa-widget__panel" id="oaWidgetPanel" aria-hidden="true">
    <div class="oa-widget__header">
      <span class="oa-widget__title">AI Assistant</span>
      <button
        type="button"
        class="oa-widget__close"
        id="oaWidgetClose"
        aria-label="Close chat"
      >
        ×
      </button>
    </div>

    <div class="oa-widget__messages" id="oaWidgetMessages">
      <div class="oa-widget__message oa-widget__message--ai">
        Hi! Ask me something.
      </div>
    </div>

    <form class="oa-widget__form" id="oaWidgetForm">
      <input
        type="text"
        id="oaWidgetInput"
        class="oa-widget__input"
        placeholder="Type your message..."
        autocomplete="off"
        required
      />
      <button type="submit" class="oa-widget__send" id="oaWidgetSend">
        Send
      </button>
    </form>
  </div>

  <button
    type="button"
    class="oa-widget__toggle"
    id="oaWidgetToggle"
    aria-label="Open AI assistant"
    aria-expanded="false"
    aria-controls="oaWidgetPanel"
  >
    AI
  </button>
</div>

<style>
  /* Isolated widget styles with oa-widget prefix to avoid site CSS conflicts */
  .oa-widget,
  .oa-widget * {
    box-sizing: border-box;
  }

  .oa-widget {
    position: fixed;
    right: 20px;
    bottom: 20px;
    z-index: 9999;
    font-family: Arial, sans-serif;
  }

  .oa-widget__panel {
    width: min(360px, calc(100vw - 24px));
    height: min(520px, calc(100vh - 100px));
    display: flex;
    flex-direction: column;
    margin-bottom: 12px;
    background: #ffffff;
    border: 1px solid #d9d9d9;
    border-radius: 16px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.18);
    overflow: hidden;
    opacity: 0;
    transform: translateY(16px) scale(0.98);
    pointer-events: none;
    visibility: hidden;
    transition:
      opacity 0.22s ease,
      transform 0.22s ease,
      visibility 0.22s ease;
  }

  .oa-widget__panel.is-open {
    opacity: 1;
    transform: translateY(0) scale(1);
    pointer-events: auto;
    visibility: visible;
  }

  .oa-widget__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    background: #111111;
    color: #ffffff;
  }

  .oa-widget__title {
    font-size: 16px;
    font-weight: 700;
    line-height: 1.2;
  }

  .oa-widget__close {
    border: 0;
    background: transparent;
    color: #ffffff;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    padding: 0;
  }

  .oa-widget__messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: #f7f7f7;
    scroll-behavior: smooth;
  }

  .oa-widget__message {
    max-width: 85%;
    margin-bottom: 12px;
    padding: 10px 12px;
    border-radius: 12px;
    line-height: 1.45;
    font-size: 14px;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .oa-widget__message--user {
    margin-left: auto;
    background: #111111;
    color: #ffffff;
    border-bottom-right-radius: 4px;
  }

  .oa-widget__message--ai {
    margin-right: auto;
    background: #e9e9e9;
    color: #111111;
    border-bottom-left-radius: 4px;
  }

  .oa-widget__message--system {
    margin-right: auto;
    background: #fff4e5;
    color: #7a4b00;
    border: 1px solid #ffd6a0;
  }

  .oa-widget__typing {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #555555;
  }

  .oa-widget__typing-dots {
    display: inline-flex;
    gap: 4px;
  }

  .oa-widget__typing-dots span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #777777;
    animation: oaWidgetBlink 1.2s infinite ease-in-out;
  }

  .oa-widget__typing-dots span:nth-child(2) {
    animation-delay: 0.15s;
  }

  .oa-widget__typing-dots span:nth-child(3) {
    animation-delay: 0.3s;
  }

  @keyframes oaWidgetBlink {
    0%, 80%, 100% {
      opacity: 0.3;
      transform: scale(0.9);
    }
    40% {
      opacity: 1;
      transform: scale(1);
    }
  }

  .oa-widget__form {
    display: flex;
    gap: 8px;
    padding: 12px;
    border-top: 1px solid #e5e5e5;
    background: #ffffff;
  }

  .oa-widget__input {
    flex: 1;
    min-width: 0;
    border: 1px solid #cccccc;
    border-radius: 10px;
    padding: 10px 12px;
    font: inherit;
    font-size: 14px;
    color: #111111;
    background: #ffffff;
    outline: none;
  }

  .oa-widget__input:focus {
    border-color: #111111;
  }

  .oa-widget__send,
  .oa-widget__toggle {
    border: 0;
    cursor: pointer;
    font: inherit;
  }

  .oa-widget__send {
    padding: 10px 14px;
    border-radius: 10px;
    background: #111111;
    color: #ffffff;
    white-space: nowrap;
  }

  .oa-widget__send:disabled,
  .oa-widget__input:disabled {
    opacity: 0.65;
    cursor: not-allowed;
  }

  .oa-widget__toggle {
    width: 60px;
    height: 60px;
    margin-left: auto;
    border-radius: 999px;
    background: #111111;
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.22);
  }

  @media (max-width: 640px) {
    .oa-widget {
      right: 12px;
      bottom: 12px;
      left: 12px;
    }

    .oa-widget__panel {
      width: 100%;
      height: min(70vh, 500px);
      margin-bottom: 10px;
    }

    .oa-widget__toggle {
      width: 56px;
      height: 56px;
    }
  }
</style>

<script>
  (function () {
    "use strict";

    // Widget element references
    var widgetPanel = document.getElementById("oaWidgetPanel");
    var widgetToggle = document.getElementById("oaWidgetToggle");
    var widgetClose = document.getElementById("oaWidgetClose");
    var widgetForm = document.getElementById("oaWidgetForm");
    var widgetInput = document.getElementById("oaWidgetInput");
    var widgetSend = document.getElementById("oaWidgetSend");
    var widgetMessages = document.getElementById("oaWidgetMessages");

    if (
      !widgetPanel ||
      !widgetToggle ||
      !widgetClose ||
      !widgetForm ||
      !widgetInput ||
      !widgetSend ||
      !widgetMessages
    ) {
      return;
    }

    // Opens the chat panel with animation and focuses the input
    function openWidget() {
      widgetPanel.classList.add("is-open");
      widgetPanel.setAttribute("aria-hidden", "false");
      widgetToggle.setAttribute("aria-expanded", "true");
      widgetInput.focus();
      scrollToBottom();
    }

    // Closes the chat panel
    function closeWidget() {
      widgetPanel.classList.remove("is-open");
      widgetPanel.setAttribute("aria-hidden", "true");
      widgetToggle.setAttribute("aria-expanded", "false");
    }

    // Toggles panel open/closed
    function toggleWidget() {
      if (widgetPanel.classList.contains("is-open")) {
        closeWidget();
      } else {
        openWidget();
      }
    }

    // Keeps the latest message visible
    function scrollToBottom() {
      widgetMessages.scrollTop = widgetMessages.scrollHeight;
    }

    // Creates and inserts a message bubble
    function addMessage(text, type) {
      var message = document.createElement("div");
      message.className = "oa-widget__message oa-widget__message--" + type;
      message.textContent = text;
      widgetMessages.appendChild(message);
      scrollToBottom();
      return message;
    }

    // Shows a temporary typing indicator while the AI request is running
    function addTypingIndicator() {
      var typingMessage = document.createElement("div");
      typingMessage.className = "oa-widget__message oa-widget__message--ai";
      typingMessage.id = "oaWidgetTypingIndicator";
      typingMessage.innerHTML =
        '<span class="oa-widget__typing">' +
        "<span>AI is thinking...</span>" +
        '<span class="oa-widget__typing-dots" aria-hidden="true">' +
        "<span></span><span></span><span></span>" +
        "</span>" +
        "</span>";

      widgetMessages.appendChild(typingMessage);
      scrollToBottom();
      return typingMessage;
    }

    // Enables or disables input controls during requests
    function setLoadingState(isLoading) {
      widgetInput.disabled = isLoading;
      widgetSend.disabled = isLoading;
      widgetSend.textContent = isLoading ? "..." : "Send";
    }

    widgetToggle.addEventListener("click", toggleWidget);
    widgetClose.addEventListener("click", closeWidget);

    // Optional: close with Escape for better UX
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && widgetPanel.classList.contains("is-open")) {
        closeWidget();
      }
    });

    widgetForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      var prompt = widgetInput.value.trim();
      if (!prompt) {
        return;
      }

      addMessage(prompt, "user");
      widgetInput.value = "";
      setLoadingState(true);

      var typingIndicator = addTypingIndicator();

      try {
        var response = await fetch("http://localhost:11434/api/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            model: "llama3:latest",
            prompt: prompt,
            stream: false
          })
        });

        if (!response.ok) {
          throw new Error("Request failed with status " + response.status + ".");
        }

        var data = await response.json();
        var aiText = data && typeof data.response === "string"
          ? data.response.trim()
          : "";

        if (!aiText) {
          throw new Error("The AI returned an empty response.");
        }

        if (typingIndicator && typingIndicator.parentNode) {
          typingIndicator.parentNode.removeChild(typingIndicator);
        }

        addMessage(aiText, "ai");
      } catch (error) {
        if (typingIndicator && typingIndicator.parentNode) {
          typingIndicator.parentNode.removeChild(typingIndicator);
        }

        var message = "Sorry, something went wrong.";

        // Keep API logic the same, only improve how errors are surfaced
        if (error && error.message) {
          message += " " + error.message;
        }

        addMessage(message, "system");
      } finally {
        setLoadingState(false);
        widgetInput.focus();
        scrollToBottom();
      }
    });
  })();
</script>


</body>
</html>
"""

# =========================
# HTTP SERVER
# =========================


asyncio.run(main())

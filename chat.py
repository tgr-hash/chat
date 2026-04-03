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



                if data.get("type") == "react":
                    idx = data.get("index")
                    emoji = data.get("emoji")

                    if 0 <= idx < len(messages):
                        msg = messages[idx]

                        if "reactions" not in msg:
                            msg["reactions"] = {}

                        msg["reactions"][emoji] = msg["reactions"].get(emoji, 0) + 1
                        save()

                        await broadcast(json.dumps([{
                            "type": "reaction_update",
                            "index": idx,
                            "emoji": emoji,
                            "count": msg["reactions"][emoji]
                        }]))

                    continue


                if data.get("type") == "typing":
                    for c in list(clients):
                        if c != ws:
                            await c.send_str(json.dumps({
                                "type": "typing",
                                "name": ws.name
                            }))
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
    if clients:
        await asyncio.gather(*[c.send(data) for c in clients])

# =========================
# 🌐 WEBSOCKET SERVER
# =========================
async def handler(ws):
    clients.add(ws)

    ws.name = None  # track username

    try:
        await ws.send(json.dumps(messages))
        async for msg in ws:
            data = json.loads(msg)

            event = {
                "name": data.get("name", "anon"),
               "msg": data.get("msg", ""),
               "type": data.get("type", "msg"),
                "time": time.time(),
                "color": data.get("color", "#ffffff"),
                "reactions": {}   # NEW
            }

            messages.append(event)
            save()

            await broadcast(json.dumps([event]))

    except:
        pass
    finally:
        clients.remove(ws)

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
  <div id="sidebar" style="width:200px; border-right:1px solid #ddd; padding:10px;">
    <h3>Users</h3>
    <div id="users"></div>
  </div>

  <div style="flex:1;">
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

  messages.forEach(m => {

  // USER LIST UPDATE
  if(m.type === "users"){
    const usersDiv = document.getElementById("users");
    usersDiv.innerHTML = "";

    m.users.forEach(u => {
      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.marginBottom = "6px";

      row.innerHTML = `
        <span class="dot" style="background:white; margin-right:6px;"></span>
        <span>${u.name}</span>
        ${isAdmin ? `<button class="kickBtn" onclick="kickUser('${u.name}')">Kick</button>` : ""}
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

if(m.type === "event"){
  div.className = "event";
  div.textContent = `[${formatTime(m.time)}] ${m.msg}`;
} else {
  div.className = "msg";

  let reactionHTML = "";

  if(m.reactions){
    for(const [emoji, count] of Object.entries(m.reactions)){
      reactionHTML += `<span style="margin-left:6px;font-size:12px;">${emoji} ${count}</span>`;
    }
  }

  div.innerHTML = `
    <span class="dot" style="background:${m.color}"></span>
    <b>${m.name}</b>: ${m.msg}
    <div class="reactions">${reactionHTML}</div>
    <div class="reactBar" style="display:none; gap:5px; margin-top:4px;">
      <button onclick="react(${i}, '👍')">👍</button>
      <button onclick="react(${i}, '😂')">😂</button>
      <button onclick="react(${i}, '🔥')">🔥</button>
    </div>
  `;

  div.onmouseenter = () => {
    div.querySelector(".reactBar").style.display = "flex";
  };

  div.onmouseleave = () => {
    div.querySelector(".reactBar").style.display = "none";
  };
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
    type: "msg",
    name,
    msg,
    color
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

function react(index, emoji){
  ws.send(JSON.stringify({
    type: "react",
    index,
    emoji
  }));
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

</body>
</html>
"""

# =========================
# HTTP SERVER
# =========================


asyncio.run(main())
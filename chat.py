# =========================
# 📦 IMPORTS
# =========================
import asyncio
import websockets
import json
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# =========================
# ⚙️ CONFIG
# =========================
import os
PORT = int(os.environ.get("PORT", 10000))
FILE = "messages.json"

clients = set()

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

    try:
        await ws.send(json.dumps(messages))

        async for msg in ws:
            data = json.loads(msg)

            event = {
                "name": data.get("name", "anon"),
                "msg": data.get("msg", ""),
                "type": data.get("type", "msg"),
                "time": time.time(),
                "color": data.get("color", "#ffffff")
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
  <div id="chat"></div>

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
  (location.protocol === "https:" ? "wss://" : "ws://") + location.host
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
    const div = document.createElement("div");

    if(m.type === "event"){
      div.className = "event";
      div.textContent = `[${formatTime(m.time)}] ${m.msg}`;
    } else {
      div.className = "msg";
      div.innerHTML = `
        <span class="dot" style="background:${m.color}"></span>
        <b>${m.name}</b>: ${m.msg}
      `;
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
function send(){
  const msgEl = document.getElementById("msg");
  const msg = msgEl.value.trim();
  if(!msg) return;

  ws.send(JSON.stringify({
    type: "msg",
    name,
    msg,
    color
  }));

  msgEl.value = "";
}

// ENTER KEY
document.getElementById("msg").addEventListener("keydown", (e) => {
  if(e.key === "Enter"){
    e.preventDefault();
    send();
  }
});

document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("gameBtn").addEventListener("click", () => {
  window.location.href = "/games.html";
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
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path

        # homepage (chat)
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
            return

        # serve static files
        file_path = "static" + path

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)

            if file_path.endswith(".html"):
                self.send_header("Content-type", "text/html")
            elif file_path.endswith(".js"):
                self.send_header("Content-type", "application/javascript")
            elif file_path.endswith(".css"):
                self.send_header("Content-type", "text/css")
            elif file_path.endswith(".png"):
                self.send_header("Content-type", "image/png")
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                self.send_header("Content-type", "image/jpeg")
            elif file_path.endswith(".gif"):
                self.send_header("Content-type", "image/gif")

            self.end_headers()

            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

# =========================
# START SERVERS
# =========================

import os
import asyncio
import websockets

PORT = int(os.environ.get("PORT", 8000))

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Server</title>
</head>
<body>
    <h1>WebSocket Chat</h1>
    <input id="msg" placeholder="message">
    <button onclick="sendMsg()">Send</button>

    <script>
        const ws = new WebSocket("wss://" + window.location.host);

        ws.onmessage = (event) => {
            console.log("Received:", event.data);
        };

        function sendMsg() {
            const input = document.getElementById("msg");
            ws.send(input.value);
            input.value = "";
        }
    </script>
</body>
</html>
"""

connected = set()

async def handler(websocket):
    connected.add(websocket)
    try:
        async for message in websocket:
            for conn in connected:
                await conn.send(message)
    finally:
        connected.remove(websocket)


async def main():
    async def ws_handler(websocket, path=None):
        if path is None or path == "/":
            await handler(websocket)

    ws_server = await websockets.serve(ws_handler, "0.0.0.0", PORT)

    print(f"Server running on port {PORT}")
    await ws_server.wait_closed()

asyncio.run(main())

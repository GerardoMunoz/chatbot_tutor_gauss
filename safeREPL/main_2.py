# main.py (versión simplificada, solo chat privado)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import hashlib
import json
import os
#from bots.gauss_bot import GaussBot 
from safeREPL import SafeREPL
from matrix_op import Matrix_op
from det_op import Det_op


#Ans.op('r1<->r2')
app = FastAPI()

newline = '<br>'
connections = []
user_sessions = {}       # { ws: email }
chatbots = {}            # { ws: ChatManager }
safe_env = {
    "Det":Det_op,
    "Matrix": Matrix_op,               # clase expuesta
    "Ans": Det_op([[1, 2], [3, 4]]),
    #"CM": CM()
}

repl = SafeREPL(safe_env)#GaussBot(autoupdate=False, newline=newline)

USERS_FILE = "users.json"

# ======================
# ChatManager embebido
# ======================
class ChatManager:
    def __init__(self, bot, users_file="users.json"):
        self.users_file = users_file
        self.users = self.load_users()
        self.current_user = None
        self.state = "ASK_EMAIL"   # máquina de estados
        self.buffer = {}
        self.bot = bot
        self.name = "ChatManager"

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, "r") as f:
                return json.load(f)
        return {}

    def save_users(self):
        with open(self.users_file, "w") as f:
            json.dump(self.users, f)

    @property
    def salutation(self):
        return "👋 Bienvenido. Por favor escribe tu correo electrónico:"

    def ask(self, msg: str) -> str:
        if self.state == "ASK_EMAIL":
            email = msg.strip().lower()
            self.buffer["email"] = email
            if email in self.users:
                self.state = "ASK_PASSWORD"
                return "🔑 Usuario encontrado. Escribe tu contraseña:"
            else:
                self.state = "REGISTER_PASSWORD"
                return "🆕 Usuario nuevo. Elige una contraseña:"

        elif self.state == "ASK_PASSWORD":
            pwd = self.hash_password(msg.strip())
            email = self.buffer["email"]
            if self.users[email]["hash"] == pwd:
                self.current_user = email
                return self.auth_ok(f"✅ Bienvenido de nuevo, {email}")
            else:
                return "❌ Contraseña incorrecta. Intenta de nuevo:"

        elif self.state == "REGISTER_PASSWORD":
            pwd = self.hash_password(msg.strip())
            email = self.buffer["email"]
            self.users[email] = {"hash": pwd}
            self.save_users()
            self.current_user = email
            return self.auth_ok(f"🎉 Usuario {email} registrado con éxito.\n")

        elif self.state == "AUTH_OK":
            return self.bot.eval(msg.strip())

        else:
            return "⚠️ Estado desconocido."

    def auth_ok(self, txt):
        self.state = "AUTH_OK"
        return txt + self.bot.salutation


# ======================
# Websocket solo privado
# ======================
@app.websocket("/ws_chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    chatbots[ws] = ChatManager(repl)
    await ws.send_text(json.dumps({"scope": "privado", "text": chatbots[ws].salutation}))

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            text = data.get("text", "")
            bot = chatbots[ws]

            respuesta = bot.ask(text)
            if respuesta:
                await ws.send_text(json.dumps({"scope": "privado", "text": str(respuesta)}))

            # ✅ si login ok → registrar sesión
            if bot.current_user:
                user_sessions[ws] = bot.current_user

    except WebSocketDisconnect:
        connections.remove(ws)
        if ws in user_sessions:
            del user_sessions[ws]
        if ws in chatbots:
            del chatbots[ws]


# =======================
# Página HTML
# =======================
html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chat Privado</title>
  <style>
    body { font-family: sans-serif; margin: 10px; font-size: 16px; }

    #privado_log {
      height: 300px;
      border: 1px solid #ccc;
      padding: 8px;
      margin-bottom: 10px;
      background: #f9f9f9;
      overflow-y: auto;
      font-size: 16px;
      resize: both; 
    }

#input_area { display: flex; gap: 5px; margin-bottom: 10px; }

    #msg {
  flex: 1;
  padding: 10px;
  font-size: 16px;
  resize: both;      /* <- permite cambiar ancho y alto */
  min-height: 40px;
  max-height: 150px; /* opcional: limitar tamaño máximo */
}

    #send_privado {
      background-color: #2196F3;
      color: white;
      border-radius: 5px;
      padding: 10px;
      font-size: 16px;
      border: none;
      cursor: pointer;
    }

    .msg {
      display: inline-block;
      padding: 6px 10px;
      margin: 4px 0;
      border-radius: 8px;
      max-width: 90%;
    }
    .msg.privado { background: #cce5ff; }

.msg.yo {
  background: #d4edda;   /* verde claro */
  text-align: right;
  display: block;
}

.msg.bot {
  background: #cce5ff;   /* azul claro */
  text-align: left;
  display: block;
}

    @media (max-width: 600px) {
      body { font-size: 18px; }
      #privado_log { height: 250px; font-size: 16px; }
      input#msg, button { font-size: 18px; padding: 10px; }
    }
  </style>
</head>
<body>
  <h2 id="title">Login</h2>

  <!-- Formulario de login -->
  <div id="login_area">
    <input id="email" type="email" placeholder="Correo electrónico">
    <input id="password" type="password" placeholder="Contraseña">
    <button id="login_btn">Iniciar sesión</button>
  </div>

  <!-- Chat oculto al inicio -->
  <div id="chat_area" style="display:none;">
    <h2>Chat Privado</h2>
    <div id="privado_log"></div>

    <div id="input_area">
      <textarea id="msg" placeholder="Escribe tu mensaje..." enterkeyhint="send"></textarea>
      <button id="send_privado">Enviar</button>
    </div>
  </div>

  <script>
    const ws = new WebSocket(`ws://${location.host}/ws_chat`);

    const login_area = document.getElementById("login_area");
    const chat_area = document.getElementById("chat_area");
    const title = document.getElementById("title");

    const email = document.getElementById("email");
    const password = document.getElementById("password");
    const login_btn = document.getElementById("login_btn");

    const privado_log = document.getElementById("privado_log");
    const msg = document.getElementById("msg");
    const btn_privado = document.getElementById("send_privado");

    let logged_in = false;

    // ✅ al recibir mensajes
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const formatted = data.text.replace(/\\n/g, "<br>");

      if (!logged_in) {
        // cuando el servidor acepte login, activamos chat
        if (formatted.includes("Bienvenido de nuevo") || formatted.includes("registrado con éxito")) {
          login_area.style.display = "none";
          chat_area.style.display = "block";
          title.innerText = "Chat Privado";
          logged_in = true;
        }
      }

      if (logged_in) {
        privado_log.innerHTML += `<div class="msg bot">${formatted}</div>`;
      }
    };

    // ✅ login
    login_btn.onclick = () => {
      if (email.value.trim() !== "" && password.value.trim() !== "") {
        ws.send(JSON.stringify({scope: "privado", text: email.value}));
        setTimeout(() => {
          ws.send(JSON.stringify({scope: "privado", text: password.value}));
        }, 300); // pequeño delay
      }
    };

    // ✅ enviar mensaje ya logueado
btn_privado.onclick = () => {
  if (msg.value.trim() !== "") {
    const texto = msg.value;
    // agrego el mensaje
    const div = document.createElement("div");
    div.className = "msg yo";
    div.textContent = texto;
    privado_log.appendChild(div);

    // ✅ hacer scroll para que este mensaje quede arriba
    div.scrollIntoView({ block: "start", behavior: "smooth" });

    // mandar al servidor
    ws.send(JSON.stringify({scope: "privado", text: texto}));
    msg.value = "";
  }
};
    msg.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        btn_privado.click();
      }
    });
  </script>
</body>

</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

# Ejecutar con:
# uvicorn main:app --host 0.0.0.0 --port 8000

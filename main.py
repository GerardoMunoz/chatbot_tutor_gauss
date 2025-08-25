# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
from chat_manager import ChatManager
from bots.gauss_bot import GaussBot 

app = FastAPI()


newline='<br>'
connections = []
user_sessions = {}       # { ws: email }
chatbots = {}            # { ws: ChatManager }
tutor=GaussBot(autoupdate=False,newline=newline)
history_global=tutor.salutation

@app.websocket("/ws_chat")
async def websocket_chat(ws: WebSocket):
    global history_global
    await ws.accept()
    connections.append(ws)
    chatbots[ws] = ChatManager(tutor)
    await ws.send_text(json.dumps({"scope": "privado", "text": chatbots[ws].salutation}))

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            print('websocket data',data)
            scope = data.get("scope")
            text = data.get("text", "")

            if scope == "privado":
                bot = chatbots[ws]
                respuesta = bot.ask(text)
                if respuesta:
                    await ws.send_text(json.dumps({"scope": "privado", "text": respuesta}))

                # ✅ si login ok → registrar sesión
                if bot.current_user:
                    user_sessions[ws] = bot.current_user
                    for conn in connections:
                        await conn.send_text(json.dumps({"scope": "global", "text": history_global}))
                   
                    

            elif scope == "global":
                # ✅ verificar login
                if ws not in user_sessions:
                    await ws.send_text(json.dumps({
                        "scope": "privado",
                        "text": "⚠️ Debes iniciar sesión antes de participar en el chat global"
                    }))
                else:
                    email = user_sessions[ws]
                    mensaje = f"{email}: {text}"
                    history_global+=mensaje+newline
                    for conn in connections:
                        await conn.send_text(json.dumps({"scope": "global", "text": mensaje, "bot":False}))
                    respuesta = bot.ask(text)   
                    history_global+=respuesta+newline                    
                    for conn in connections:
                        await conn.send_text(json.dumps({"scope": "global", "text": respuesta, "bot":True}))
                         

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
  <title>Chat Estudiantil</title>
  <style>
    body { font-family: sans-serif; margin: 10px; font-size: 16px; }

    #global_log, #privado_log {
      height: 200px;
      border: 1px solid #ccc;
      padding: 8px;
      margin-bottom: 10px;
      background: #f9f9f9;
      overflow-y: auto;
      font-size: 16px;
    }

    #input_area { display: flex; gap: 5px; margin-bottom: 10px; }
    #msg { flex: 1; padding: 10px; font-size: 16px; }

    #button_area { display: flex; width: 100%; margin-top: 5px; }
    #button_area button {
      flex: 1;
      padding: 10px;
      font-size: 16px;
      border: none;
      cursor: pointer;
    }

    #send_privado {
      background-color: #2196F3;
      color: white;
      border-radius: 5px 0 0 5px;
    }

    #send_global {
      background-color: #4CAF50;
      color: white;
      border-radius: 0 5px 5px 0;
    }

    .msg {
      display: inline-block;
      padding: 6px 10px;
      margin: 4px 0;
      border-radius: 8px;
      max-width: 90%;
    }
    .msg.global { background: #e0e0e0; }
    .msg.privado { background: #cce5ff; }

    @media (max-width: 600px) {
      body { font-size: 18px; }
      #global_log, #privado_log { height: 250px; font-size: 16px; }
      input#msg, button { font-size: 18px; padding: 10px; }
    }
  </style>
</head>
<body>
  <h2>Chat Privado (Login y pruebas)</h2>
  <div id="privado_log"></div>

  <div id="input_area">
    <input id="msg" type="text" placeholder="Escribe tu mensaje..." enterkeyhint="send">
  </div>

  <div id="button_area">
    <button id="send_privado">Enviar Privado</button>
    <button id="send_global">Enviar Global</button>
  </div>

  <h2>Chat Global (Propuestas)</h2>
  <div id="global_log"></div>

  <script>
    const ws = new WebSocket(`ws://${location.host}/ws_chat`);

    const global_log = document.getElementById("global_log");
    const privado_log = document.getElementById("privado_log");
    const msg = document.getElementById("msg");
    const btn_global = document.getElementById("send_global");
    const btn_privado = document.getElementById("send_privado");

    // recibir mensajes
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const formatted = data.text.replace(/\\n/g, "<br>");
      if (data.scope === "global") {
        global_log.innerHTML += `<div class="msg global">${formatted}</div>`;
        global_log.scrollTop = global_log.scrollHeight;
      } else {
        privado_log.innerHTML += `<div class="msg privado">${formatted}</div>`;
        privado_log.scrollTop = privado_log.scrollHeight;
      }
    };

    // enviar global
    btn_global.onclick = () => {
      if (msg.value.trim() !== "") {
        ws.send(JSON.stringify({scope: "global", text: msg.value}));
        msg.value = "";
      }
    };

    // enviar privado
    btn_privado.onclick = () => {
      if (msg.value.trim() !== "") {
        ws.send(JSON.stringify({scope: "privado", text: msg.value}));
        msg.value = "";
      }
    };

    // atajo Enter = enviar privado (puedes cambiarlo a global si prefieres)
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

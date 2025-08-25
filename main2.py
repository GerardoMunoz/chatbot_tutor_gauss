from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from chat_manager import ChatManager 

app = FastAPI()

# =======================
# ChatBot de ejemplo
# =======================
class ChatBot:
    def __init__(self, nombre="Tutor"):
        self.nombre = nombre

    def ask(self, texto: str) -> str:
        if "hola" in texto.lower():
            return f"{self.nombre}: ¡Hola! 👋"
        elif "adios" in texto.lower():
            return f"{self.nombre}: Hasta luego."
        else:
            return f"{self.nombre}: No entendí '{texto}'"



connections = []   # todos los clientes conectados

@app.websocket("/ws_chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    connections.append(ws)

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            scope = data.get("scope")
            text = data.get("text", "")

            if scope == "privado":
                # responder solo al remitente
                respuesta = f"(Privado) Tú: {text}"
                await ws.send_text(json.dumps({"scope": "privado", "text": respuesta}))

            elif scope == "global":
                # difundir a todos
                for conn in connections:
                    await conn.send_text(json.dumps({"scope": "global", "text": text}))
    except WebSocketDisconnect:
        connections.remove(ws)

# # # =======================
# # # WebSocket grupal
# # # =======================

# connections_global = []
# chat_global_history = []   # lista de mensajes
# user_sessions = {}   # { ws_global: email }
# private_links = {}   # { email: ws_privado }


# @app.websocket("/ws_global")
# async def websocket_global(ws: WebSocket):
    # await ws.accept()
    # connections_global.append(ws)
    # # Enviar historial existente
  # #  for past in chat_global_history:
  # #      await ws.send_text(past)
    
    
    # try:
        # while True:
            # msg = await ws.receive_text()
            
            # email = user_sessions.get(ws)
            

            # if email:  # ✅ autorizado
                # chat_global_history.append(msg)
                # for conn in connections_global:
                    # await conn.send_text(f"{email}: {msg}")
            # else:  # ❌ no logueado
                # # Buscar su privado y enviarle alerta
                # for priv_ws in private_links.values():
                    # if priv_ws.client_state.name == "CONNECTED":
                        # await priv_ws.send_text("⚠️ Debes hacer login antes de participar en el chat global")




            
           # # chat_global_history.append(msg)
            # # reenviar a todos los conectados
           # # for conn in connections_global:
           # #     await conn.send_text(msg)
    # except WebSocketDisconnect:
        # connections_global.remove(ws)
        # if ws in user_sessions:
            # del user_sessions[ws]



# # # =======================
# # # WebSocket privado
# # # =======================

# from chat_manager import ChatManager

# @app.websocket("/ws_privado")
# async def ws_privado(websocket: WebSocket):
    # await websocket.accept()
    # bot = ChatManager()  # cada cliente tiene su propio login y GaussBot
    # await websocket.send_text(bot.salutation)  # mensaje inicial de login
    # try:
        # while True:
            # data = await websocket.receive_text()
            # respuesta = bot.ask(data)
            
            # # Si el login fue exitoso, registrar al usuario
            # if bot.current_user:
                # private_links[bot.current_user] = websocket
                 
            
            # if respuesta:
                # await websocket.send_text(respuesta)
    # except WebSocketDisconnect:
        # if bot.current_user in private_links:
            # del private_links[bot.current_user]


# =======================
# Página HTML con dos consolas
# =======================
html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chat Estudiantil</title>
  <style>
    body { font-family: sans-serif; margin: 10px; }
    textarea { width: 100%; resize: none; }
    #global_log, #privado_log {
      height: 150px;
      border: 1px solid #ccc;
      padding: 5px;
      margin-bottom: 10px;
      background: #f9f9f9;
      overflow-y: auto;
    }
    #input_area { display: flex; gap: 5px; margin-bottom: 10px; }
    #msg { flex: 1; }
    button { padding: 5px 10px; }
  </style>
  <style>
  #button_area {
    display: flex;
    width: 100%;
    margin-top: 5px;
  }

  #button_area button {
    flex: 1;             /* cada botón ocupa el mismo espacio */
    padding: 10px;
    font-size: 16px;
    border: none;
    cursor: pointer;
  }

  #send_global {
    background-color: #4CAF50; /* verde */
    color: white;
    border-radius: 5px 0 0 5px; /* esquinas izquierda */
  }

  #send_privado {
    background-color: #2196F3; /* azul */
    color: white;
    border-radius: 0 5px 5px 0; /* esquinas derecha */
  }
  
.msg {
  display: inline-block;       /* ajusta el ancho al contenido */
  background: #f1f1f1;         /* color de fondo */
  padding: 8px 12px;           /* espacio interno */
  margin: 5px 0;               /* separación entre mensajes */
  border-radius: 10px;         /* esquinas redondeadas */
  max-width: 80%;              /* ancho máximo */
}  
.msg.user {
  background: #2196F3;
  color: white;
  margin-left: auto;    /* empuja a la derecha */
  text-align: right;
}

.msg.bot {
  background: #e0e0e0;
  color: black;
  margin-right: auto;   /* empuja a la izquierda */
  text-align: left;
}


body {
  font-family: sans-serif;
  margin: 10px;
  font-size: 16px;       /* base para escritorio */
}

#global_log, #privado_log {
  height: 150px;
  border: 1px solid #ccc;
  padding: 8px;
  margin-bottom: 10px;
  background: #f9f9f9;
  overflow-y: auto;
  font-size: 14px;       /* un poco más grande que ahora */
}

input#msg {
  flex: 1;
  padding: 10px;
  font-size: 16px;
}

button {
  padding: 10px;
  font-size: 16px;
  border-radius: 6px;
}

/* 🔹 Ajustes especiales para pantallas pequeñas */
@media (max-width: 600px) {
  body {
    font-size: 18px;     /* texto más grande en celular */
  }
  #global_log, #privado_log {
    height: 200px;       /* más altos para ver más mensajes */
    font-size: 16px;     /* subir tamaño de letra */
  }
  input#msg {
    font-size: 18px;
    padding: 12px;
  }
  button {
    font-size: 18px;
    padding: 12px;
  }
}


</style>
  
</head>
<body>
  <h2>Chat Privado</h2>
  <div id="privado_log"></div>

<div id="input_area">
  <input id="msg" type="text" placeholder="Escribe tu mensaje..." enterkeyhint="send">
</div>

<div id="button_area">
  <button id="send_privado">Enviar Privado</button>
  <button id="send_global">Enviar Global</button>
</div>
  <h2>Chat Global</h2>
  <div id="global_log"></div>

  <!--script>
    // Conexiones WebSocket
    const ws_global = new WebSocket(`ws://${location.host}/ws_global`);
    const ws_privado = new WebSocket(`ws://${location.host}/ws_privado`);

    const global_log = document.getElementById("global_log");
    const privado_log = document.getElementById("privado_log");
    const msg = document.getElementById("msg");
    const btn_global = document.getElementById("send_global");
    const btn_privado = document.getElementById("send_privado");

    // Muestra mensajes globales
    ws_global.onmessage = (event) => {
      const formatted = event.data;//.replace(/\\n/g, "<br>");
      global_log.innerHTML += `<div>${formatted}</div>`;
      global_log.scrollTop = global_log.scrollHeight;
      // al actualizar global, limpiamos privado
      //privado_log.innerHTML = "";
    };

    // Muestra mensajes privados
    ws_privado.onmessage = (event) => {
      const formatted = event.data;//.replace("\\n", "<br>");
      privado_log.innerHTML += `<div>${formatted}</div>`;
      privado_log.scrollTop = privado_log.scrollHeight;
    };

    // Enviar mensaje global
    btn_global.onclick = () => {
      if (msg.value.trim() !== "") {
        ws_global.send(msg.value);
        msg.value = "";
      }
    };

    // Enviar mensaje privado
    btn_privado.onclick = () => {
      if (msg.value.trim() !== "") {
        ws_privado.send(msg.value);
        msg.value = "";
      }
    };

    // Atajo con Enter (solo global)
    msg.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        btn_privado.click();
      }
    });
  </script-->
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
  const formatted = data.text.replace(/\n/g, "<br>");
  if (data.scope === "global") {
    global_log.innerHTML += `<div class="msg global">${formatted}</div>`;
    global_log.scrollTop = global_log.scrollHeight;
  } else {
    privado_log.innerHTML += `<div class="msg privado">${formatted}</div>`;
    privado_log.scrollTop = privado_log.scrollHeight;
  }
};

// enviar
btn_global.onclick = () => {
  if (msg.value.trim() !== "") {
    ws.send(JSON.stringify({scope: "global", text: msg.value}));
    msg.value = "";
  }
};

btn_privado.onclick = () => {
  if (msg.value.trim() !== "") {
    ws.send(JSON.stringify({scope: "privado", text: msg.value}));
    msg.value = "";
  }
};
  
  
  
    // Atajo con Enter (solo global)
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


#ToDo
# Aumentar Letra Cliente Cel
# Notas, presentar y almacenar
# Chat publico y privado
#%Autoupdate comando del chatbor
#!comandos otros chatbots
# Permitir otras entradas de matrices

#Bugs
#No funciona 'Enter'

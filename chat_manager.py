# chat_manager.py
import hashlib
import json
import os



class ChatManager:
    def __init__(self, bot, users_file="users.json"):
        self.users_file = users_file
        self.users = self.load_users()
        self.current_user = None
        self.state = "ASK_EMAIL"   # máquina de estados
        self.buffer = {}
        self.tutor=bot

    # ======================
    # Utils
    # ======================
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

    # ======================
    # Conversación
    # ======================
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
            if self.users[email] == pwd:
                self.current_user = email
                #self.state = "AUTH_OK"
                return self.auth_ok(f"✅ Bienvenido de nuevo, {email}")#.\nAhora puedes elegir un bot."
            else:
                return "❌ Contraseña incorrecta. Intenta de nuevo:"

        elif self.state == "REGISTER_PASSWORD":
            pwd = self.hash_password(msg.strip())
            email = self.buffer["email"]
            self.users[email] = pwd
            self.save_users()
            self.current_user = email
            return self.auth_ok(f"🎉 Usuario {email} registrado con éxito.\n")

        elif self.state == "AUTH_OK":
            
    #print(tutor.salutation)
    #print(tutor.ask("[[1,2],[3,4]]"))

            #return f"🤖 Hola {self.current_user}, aquí aparecería el menú de bots.\n"+
            return self.tutor.ask(msg.strip())

        else:
            return "⚠️ Estado desconocido."
            #Pendiente: autoupdate, public and private , WA box, Cel size
            
    def auth_ok(self, txt):
            self.state = "AUTH_OK"
            #self.tutor=GaussBot("{","}",autoupdate=False,newline='<br>')
            #print(self.tutor)
            return txt+self.tutor.salutation
        
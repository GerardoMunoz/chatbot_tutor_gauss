from chat_manager import hash_password, save_users

class AuthBot:
    def __init__(self, manager):
        self.manager = manager
        self.stage = "correo"
        self.temp = {}
        self.prompt = "[AUTH] "
        self.salutation = "Hola, Ingresa tu correo"
        

    def ask(self, text: str):
        if self.stage == "correo":
            correo = text.strip()
            self.temp["correo"] = correo
            if correo in self.manager.users:
                self.stage = "password"
                return self.prompt + "Correo encontrado. Ingresa tu contraseña:"
            else:
                self.stage = "registro"
                return self.prompt + "Nuevo usuario. Ingresa una contraseña para registrarte:"

        elif self.stage == "registro":
            self.manager.users[self.temp["correo"]] = {
                "password_hash": hash_password(text),
                "bots_usados": []
            }
            save_users(self.manager.users)
            self.manager.user = self.temp["correo"]
            from bots.menu_bot import MenuBot
            return (self.prompt + "Registro exitoso. Bienvenido.", "SWITCH", MenuBot(self.manager))

        elif self.stage == "password":
            correo = self.temp["correo"]
            pwd_hash = hash_password(text)
            if pwd_hash == self.manager.users[correo]["password_hash"]:
                self.manager.user = correo
                from bots.menu_bot import MenuBot
                return (self.prompt + "Autenticado correctamente.", "SWITCH", MenuBot(self.manager))
            else:
                self.stage = "correo"
                return self.prompt + "Contraseña incorrecta. Ingresa tu correo de nuevo:"

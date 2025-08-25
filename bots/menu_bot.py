from bots.math_bot import MathBot
from bots.echo_bot import EchoBot

class MenuBot:
    def __init__(self, manager):
        self.manager = manager
        self.prompt = f"[MENU/{manager.user}] "

    def ask(self, text: str):
        if text == "1":
            return (self.prompt + "Entrando a MathBot", "SWITCH", MathBot(self.manager.user))
        elif text == "2":
            return (self.prompt + "Entrando a EchoBot", "SWITCH", EchoBot(self.manager.user))
        elif text.lower() == "logout":
            self.manager.user = None
            from bots.auth_bot import AuthBot
            return (self.prompt + "Has cerrado sesión.", "SWITCH", AuthBot(self.manager))
        else:
            return self.prompt + "Opciones:\n1) MathBot\n2) EchoBot\nEscribe 'logout' para salir."

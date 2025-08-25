class EchoBot:
    def __init__(self, username):
        self.prompt = f"[{username}/Echo] "

    def ask(self, text: str):
        if text.lower() == "salir":
            return (self.prompt + "Saliendo al menú...", "POP")
        return self.prompt + text

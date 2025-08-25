class YieldBot:
    def __init__(self, username):
        self.username = username
        self._gen = self._run()
        self.salutation = next(self._gen)  # 🚀 primer yield = salutation

    def _run(self):
        yield f"[{self.username}/Yield] Hola, soy un bot con yield. ¿Qué quieres decirme?"
        while True:
            text = (yield)
            if text == "salir":
                yield f"[{self.username}/Yield] Chao!"
                break
            yield f"[{self.username}/Yield] Repetiste: {text}"

    def ask(self, text: str):
        return self._gen.send(text)

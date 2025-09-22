# ============================
# Clase base para objetos seguros
# ============================
class SafeObject:
    __safe_methods__ = []

    def __getattribute__(self, name):
        # Bloquear atributos internos peligrosos
        if name.startswith("_") and name not in ("__str__", "__repr__","__safe_methods__"):
            raise AttributeError("Acceso no permitido")
        return object.__getattribute__(self, name)

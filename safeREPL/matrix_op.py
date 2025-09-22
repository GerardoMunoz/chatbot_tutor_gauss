from safeObject import SafeObject
# ============================
# Ejemplo de clase segura: Matrix
# ============================
class Matrix_op(SafeObject):
    __safe_methods__ = ["op", "det"]

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return "\n".join(str(r) for r in self.data)

    def op(self, command: str):
        """
        Operaciones de renglones/columnas:
        - "r1<->r2"  intercambia renglones
        - "c1<->c2"  intercambia columnas
        """
        if "<->" in command:
            left, right = command.split("<->")
            if left.strip().startswith("r") and right.strip().startswith("r"):
                r1, r2 = int(left[1:]) - 1, int(right[1:]) - 1
                self.data[r1], self.data[r2] = self.data[r2], self.data[r1]
            elif left.strip().startswith("c") and right.strip().startswith("c"):
                c1, c2 = int(left[1:]) - 1, int(right[1:]) - 1
                for row in self.data:
                    row[c1], row[c2] = row[c2], row[c1]
            else:
                return "⚠️ Comando inválido"
        return self

    def det(self):
        """Determinante solo para 2x2 (ejemplo)"""
        if len(self.data) == 2 and len(self.data[0]) == 2:
            a, b = self.data[0]
            c, d = self.data[1]
            return a * d - b * c
        return "⚠️ Solo implementado para 2x2"

















import ast
from safeObject import SafeObject
from matrix_op import Matrix_op
from det_op import Det_op



# ============================
# Ejemplo de clase segura: CM
# ============================
class CM(SafeObject):
    __safe_methods__ = ["help", "quit"]

    def help(self):
        return (
            "📖 Métodos disponibles en CM:\n"
            "- CM.help() → muestra esta ayuda\n"
            "- CM.quit() → termina la sesión\n"
        )

    def quit(self):
        return "👋 Sesión terminada."


# ============================
# REPL seguro
# ============================
class SafeREPL:
    def __init__(self, env=None):
        self.env = env or {}
        self.salutation="Hola"

    def eval(self, code: str):
        try:
            tree = ast.parse(code, mode="exec")
            result = None
            for stmt in tree.body:
                if isinstance(stmt, ast.Assign):
                    # Ej: x = Ans
                    target = stmt.targets[0]
                    if not isinstance(target, ast.Name):
                        raise ValueError("Asignación inválida")
                    var_name = target.id
                    value = self._eval_expr(stmt.value)
                    self.env[var_name] = value
                    result = f"✅ {var_name} asignado"
                elif isinstance(stmt, ast.Expr):
                    result = self._eval_expr(stmt.value)
                else:
                    raise ValueError("Instrucción no permitida")
            return result
        except Exception as e:
            return f"⚠️ Error: {e}"

    def _eval_expr(self, node):
        if isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            raise ValueError(f"Variable desconocida: {node.id}")

        elif isinstance(node, ast.Call):
            func = self._eval_expr(node.func)
            args = [self._eval_expr(arg) for arg in node.args]
            return func(*args)

        elif isinstance(node, ast.Attribute):
            value = self._eval_expr(node.value)
            attr = node.attr
            print(getattr(value, "__safe_methods__", [9]),dir(value))
            if attr not in getattr(value, "__safe_methods__", []):
                raise ValueError(f"Método {attr} no permitido en {value}")
            return getattr(value, attr)

        elif isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.List):
            return [self._eval_expr(elt) for elt in node.elts]

        else:
            raise ValueError(f"Expresión no permitida: {type(node)}")


# ============================
# Demo
# ============================
if __name__ == "__main__":
    #Ans = Matrix([[1, 2], [3, 4]])
    #cm = CM()
    safe_env = {
    "Det":Det_op,
    "Matrix": Matrix_op,               # clase expuesta
    "Ans": Det_op([[1, 2], [3, 4]]),
    #"CM": CM()
}

    repl = SafeREPL(safe_env)#{"Ans": Ans, "CM": cm})
    cont=True
    while cont:
        cmd=input ('>>> ').strip()
        if 'quit' == cmd[:4]:
            cont=False
            break
        print(str(repl.eval(cmd) ))

    # print(repl.eval("Ans"))             # muestra la matriz
    # print(repl.eval("Ans.op('r1<->r2')"))
    # print(repl.eval("Ans"))             # matriz cambiada
    # print(repl.eval("Ans.det()"))       # determinante
    # print(repl.eval("M = Ans"))         # asignación
    # print(repl.eval("M.det()"))         # uso de variable
    # print(repl.eval("CM.help()"))       # ayuda de CM
    # print(repl.eval("CM.quit()"))       # terminar sesión

from bots.matrix import Matrix, eye, vec
import ast, re



class GaussBot:
    # Mensajes centralizados
    msg_intro = (
        "#Reducción por Gauss-Jordan\n"
        "#1 Vaya a la columna no cero extrema izquierda.\n"
        "#2 Si el primer renglón tiene un cero en la columna del paso (1), intercámbielo con uno que tenga un elemento no cero en la misma columna.\n"
        "#3 Obtenga ceros abajo del elemento delantero, sumando múltiplos adecuados del renglón superior a los renglones debajo de él.\n"
        "#4 Cubra el renglón superior y repita el mismo proceso comenzando por el paso (1) aplicado a la sub-matriz restante. Repita este proceso con el resto de los renglones.\n"
        "#5 Comenzando con el último renglón no cero, avance hacia arriba: para cada renglón obtenga un 1 delantero e introduzca ceros arriba de él, sumando múltiplos adecuados a los renglones correspondientes."
    )

    msg_example_source = "Ejemplo tomado de la página 19 del libro 'Álgebra Lineal con aplicaciones' de Nakos-Joyner de la editorial Thomson impreso en 1999."

    msg_matrix_input = "Puede ingresar otra matriz, si no, solamente envie el símbolo \"=\"\n A="
    msg_matrix_loaded = "La matriz ingresada fue"
    msg_matrix_repr = "A=[[0, 3, -6, -4, -3, -5],[-1, 3, -10, -4, -4, -2],[4, -9, 34, 0, 1, -21],[2, -6, 20, 2, 8, -8]]"

    msg_op_prompt = "Escriba la operación entre renglones\n operación = "

    msg_matrix_changed = "la matriz cambió"
    msg_matrix_not_changed = "La matriz no cambió"
    msg_congratulations = "Felicitaciones!! la matriz ya está en forma escalón"
    msg_advanced_column = "Muy bien, avanzó otra columna"
    msg_lost_column = "Muy mal, perdió alguna columna"
    msg_pivot_nonzero =  staticmethod(lambda Bi, Bj: f"Super bien, ya no es cero el elemento delantero {Bi},{Bj}")
    msg_pivot_zero =  staticmethod(lambda Bi, Bj: f"Super mal, ahora es cero el elemento delantero {Bi},{Bj}")
    msg_pivot_max = "Además, al ser el mayor es más estable"
    msg_more_zeros = "Bien, obtuvo un cero más"
    msg_less_zeros = "Mal, perdió algún cero"
    msg_possible_zero = "Hubiera podido obtener un cero"
    msg_pivot_divisor = "Ya obtuvo un divisor en el elemento delantero"
    msg_no_understand_op = "No entiendo para que realizó esa operación"
    msg_exit = "hasta luego"
    msg_unknown_op =  staticmethod(lambda e: f"No entiendo: {e}\nAlgunos ejemplos de operaciones son: \n \t r1<->r2 \n \t -2r1+r2->r2 \n \t 3r2->r2")
    msg_help =  staticmethod("Algunos ejemplos de operaciones son: \n \t r1<->r2 \n \t -2r1+r2->r2 \n \t 3r2->r2\n Si %autoupdate=False la operación no actualiza la matriz y hay que actualizarla con %update")

    msg_sug_pivot_zero =  staticmethod(lambda Cj, Ci: f"Nuestro objetivo ahora es obtener un pivote en la columna {Cj}, pero observe que en el renglón {Ci} hay un cero")
    msg_sug_swap_rows =  staticmethod(lambda Ci, CiNoCero: f"Debe intercambiar el renglón {Ci} con el renglón {CiNoCero}")
    msg_sug_swap_rows_short =  staticmethod(lambda Ci, CiNoCero: f"R{Ci} <-> R{CiNoCero}")
    msg_sug_zeros_below = "Ahora hay que obtener ceros bajo el pivite"
    msg_sug_add_multiple =  staticmethod(lambda Ci, CiNoCero, coef: f"{coef}R{Ci} + R{CiNoCero} -> R{CiNoCero}")
    msg_sug_already_reduced = "La matriz ya está en forma escalón"

    def __init__(self,pretxt="",postxt="",autoupdate=True,first_rowcol=1,newline="\n"):
        #self.input = input_func
        #self.output = output_func
        self.autoupdate=autoupdate
        self.newline=newline
        self.pretxt=pretxt
        self.postxt=postxt
        self.sugerencia = 0
        self.repetir = True
        self.output_buf=""
        self._gen = self._run()
        self.salutation=next(self._gen)
        self.first_rowcol=first_rowcol
        self.name="GaussBot"

    def ask(self, text: str):
        return self._gen.send(text)

    #def matriz(self, A):
    #    return Matrix(A)
    
    def output(self,text):
        self.output_buf+=str(text)+'\n'
        
    def get_output(self,text):
        self.output(text)
        obuf=self.output_buf
        self.output_buf=""
        obuf=obuf.replace('\n',self.newline)
        #print('newline:'+self.newline+' obuf:'+obuf)
        return self.pretxt+obuf+self.postxt

    def row_op(self, A, i, j, k=0):
        r, c = A.shape
        E = eye(r)
        if k == 0:
            E[i, i] = 0
            E[j, j] = 0
            E[i, j] = 1
            E[j, i] = 1
        else:
            E[i, j] = k
        D = E @ A
        self.output(D)
        return D

    def str2num(self, s):
        if '.' in s:
            return float(s)
        elif '/' in s:
            return float(s)
        elif s.strip() == "-":
            return -1
        else:
            return int(s)

    def op(self, Amat, s):
        s = s.lower()

        def interpretaRenglon(s1):
            s = s1.replace(' ', '')
            d = s.find("r")
            if d == -1:
                raise ValueError(f"fala la 'r'. Error en {s}")
            elif d == 0:
                k = 1
            else:
                try:
                    k = self.str2num(s[:d])
                except ValueError as err:
                    raise ValueError(f"antes de 'r' sólo debe haber un entero. Error en {s}. {err}")
            try:
                a = int(s[d + 1:])
            except ValueError as err:
                raise ValueError(f"después de 'r' sélo debe haber un dígito. Error en {s}. {err}")
            return (k, a)

        (size, z) = Amat.shape
        m = eye(size)
        d = s.find("<->")
        if d != -1:
            (k1, a1) = interpretaRenglon(s[:d])
            (k2, a2) = interpretaRenglon(s[d + 3:])
            if (k1 != 1) or (k2 != 1):
                raise ValueError(f"al intercambiar renglones no se puede multiplicar. Error en {s}")
            r = f"R{a1} <-> R{a2}"
            m[a1, a1] = 0
            m[a2, a2] = 0
            m[a1, a2] = 1
            m[a2, a1] = 1
        else:
            d = s.find("->")
            if d == -1:
                raise ValueError(f"no se encontrO ni '->' ni '<->'. Error en {s}")
            else:
                (k2, a2) = interpretaRenglon(s[d + 2:])
                e = s[:d].find("+")
                f = s[:d].rfind("-")
                if e != -1:
                    (k11, a11) = interpretaRenglon(s[:e])
                    (k12, a12) = interpretaRenglon(s[e + 1:d])
                    if (a11 == a2) and (a12 == a2):
                        raise ValueError(f"en este caso es mejor multiplicar el renglón por {k11 + k12}. Error en {s}")
                    elif (a11 == a2):
                        r = f"{k12}R{a12}+{k11}R{a2} -> R{a2}"
                        m[a2, a12] = k12
                        m[a2, a11] = k11
                    elif (a12 == a2):
                        r = f"{k11}R{a11}+{k12}R{a2} -> R{a2}"
                        m[a2, a11] = k11
                        m[a2, a12] = k12
                    else:
                        raise ValueError(f"el renglón destino y un origen deben coincidir. Error en {s}")
                elif f != -1:
                    c = s[:d].count('r')
                    if c == 0:
                        raise ValueError(f"faltan 'R' en {s[:d]}")
                    elif c == 2:
                        (k11, a11) = interpretaRenglon(s[:f])
                        (k12, a12) = interpretaRenglon(s[f + 1:d])
                        if (a11 == a2) and (a12 == a2):
                            raise ValueError(f"en este caso es mejor multiplicar el renglón. Error en {s}")
                        elif (a11 == a2):
                            r = f"{-k12}R{a12}+{k11}R{a2} -> R{a2}"
                            m[a2, a12] = -k12
                            m[a2, a11] = k11
                        elif (a12 == a2):
                            r = f"{-k11}R{a11}+{k12}R{a2} -> R{a2}"
                            m[a2, a11] = -k11
                            m[a2, a12] = k12
                        else:
                            raise ValueError(f"el renglón destino y un origen deben coincidir. Error en {s}")
                    elif c == 1:
                        (k1, a1) = interpretaRenglon(s[:d])
                        if a1 != a2:
                            raise ValueError(f"el renglón destino y el origen deben coincidir. Error en {s}")
                        r = f"{k1}R{a1} -> R{a2}"
                        m[a2, a2] = k1
                    else:
                        raise ValueError(f"se operan máximo dos renglones. Error en {s}")
                else:
                    (k1, a1) = interpretaRenglon(s[:d])
                    if a1 != a2:
                        raise ValueError(f"el renglón destino y el origen deben coincidir. Error en {s}")
                    r = f"{k1}R{a1} -> R{a2}"
                    m[a2, a2] = k1
        self.output(r)
        return m @ Amat

    def califica_matriz(self, mat):
        i = 0
        j = 0
        (m, n) = mat.shape
        repetir = True
        while repetir:
            cont_ceros = 0
            cont_div = 0
            delant = mat[i, j]
            ceros_abajo = True
            mayor_abs=0
            for i1 in range(i + 1, m):
                a = mat[i1, j]
                if bool(a):
                    ceros_abajo = False
                    try:
                        amod = a % delant
                        if amod == 0:
                            cont_div += 1
                        mayor_abs=max(mayor_abs,abs(a))
                    except:
                        pass
                else:
                    cont_ceros += 1
            if j == n - 1 or i == m - 1 or not ceros_abajo:
                repetir = False
            elif ceros_abajo:
                j += 1
                if bool(delant):
                    i += 1
        return (delant, cont_ceros, cont_div, ceros_abajo, i, j, mayor_abs)

    def _dar_sugerencia(self, A):
        C = A.ultop
        self.output(str(C))
        (Cm, Cn) = C.shape
        (Cij, Cceros, Cdiv, Cabajo, Ci, Cj) = self.califica_matriz(C)
        if Ci == Cm - 1 or Cj == Cn - 1:
            self.output(self.msg_sug_already_reduced)
        else:
            if not bool(Cij):
                self.output(self.msg_sug_pivot_zero(Cj, Ci))
                d = Ci + 1
                while d < Cm and not bool(C[d, Cj]):
                    d += 1
                if d < Cm:
                    self.output(self.msg_sug_swap_rows(Ci, d))
            else:
                self.output(self.msg_sug_zeros_below)
                for d in range(Ci + 1, Cm):
                    if bool(C[d, Cj]):
                        co = -C[d, Cj] / C[Ci, Cj]
                        if bool(co):
                            self.output(self.msg_sug_add_multiple(d, Ci, co))


    # def parse_matrix(s):
        # # ---- Ejemplos ----
        # # ej1 = "[1 2 3; 4 5 6; 7 8 9]"         # Formato MATLAB
        # # ej2 = "[[1,2,3],[4,5,6],[7,8,9]]"     # Formato Python
        # # ej3 = "1 2 3;4,5,6; 7   8   9"        # Mixto con comas y espacios

        # # print(parse_matrix(ej1))
        # # print(parse_matrix(ej2))
        # # print(parse_matrix(ej3))
        
        # # Quitar espacios sobrantes al inicio y fin
        # s = s.strip()
        
        # # Quitar corchetes exteriores si los hay
        # s = re.sub(r'^\[|\]$', '', s.strip())

        # # Separar filas: puede ser '];[', '][' o ';'
        # filas = re.split(r'\];?\s*\[|\]\s*\[|;', s)

        # matriz = []
        # for fila in filas:
            # # Quitar corchetes internos sobrantes
            # fila = re.sub(r'^\[|\]$', '', fila.strip())
            # if not fila:
                # continue
            # # Separar elementos por espacio(s) o coma
            # elementos = re.split(r'[,\s]+', fila.strip())
            # # Convertir a float o int según corresponda
            # fila_num = [float(e) if '.' in e or 'e' in e.lower() else int(e) for e in elementos if e]
            # matriz.append(fila_num)

        # return matriz



    def _run(self):
        self.output(self.msg_intro)
        self.output('')
        self.output(self.msg_example_source)

        B = Matrix([[0, 3, -6, -4, -3, -5],
                         [-1, 3, -10, -4, -4, -2],
                         [4, -9, 34, 0, 1, -21],
                         [2, -6, 20, 2, 8, -8]])
        self.output(self.msg_matrix_loaded)
        self.output(self.msg_matrix_repr)
        
        entrada=yield self.get_output(self.msg_matrix_input)
        if entrada != "=":
            try:
                B = Matrix(ast.literal_eval(entrada))   # ✅ versión segura de eval
                #B = Matrix( parse_matrix(entrada))
            except Exception as e:
                self.output(f"Formato inválido de matriz: {e}")
    
        self.output(str(B))
        C=B
        #B = A
        Am, An = B.shape
        self.output('Comandos básicos del bot:  %update, %salir, %sugerir, %ayuda')

        while self.repetir:
            self.output('------------------------------------------')
            self.output(C)
            operacion=yield self.get_output(self.msg_op_prompt)
            operacion = operacion.strip().lower()            
            #operacion = self.input(self.msg_op_prompt)
            #print(operacion,type(operacion))
            try:
                # if operacion.startswith("%autoupdate="):
                    # val = operacion.split("=")[1].strip().lower()
                    # if val in ("true", "1", "yes", "on"):
                        # self.autoupdate = True
                    # elif val in ("false", "0", "no", "off"):
                        # self.autoupdate = False
                    # self.output(f"autoupdate = {self.autoupdate}")
                    # continue
                if operacion in ["%update", "%up"]:
                    C = B
                    continue
                if operacion == '%salir':
                    self.repetir = False
                    self.output(self.msg_exit)
                    continue
                if operacion=='%sugerir':
                    self._dar_sugerencia(C)
                    continue
                if operacion=='%ayuda':
                    self.output(self.msg_help)
                    continue
                    
                if self.autoupdate:
                    C = B
                    B = self.op(B, operacion)
                else:
                    self.output(C)
                    B = self.op(C, operacion)
                #B = A
                self.output(B)
                self.sugerencia = 0
                D = C - B
                if bool(D):
                    #self.output(f"{self.msg_matrix_changed} [+1]")
                    (Bij, Bceros, Bdiv, Babajo, Bi, Bj, Bmax) = self.califica_matriz(B)
                    (Cij, Cceros, Cdiv, Cabajo, Ci, Cj, Cmax) = self.califica_matriz(C)

                    if Bi == Am - 1 or Bj == An - 1:
                        self.repetir = False
                        self.output(f"{self.msg_congratulations} !!!SCORE[+5]")
                    elif Bj > Cj:
                        self.output(f"{self.msg_advanced_column} !!!SCORE[+2]")
                    elif Bj < Cj:
                        self.output(f"{self.msg_lost_column} !!!SCORE[-2]")
                    else:
                        if (not bool(Cij)) and bool(Bij):
                            self.output(f"{self.msg_pivot_nonzero(Bi, Bj)} !!!SCORE[+3]")
                            if (Bij >= Bmax):
                                self.output(f"{self.msg_pivot_max} !!!SCORE[+1]")
                        elif bool(Cij) and (not bool(Bij)):  
                            self.output(f"{self.msg_pivot_zero(Bi, Bj)} !!!SCORE[-3]")
                        else:
                            if Bceros > Cceros:
                                self.output(f"{self.msg_more_zeros} !!!SCORE[+1]")
                            elif Bceros < Cceros:
                                self.output(f"{self.msg_less_zeros} !!!SCORE[-1]")
                            else:
                                if Cdiv > 0:
                                    self.output(f"{self.msg_possible_zero} !!!SCORE[+0]")
                                elif Bdiv > 0:
                                    self.output(f"{self.msg_pivot_divisor} !!!SCORE[+1]")
                                else:
                                    self.output(f"{self.msg_no_understand_op} !!!SCORE[0]")
                else:
                    self.output(f"{self.msg_matrix_not_changed} !!!SCORE[0]")

            except ValueError as e:
                    self.output(self.msg_unknown_op(e))


# Ejemplo de ejecución
if __name__ == "__main__":
    tutor = GaussTutor("{","}")
    print(tutor.salutation)
    print(tutor.ask("[[1,2],[3,4]]"))
    print(tutor.ask("r0<->r1"))

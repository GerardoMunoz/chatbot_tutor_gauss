import array
from math import cos, sin, sqrt
from typing import List, Union, Iterable
from safeObject import SafeObject

class Matrix(SafeObject):
    __safe_methods__ = ["op", "det"]

    def __init__(self, m, n: int = None, data: Iterable[float] = None, tail_type: int = 0):
        """
        Construye una matriz de distintas formas:
          - lista de listas: Matrix([[1,2],[3,4]])
          - lista plana: Matrix([1,2,3]) → 1x3
          - lista plana + n: Matrix([1,2,3,4], 2) → 2x2
          - dimensiones: Matrix(2, 3) (ceros)
          - dimensiones + datos: Matrix(2, 2, [1,2,3,4])
        """
        self.tail_type = tail_type

        # Caso: lista de listas
        if isinstance(m, list) and all(isinstance(row, list) for row in m):
            self.rows = len(m)
            self.cols = len(m[0]) if self.rows else 0
            for row in m:
                if len(row) != self.cols:
                    raise ValueError("All rows must have the same number of columns")
            self.data = array.array('f', [elem for row in m for elem in row])

        # Caso: lista plana
        elif isinstance(m, list) and all(isinstance(x, (int, float)) for x in m):
            flat_data = m
            total = len(flat_data)
            if n is None:
                self.rows, self.cols = 1, total
            else:
                if total % n != 0:
                    raise ValueError(f"Cannot reshape data of length {total} into columns={n}")
                self.cols = n
                self.rows = total // n
            self.data = array.array('f', flat_data)

        # Caso: dimensiones + opcional data
        else:
            self.rows = m
            if data is None:
                if n is None:
                    raise ValueError("If data is None, n (columns) must be specified")
                self.cols = n
                self.data = array.array('f', [0.0] * (self.rows * self.cols))
            else:
                if n is None:
                    if len(data) % self.rows != 0:
                        raise ValueError("Cannot infer number of columns")
                    self.cols = len(data) // self.rows
                else:
                    self.cols = n
                    if len(data) != self.rows * self.cols:
                        raise ValueError("Incorrect data length")
                self.data = array.array('f', data)

    @property
    def shape(self) -> tuple[int, int]:
        return (self.rows, self.cols)

    @property
    def T(self) -> "Matrix":
        """Devuelve la transpuesta (propiedad, no método)."""
        transposed = array.array('f', [0.0] * (self.cols * self.rows))
        for i in range(self.rows):
            for j in range(self.cols):
                transposed[j * self.rows + i] = self.data[i * self.cols + j]
        return Matrix(self.cols, self.rows, transposed)

    def __len__(self) -> int:
        return self.rows

    def __iter__(self):
        """Itera por filas como listas."""
        for i in range(self.rows):
            yield [self.data[i * self.cols + j] for j in range(self.cols)]

    def __eq__(self, other) -> bool:
        if not isinstance(other, Matrix):
            return False
        return self.shape == other.shape and all(a == b for a, b in zip(self.data, other.data))

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def verify_tail(self) -> bool:
        m, n = self.rows, self.cols
        t = self.tail_type

        if t in (0, 1):
            return True
        if t == 2:  # Horizontal, ceros
            return all(self[i, n - 1] == 0 for i in range(m))
        if t == 3:  # Vertical, ceros
            return all(self[m - 1, j] == 0 for j in range(n))
        if t == 4:  # Horizontal, un 1 por fila
            return all(self[i, n - 1] == 1 and
                       all(self[i, j] != 1 for j in range(n - 1))
                       for i in range(m))
        if t == 5:  # Vertical, un 1 por columna
            return all(self[m - 1, j] == 1 and
                       all(self[i, j] != 1 for i in range(m - 1))
                       for j in range(n))
        if t == 6:  # Horizontal, todos 1
            return all(self[i, n - 1] == 1 for i in range(m))
        if t == 7:  # Vertical, todos 1
            return all(self[m - 1, j] == 1 for j in range(n))
        return False

    def __getitem__(self, index):
        # Igual que en tu versión original
        if isinstance(index, int):
            if 0 <= index < self.cols * self.rows:
                return self.data[index]
            raise IndexError("Matrix index out of range")

        if not isinstance(index, tuple) or len(index) != 2:
            raise ValueError("Index must be a tuple of two elements")

        i, j = index

        if isinstance(i, int) and isinstance(j, int):
            if j < 0:
                j += self.cols
            if i < 0:
                i += self.rows
            if 0 <= i < self.rows and 0 <= j < self.cols:
                return self.data[i * self.cols + j]
            raise IndexError("Matrix indices out of range")

        if isinstance(i, int) and isinstance(j, slice):
            start, stop, step = j.indices(self.cols)
            return Matrix([self.data[i * self.cols + jj] for jj in range(start, stop, step)])

        if isinstance(i, slice) and isinstance(j, int):
            start, stop, step = i.indices(self.rows)
            return Matrix([self.data[ii * self.cols + j] for ii in range(start, stop, step)])

        if isinstance(i, slice) and isinstance(j, slice):
            si, ei, _ = i.indices(self.rows)
            sj, ej, _ = j.indices(self.cols)
            sub = [self.data[r * self.cols + c]
                   for r in range(si, ei) for c in range(sj, ej)]
            return Matrix(ei - si, ej - sj, sub)

        raise IndexError("Unsupported index format")

    def __setitem__(self, index, value):
        if isinstance(index, int):
            if 0 <= index < self.cols * self.rows:
                self.data[index] = value
            else:
                raise IndexError("Matrix index out of range")
            return

        if not isinstance(index, tuple) or len(index) != 2:
            raise ValueError("Index must be a tuple of two elements")

        i, j = index

        if isinstance(i, int) and isinstance(j, int):
            if j < 0:
                j += self.cols
            if i < 0:
                i += self.rows
            if 0 <= i < self.rows and 0 <= j < self.cols:
                self.data[i * self.cols + j] = value
            else:
                raise IndexError("Matrix indices out of range")
            return

        # Row slice: M[i, :]
        if isinstance(i, int) and isinstance(j, slice):
            start_j, stop_j, step_j = j.indices(self.cols)
            expected_len = len(range(start_j, stop_j, step_j))
            if len(value) != expected_len:
                raise ValueError(f"Expected {expected_len} elements, got {len(value)}")
            for k, jj in enumerate(range(start_j, stop_j, step_j)):
                self.data[i * self.cols + jj] = value[k]
            return

        # Column slice: M[:, j]
        if isinstance(i, slice) and isinstance(j, int):
            start_i, stop_i, step_i = i.indices(self.rows)
            expected_len = len(range(start_i, stop_i, step_i))
            if len(value) != expected_len:
                raise ValueError(f"Expected {expected_len} elements, got {len(value)}")
            for k, ii in enumerate(range(start_i, stop_i, step_i)):
                self.data[ii * self.cols + j] = value[k]
            return

        # Submatrix slice: M[i1:i2, j1:j2]
        if isinstance(i, slice) and isinstance(j, slice):
            start_i, stop_i, step_i = i.indices(self.rows)
            start_j, stop_j, step_j = j.indices(self.cols)

            if step_i != 1 or step_j != 1:
                raise IndexError("Step must be one")

            expected_rows = stop_i - start_i
            expected_cols = stop_j - start_j

            if len(value) != expected_rows or any(len(row) != expected_cols for row in value):
                raise ValueError(f"Expected matrix of size {expected_rows}x{expected_cols}")

            for r_offset, row in enumerate(range(start_i, stop_i)):
                for c_offset, col in enumerate(range(start_j, stop_j)):
                    self.data[row * self.cols + col] = value[r_offset][c_offset]
            return

        raise IndexError("Unsupported index format")

    def __mul__(self, other: Union[int, float, "Matrix"]) -> "Matrix":
        """Multiplicación elemento a elemento o por escalar."""
        if isinstance(other, (int, float)):
            return Matrix(self.rows, self.cols, [v * other for v in self.data])
        if isinstance(other, Matrix):
            if self.shape != other.shape:
                raise ValueError("Shapes must match for elementwise multiplication")
            return Matrix(self.rows, self.cols, [a * b for a, b in zip(self.data, other.data)])
        raise TypeError("Unsupported operand type for *")

    def __matmul__(self, other: "Matrix") -> "Matrix":
        """Multiplicación matricial pura (sin ajuste de tail)."""
        if not isinstance(other, Matrix):
            raise TypeError("Matrix multiplication is only defined between Matrix objects")
        if self.cols != other.rows:
            raise ValueError("Inner dimensions must match for matrix multiplication")
        result = [0.0] * (self.rows * other.cols)
        for i in range(self.rows):
            for k in range(self.cols):
                aik = self.data[i * self.cols + k]
                for j in range(other.cols):
                    result[i * other.cols + j] += aik * other.data[k * other.cols + j]
        return Matrix(self.rows, other.cols, result)

    # def matmul_tail(self, other: "Matrix") -> "Matrix":
    #     """Multiplicación matricial con ajuste automático de tail."""
    #     if self.cols == other.rows:
    #         return self @ other
    #     elif self.cols == other.rows - 1:
    #         return (self.tail() @ other).untail()
    #     elif self.cols - 1 == other.rows:
    #         return (self.untail() @ other).tail()
    #     else:
    #         raise ValueError("Tail adjustment not possible with given shapes")

    # El resto de métodos (inv, tail, untail, eye, etc.) quedarían igual que en tu versión

    def copy(self):
        return Matrix(self.rows,self.cols,self.data[:])

    def __add__(self, other):
        #print('add',self.rows,self.cols,other.rows,other.cols)
        if isinstance(other, Matrix) and self.cols == other.cols and self.rows == other.rows:
            result = Matrix(self.rows, self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] + other[i, j]
            return result
        else:
            raise ValueError("Matrices of different dimensions cannot be added",self.rows,self.cols,other.rows,other.cols)

    def __sub__(self, other):
        #print('sub',self.rows,self.cols,other.rows,other.cols)
        if isinstance(other, Matrix) and self.cols == other.cols and self.rows == other.rows:
            result = Matrix(self.rows, self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] - other[i, j]
            return result
        else:
            raise ValueError("Matrices of different dimensions cannot be subtracted",self.rows,self.cols,other.rows,other.cols)

    def __rmul__(self, other):
      return self * other

    def __rmatmul__(self, other):
      return self @ other

    def inv(self):
        if self.rows != self.cols:
            raise ValueError("Only square matrices can be inverted")

        n = self.rows
        A = self.copy()
        I = Matrix(n, n, [1 if i == j else 0 for i in range(n) for j in range(n)])

        for i in range(n):
            # Find the pivot row
            pivot = i
            while pivot < n and A[pivot, i] == 0:
                pivot += 1
            if pivot == n:
                raise ValueError("Matrix is singular and cannot be inverted")

            # Swap the pivot row with the current row
            if pivot != i:
                for j in range(n):
                    A[i, j], A[pivot, j] = A[pivot, j], A[i, j]
                    I[i, j], I[pivot, j] = I[pivot, j], I[i, j]

            # Normalize the pivot row
            pivot_value = A[i, i]
            for j in range(n):
                A[i, j] /= pivot_value
                I[i, j] /= pivot_value

            # Eliminate the other rows
            for k in range(n):
                if k != i:
                    factor = A[k, i]
                    for j in range(n):
                        A[k, j] -= factor * A[i, j]
                        I[k, j] -= factor * I[i, j]

        return I

    def __or__(self, other):
        """
        concatenate vertically
        """
        if isinstance(other, Matrix) and self.cols == other.cols:
            return Matrix(self.rows + other.rows, self.cols, self.data + other.data)
        else:
            raise ValueError("Matrices of different dimensions cannot be added", self.rows, self.cols, other.rows,
                             other.cols)

    def vstack(self,other):
        return self | other

    def row_join(self,other):
        return self | other

    def __and__(self, other):
        """
        Concatenate two matrices horizontally.

        Args:
            other (Matrix): The second matrix to concatenate.

        Returns:
            Matrix: The resulting matrix after horizontal concatenation.
        """
        if self.rows != other.rows:
            raise ValueError("Matrices must have the same number of rows to concatenate horizontally")

        concatenated_data = []
        for i in range(self.rows):
            concatenated_data.extend(self.data[i * self.cols: (i + 1) * self.cols])
            concatenated_data.extend(other.data[i * other.cols: (i + 1) * other.cols])

        return Matrix(self.rows, self.cols + other.cols, concatenated_data)

    def hstack(self,other):
        return self & other

    def col_join(self,other):
        return self & other

    def norm2(self):
        return sum(a**2 for a in  self.data)

    def norm(self):
        return sqrt(sum(a**2 for a in  self.data))

    def untail(m):  # static
        return Matrix(m.m, m.n - 1, [m.data[i] for i in range(len(m.data)) if i % m.n != m.n - 1])

    def tail(m):
        return Matrix(m.m, m.n + 1,
                      [(m.data[i * m.n + j] if j != m.n else 1) for i in range(m.m) for j in range(m.n + 1)])

    def tolist(self):
        return list(self.data)

    def __str__(self):
        output = ""
        for i in range(self.rows):
            row_str = " ".join(str(self[i, j]) for j in range(self.cols))
            output += row_str + "\n"
        return output

    def save(self, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(f"{self.rows} {self.cols}\n")
            for i in range(self.rows):
                for j in range(self.cols):
                    file.write(str(self.data[i * self.cols + j]) + ' ')
                file.write('\n')

    @classmethod
    def loadtxt(cls, filename):
        # import os
        # print(os.listdir())
        with open(filename, 'r', encoding='utf-8') as file:
            rows, cols = map(int, file.readline().split())
            data = []
            for _ in range(rows):
                row = list(map(float, file.readline().split()))
                data.extend(row)
            return cls(rows, cols, data)


    def rref(
            self,
            pivot_mode: str = "partial",  # "none", "partial", "total"
            form: str = "row_echelon",  # "row_echelon", "diagonal", "reduced"
            augment_identity: bool = False
    ) -> "Matrix":
        """
        Reduce la matriz según los parámetros dados.

        pivot_mode:
            "none"    → sin pivoteo
            "partial" → pivoteo parcial (por columna)

        form:
            "row_echelon" → forma escalón (ceros debajo de pivotes)
            "diagonal"    → escalonada con 1s en diagonal
            "reduced"     → forma escalón reducida (ceros arriba y abajo de pivotes)

        augment_identity:
            True → añade la identidad al lado derecho para cálculo de inversa
        """
        print('rref_in',  pivot_mode,form,  augment_identity,self)
        m, n = self.rows, self.cols
        if augment_identity:
            I = eye(m)
            work = self & I# Matrix(m, n + m, list(self.data) + list(I.data))
        else:
            work = self.copy()

        swaps = 0
        col_offset = 0
        col_max = work.cols if not augment_identity else n

        for k in range(min(m, col_max)):
            pivot_row = k

            # --- Pivoteo ---
            if pivot_mode=="partial":# in ("partial", "total"):
                #if pivot_mode == "partial":
                pivot_row = max(range(k, m), key=lambda i: abs(work[i, k]))
                # elif pivot_mode == "total":
                #     pivot_row, pivot_col = max(
                #         ((i, j) for i in range(k, m) for j in range(k, col_max)),
                #         key=lambda x: abs(work[x[0], x[1]])
                #     )
                #     if pivot_col != k:
                #         # Intercambiar columnas
                #         for r in range(m):
                #             work[r, k], work[r, pivot_col] = work[r, pivot_col], work[r, k]
                #         col_offset += 1

                if abs(work[pivot_row, k]) < 1e-12:
                    continue

                if pivot_row != k:
                    # Intercambiar filas
                    for c in range(work.cols):
                        work[k, c], work[pivot_row, c] = work[pivot_row, c], work[k, c]
                    swaps += 1

            elif pivot_mode == "none":
                if abs(work[k, k]) < 1e-12:
                    continue

            else:
                raise ValueError("pivot_mode not supported: ",pivot_mode)

            # --- Escalonar ---
            pivot = work[k, k]
            if form in ("diagonal", "reduced"):
                # Normalizar la fila para poner un 1 en el pivote
                for j in range(k, work.cols):
                    work[k, j] /= pivot

            # Eliminar hacia abajo
            for i in range(k + 1, m):
                factor = work[i, k] / work[k, k]
                for j in range(k, work.cols):
                    work[i, j] -= factor * work[k, j]

        # --- Escalonar hacia arriba si es reducido ---
        if form == "reduced":
            for k in range(min(m, col_max) - 1, -1, -1):
                pivot_col = next((c for c in range(col_max) if abs(work[k, c]) > 1e-12), None)
                if pivot_col is None:
                    continue
                for i in range(k):
                    factor = work[i, pivot_col]
                    for j in range(pivot_col, work.cols):
                        work[i, j] -= factor * work[k, j]
        print('rref_out',work)
        return work


def vec(*data, **kwargs):
    return Matrix(1, len(data), data, **kwargs)

    # @staticmethod


def eye(n):
    return Matrix(n, n, [1 if i == j else 0 for i in range(n) for j in range(n)])


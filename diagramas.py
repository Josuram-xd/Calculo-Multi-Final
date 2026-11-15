"""Dibuja los diagramas de flujo del pseudocodigo en diagramas/.

Uso:  python diagramas.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

DIR = Path(__file__).parent / "diagramas"
W, H = 5.2, 0.9  # ancho y alto de cada caja


class Diagrama:
    def __init__(self, titulo, alto, ancho=11):
        self.fig, self.ax = plt.subplots(figsize=(ancho * 0.8, alto * 0.8))
        self.ax.set_xlim(-ancho / 2, ancho / 2)
        self.ax.set_ylim(-alto + 0.3, 1)
        self.ax.axis("off")
        self.ax.set_title(titulo, fontsize=12, weight="bold")

    def nodo(self, tipo, x, y, texto, w=W, h=H):
        """tipo: 'fin' (inicio/fin), 'proc' (proceso), 'io' (entrada/salida), 'dec' (decision)."""
        ax = self.ax
        if tipo == "fin":
            p = FancyBboxPatch((x - w / 4, y - h / 2), w / 2, h, boxstyle="round,pad=0,rounding_size=0.45",
                               fc="#d9ead3", ec="k")
        elif tipo == "proc":
            p = Polygon([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)],
                        fc="#cfe2f3", ec="k")
        elif tipo == "io":
            s = 0.3
            p = Polygon([(x - w / 2 + s, y + h / 2), (x + w / 2 + s, y + h / 2), (x + w / 2 - s, y - h / 2),
                         (x - w / 2 - s, y - h / 2)], fc="#fff2cc", ec="k")
        else:  # decision
            p = Polygon([(x, y + h * 0.8), (x + w / 2, y), (x, y - h * 0.8), (x - w / 2, y)], fc="#f4cccc", ec="k")
        ax.add_patch(p)
        ax.text(x, y, texto, ha="center", va="center", fontsize=8.5)

    def flecha(self, puntos, etiqueta=None):
        """Linea quebrada por la lista de puntos, con punta de flecha al final."""
        xs, ys = zip(*puntos)
        self.ax.plot(xs[:-1], ys[:-1], "k", lw=1)
        self.ax.annotate("", xy=puntos[-1], xytext=puntos[-2], arrowprops=dict(arrowstyle="->", lw=1))
        if etiqueta:
            (x0, y0), (x1, y1) = puntos[0], puntos[1]
            self.ax.text(x0 + (0.25 if x1 == x0 else (0.3 if x1 > x0 else -0.3)), y0 + (-0.25 if x1 == x0 else 0.18),
                         etiqueta, fontsize=8.5, weight="bold", ha="center")

    def columna(self, nodos, x=0, y0=0, paso=1.5):
        """Coloca nodos en vertical unidos por flechas. Devuelve la y de cada uno."""
        ys = []
        for i, (tipo, texto) in enumerate(nodos):
            y = y0 - i * paso
            self.nodo(tipo, x, y, texto)
            if i:
                arriba = H * 0.8 if tipo == "dec" else H / 2
                abajo = H * 0.8 if nodos[i - 1][0] == "dec" else H / 2
                self.flecha([(x, ys[-1] - abajo), (x, y + arriba)], "No" if nodos[i - 1][0] == "dec" else None)
            ys.append(y)
        return ys

    def guardar(self, nombre):
        DIR.mkdir(exist_ok=True)
        self.fig.savefig(DIR / nombre, dpi=150, bbox_inches="tight")
        plt.close(self.fig)


def general():
    d = Diagrama("Diagrama 1. Algoritmo general del ajuste por mínimos cuadrados", alto=20, ancho=14)
    ys = d.columna([
        ("fin", "Inicio"),
        ("io", "Leer los datos (xᵢ, yᵢ), i = 1..n"),
        ("proc", "Calcular n, Σx, Σy, Σx², Σxy\n(ver Diagrama 2)"),
        ("proc", "D ← n·Σx² − (Σx)²"),
        ("dec", "¿D = 0?"),
        ("proc", "a* ← (n·Σxy − Σx·Σy) / D\nb* ← (Σy − a*·Σx) / n"),
        ("proc", "Calcular S(a*, b*), RMSE y R²\n(ver Diagrama 3)"),
        ("proc", "H ← [[2Σx², 2Σx], [2Σx, 2n]]\ndet H ← 4·D"),
        ("dec", "¿2Σx² > 0\ny det H > 0?"),
        ("io", "Escribir: «el punto crítico\nNO es un mínimo»"),
        ("proc", "Comparar a*, b*, S con la biblioteca\n(numpy.polyfit)"),
        ("io", "Escribir resultados y dibujar gráficas"),
        ("fin", "Fin"),
    ])
    # ¿D = 0?  Si -> error -> Fin
    d.nodo("io", 4.3, ys[4], "Escribir: «todos los xᵢ\nson iguales: sin\nsolución única»", w=3.2, h=1.2)
    d.flecha([(W / 2, ys[4]), (2.7, ys[4])], "Sí")
    d.flecha([(4.3, ys[4] - 0.6), (4.3, ys[12]), (W / 4, ys[12])])
    # ¿minimo?  Si -> es minimo -> comparar
    d.nodo("io", -4.3, ys[9], "Escribir: «el punto\ncrítico es un\nMÍNIMO»", w=3.0, h=1.2)
    d.flecha([(-W / 2, ys[8]), (-4.3, ys[8]), (-4.3, ys[9] + 0.6)], "Sí")
    d.flecha([(-4.3, ys[9] - 0.6), (-4.3, ys[10]), (-W / 2, ys[10])])
    d.guardar("diagrama_1_general.png")


def sumas():
    d = Diagrama("Diagrama 2. Cálculo de las sumas", alto=10.5)
    ys = d.columna([
        ("fin", "Inicio"),
        ("proc", "n ← 0,  Σx ← 0,  Σy ← 0\nΣx² ← 0,  Σxy ← 0,  Σy² ← 0"),
        ("dec", "¿Quedan datos\n(xᵢ, yᵢ) por leer?"),
        ("io", "Devolver n, Σx, Σy, Σx², Σxy, Σy²"),
        ("fin", "Fin"),
    ], x=-2, paso=2.2)
    d.nodo("proc", 3.3, ys[2], "n ← n + 1\nΣx ← Σx + xᵢ\nΣy ← Σy + yᵢ\nΣx² ← Σx² + xᵢ·xᵢ\nΣxy ← Σxy + xᵢ·yᵢ\nΣy² ← Σy² + yᵢ·yᵢ", w=3.6, h=2.4)
    d.flecha([(-2 + W / 2, ys[2]), (1.5, ys[2])], "Sí")
    # regreso del bucle a la decision
    d.flecha([(3.3, ys[2] + 1.2), (3.3, ys[2] + 1.45), (-2, ys[2] + 1.45)])
    d.guardar("diagrama_2_sumas.png")


def error():
    d = Diagrama("Diagrama 3. Cálculo de S(a, b), RMSE y R²", alto=15)
    ys = d.columna([
        ("fin", "Inicio"),
        ("io", "Recibir a, b y los datos (xᵢ, yᵢ)"),
        ("proc", "S ← 0,  ST ← 0,  ȳ ← Σy / n"),
        ("dec", "¿Quedan datos\n(xᵢ, yᵢ) por leer?"),
        ("proc", "RMSE ← √(S / n)\nR² ← 1 − S / ST"),
        ("io", "Devolver S, RMSE, R²"),
        ("fin", "Fin"),
    ], x=-2, paso=2.2)
    d.nodo("proc", 3.3, ys[3], "eᵢ ← yᵢ − (a·xᵢ + b)\nS ← S + eᵢ²\nST ← ST + (yᵢ − ȳ)²", w=3.6, h=1.6)
    d.flecha([(-2 + W / 2, ys[3]), (1.5, ys[3])], "Sí")
    d.flecha([(3.3, ys[3] + 0.8), (3.3, ys[3] + 1.3), (-2, ys[3] + 1.3)])
    d.guardar("diagrama_3_error.png")


if __name__ == "__main__":
    general()
    sumas()
    error()
    print(f"Diagramas guardados en {DIR}")

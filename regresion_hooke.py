"""Regresion lineal por minimos cuadrados para el experimento del resorte (Ley de Hooke).

Implementa las formulas deducidas a mano (grad S = 0), calcula el Hessiano,
compara con numpy.polyfit y genera todas las graficas del informe en figuras/.

Uso:  python regresion_hooke.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------- 1. Datos (x = masa colgada en g, y = estiramiento en cm) ----------
OBJETOS = ["Resorte sin carga", "Llave grande", "Tornillo grande", "Taza plástica",
           "Rollo de cinta", "Herradura", "Teléfono LG", "Reproductor / parlante",
           "Libro pequeño", "Alicate"]
X = [0, 15, 70, 92, 150, 185, 190, 220, 300, 410]
Y = [0.0, 0.1, 0.4, 1.6, 1.9, 2.5, 2.9, 4.2, 4.8, 5.6]

FIG = Path(__file__).parent / "figuras"


# ---------- 2. Metodo propio: formulas obtenidas de grad S = 0 ----------
def sumas(x, y):
    """Recorre los datos una vez y acumula n, Sx, Sy, Sxx, Sxy, Syy."""
    n = sx = sy = sxx = sxy = syy = 0
    for xi, yi in zip(x, y):
        n += 1
        sx += xi
        sy += yi
        sxx += xi * xi
        sxy += xi * yi
        syy += yi * yi
    return n, sx, sy, sxx, sxy, syy


def ajustar(x, y):
    """Devuelve (a*, b*) resolviendo las ecuaciones normales por Cramer."""
    n, sx, sy, sxx, sxy, _ = sumas(x, y)
    det = n * sxx - sx * sx
    if det == 0:
        raise ValueError("Todos los x son iguales: el sistema no tiene solucion unica")
    a = (n * sxy - sx * sy) / det
    b = (sy - a * sx) / n
    return a, b


def error_S(a, b, x, y):
    """S(a,b) = suma de (y_i - a x_i - b)^2."""
    return sum((yi - a * xi - b) ** 2 for xi, yi in zip(x, y))


def hessiano(x):
    """H = [[2 Sxx, 2 Sx], [2 Sx, 2 n]] (constante: no depende de a ni de b)."""
    n = len(x)
    sx = sum(x)
    sxx = sum(xi * xi for xi in x)
    return [[2 * sxx, 2 * sx], [2 * sx, 2 * n]]


def residuos(a, b, x, y):
    return [yi - (a * xi + b) for xi, yi in zip(x, y)]


def calidad(a, b, x, y):
    """Devuelve (RMSE, R^2)."""
    n = len(x)
    s = error_S(a, b, x, y)
    ym = sum(y) / n
    st = sum((yi - ym) ** 2 for yi in y)
    return (s / n) ** 0.5, 1 - s / st


# ---------- 3. Graficas ----------
def graficas(a, b):
    FIG.mkdir(exist_ok=True)
    x, y = np.array(X, float), np.array(Y)
    xs = np.linspace(-10, 430, 50)
    s_min = error_S(a, b, X, Y)

    def guardar(nombre):
        plt.tight_layout()
        plt.savefig(FIG / nombre, dpi=150)
        plt.close()

    def puntos(ax, etiquetas=True):
        ax.scatter(x, y, color="tab:blue", zorder=3, label="Datos medidos")
        if etiquetas:
            for nom, xi, yi in zip(OBJETOS, x, y):
                ax.annotate(nom, (xi, yi), textcoords="offset points", xytext=(6, -11), fontsize=7)
        ax.set_xlabel("Masa colgada x (g)")
        ax.set_ylabel("Estiramiento y (cm)")
        ax.grid(alpha=0.3)

    # 1. Dispersion
    fig, ax = plt.subplots(figsize=(8, 5))
    puntos(ax)
    ax.set_title("Diagrama de dispersión: estiramiento vs. masa colgada")
    guardar("01_dispersion.png")

    # 2. Recta optima y otras rectas
    fig, ax = plt.subplots(figsize=(8, 5))
    puntos(ax, etiquetas=False)
    ax.plot(xs, a * xs + b, "r", lw=2.5, label=f"Óptima: a={a:.4f}, b={b:.3f}, S={s_min:.2f}")
    for (a2, b2), est in zip(OTRAS_RECTAS, ["--", "-.", ":"]):
        ax.plot(xs, a2 * xs + b2, est, label=f"a={a2}, b={b2}, S={error_S(a2, b2, X, Y):.2f}")
    ax.set_title("Recta de mínimos cuadrados comparada con otras rectas")
    ax.legend(fontsize=8)
    guardar("02_recta_ajuste.png")

    # Malla de S(a,b)
    A, B = np.meshgrid(np.linspace(0.005, 0.025, 200), np.linspace(-2, 2, 200))
    S = sum((yi - A * xi - B) ** 2 for xi, yi in zip(X, Y))

    # 3. Superficie
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(A, B, S, cmap="viridis", alpha=0.85)
    ax.scatter([a], [b], [s_min], color="red", s=60, label=f"Mínimo ({a:.4f}, {b:.3f}, {s_min:.2f})")
    ax.set_xlabel("a (cm/g)")
    ax.set_ylabel("b (cm)")
    ax.set_zlabel("S(a,b) (cm²)")
    ax.set_title("Superficie de error z = S(a,b)")
    ax.view_init(28, -55)
    ax.legend()
    guardar("03_superficie.png")

    # 4. Trazas y secciones transversales
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    aa = np.linspace(0.005, 0.025, 200)
    for b0, nom in [(b, f"b = b* = {b:.3f}"), (0, "b = 0 (traza)"), (-1, "b = -1"), (1, "b = 1")]:
        ax1.plot(aa, [error_S(t, b0, X, Y) for t in aa], label=nom)
    ax1.scatter([a], [s_min], color="red", zorder=3)
    ax1.set_xlabel("a (cm/g)")
    ax1.set_ylabel("S (cm²)")
    ax1.set_title("Secciones con b constante: S(a, b₀)")
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)
    bb = np.linspace(-2, 3.5, 200)
    for a0, nom in [(a, f"a = a* = {a:.4f}"), (0, "a = 0 (traza)"), (0.010, "a = 0.010"), (0.020, "a = 0.020")]:
        ax2.plot(bb, [error_S(a0, t, X, Y) for t in bb], label=nom)
    ax2.scatter([b], [s_min], color="red", zorder=3)
    ax2.set_xlabel("b (cm)")
    ax2.set_ylabel("S (cm²)")
    ax2.set_title("Secciones con a constante: S(a₀, b)")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    guardar("04_trazas.png")

    # 5. Curvas de nivel
    fig, ax = plt.subplots(figsize=(8, 5.5))
    cs = ax.contour(A, B, S, levels=[2, 2.5, 4, 7, 12, 20, 35, 60, 100], cmap="viridis")
    ax.clabel(cs, fontsize=8)
    ax.plot(a, b, "r*", ms=14, label=f"(a*, b*) = ({a:.4f}, {b:.3f}),  S = {s_min:.2f}")
    ax.set_xlabel("a (cm/g)")
    ax.set_ylabel("b (cm)")
    ax.set_title("Curvas de nivel de S(a,b)")
    ax.legend()
    ax.grid(alpha=0.3)
    guardar("05_curvas_nivel.png")

    # 6. Residuos vs x
    e = np.array(residuos(a, b, X, Y))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0, color="k", lw=1)
    ax.vlines(x, 0, e, color="gray", lw=1)
    ax.scatter(x, e, color="tab:red", zorder=3)
    for nom, xi, ei in zip(OBJETOS, x, e):
        ax.annotate(nom, (xi, ei), textcoords="offset points", xytext=(5, 5), fontsize=7)
    ax.set_xlabel("Masa colgada x (g)")
    ax.set_ylabel("Residuo e (cm)")
    ax.set_title("Residuos en función de x")
    ax.grid(alpha=0.3)
    guardar("06_residuos.png")

    # 7. Histograma de residuos
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(e, bins=np.arange(-0.75, 1.26, 0.25), edgecolor="k", color="tab:orange")
    ax.axvline(0, color="k", ls="--")
    ax.set_xlabel("Residuo e (cm)")
    ax.set_ylabel("Cantidad de datos")
    ax.set_title("Histograma de los residuos")
    guardar("07_histograma.png")

    # 8. Influencia de un dato (opcion B)
    i = OBJETOS.index("Reproductor / parlante")
    x2, y2 = X[:i] + X[i + 1:], Y[:i] + Y[i + 1:]
    a2, b2 = ajustar(x2, y2)
    fig, ax = plt.subplots(figsize=(8, 5))
    puntos(ax, etiquetas=False)
    ax.scatter([X[i]], [Y[i]], s=160, facecolors="none", edgecolors="red", label="Parlante (dato retirado)")
    ax.plot(xs, a * xs + b, "r", label=f"Con los 10 datos: y = {a:.4f}x {b:+.3f}")
    ax.plot(xs, a2 * xs + b2, "g--", label=f"Sin el parlante: y = {a2:.4f}x {b2:+.3f}")
    ax.set_title("Influencia del dato del parlante en la recta")
    ax.legend(fontsize=8)
    guardar("08_influencia.png")


# Rectas "no optimas" para comparar con la optima: (a, b)
OTRAS_RECTAS = [(0.012, 0.3), (0.018, -0.5), (0.0151, 0.5)]


def main():
    # Metodo propio
    a, b = ajustar(X, Y)
    s_min = error_S(a, b, X, Y)
    rmse, r2 = calidad(a, b, X, Y)
    print(f"Sumas (n, Sx, Sy, Sxx, Sxy, Syy): {sumas(X, Y)}")
    print(f"Codigo propio : a* = {a:.8f}  b* = {b:.8f}  S_min = {s_min:.8f}")
    print(f"RMSE = {rmse:.4f} cm   R^2 = {r2:.4f}")

    # Hessiano y verificacion numerica
    H = hessiano(X)
    det = H[0][0] * H[1][1] - H[0][1] * H[1][0]
    vals = np.linalg.eigvalsh(np.array(H, float))
    print(f"Hessiano = {H}   det = {det}   valores propios = {vals}")
    assert H[0][0] > 0 and det > 0 and all(vals > 0), "El punto critico no es un minimo"
    # Hessiano por diferencias finitas centradas (S es cuadratica: debe coincidir)
    h = 1e-3
    f = lambda p, q: error_S(p, q, X, Y)
    Hn = [[(f(a + h, b) - 2 * f(a, b) + f(a - h, b)) / h**2,
           (f(a + h, b + h) - f(a + h, b - h) - f(a - h, b + h) + f(a - h, b - h)) / (4 * h**2)],
          [0, (f(a, b + h) - 2 * f(a, b) + f(a, b - h)) / h**2]]
    Hn[1][0] = Hn[0][1]
    print(f"Hessiano numerico (diferencias finitas) = {np.round(Hn, 3).tolist()}")
    assert np.allclose(Hn, H, rtol=1e-4)

    # Verificacion con la biblioteca
    a_lib, b_lib = np.polyfit(X, Y, 1)
    s_lib = error_S(a_lib, b_lib, X, Y)
    print(f"numpy.polyfit : a  = {a_lib:.8f}  b  = {b_lib:.8f}  S_min = {s_lib:.8f}")
    assert abs(a - a_lib) < 1e-9 and abs(b - b_lib) < 1e-9, "El codigo propio no coincide con numpy"

    # S en el minimo debe ser menor que en cualquier otra recta
    for a2, b2 in OTRAS_RECTAS:
        assert error_S(a2, b2, X, Y) > s_min

    graficas(a, b)
    print(f"Graficas guardadas en {FIG}")


if __name__ == "__main__":
    main()

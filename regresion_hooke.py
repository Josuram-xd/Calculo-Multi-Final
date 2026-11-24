"""Regresion lineal por minimos cuadrados para el experimento del resorte (Ley de Hooke).

Implementa las formulas deducidas a mano (grad S = 0), calcula el Hessiano,
compara con numpy.polyfit y genera todas las graficas del informe en figuras/.

Ademas incluye el analisis pedido en las recomendaciones del docente:
  1. Intervalos de confianza y sensibilidad de la pendiente y de k (minimo y maximo).
  2. Regresion polinomica (grados 1 a 4) para mostrar que no conviene otra funcion.
  3. RMSE expresado en las unidades del fenomeno (cm, mm, g, N, %).
  4. Errores de los instrumentos (regla y gramera) y su propagacion.

Los valores de ese analisis se guardan en presentacion/valores.tex para la presentacion.

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
CORTOS = ["sin carga", "llave", "tornillo", "taza", "cinta", "herradura", "LG", "parlante", "libro", "alicate"]
X = [0, 15, 70, 92, 150, 185, 190, 220, 300, 410]
Y = [0.0, 0.1, 0.4, 1.6, 1.9, 2.5, 2.9, 4.2, 4.8, 5.6]

G = 9.8  # m/s^2

# Instrumentos
RES_REGLA = 0.1    # cm, division minima de la regla
RES_GRAMERA = 1.0  # g, division minima de la gramera (balanza de cocina)
LECTURAS_POR_DATO = 3  # y = lectura total - largo del objeto - L0  -> tres lecturas de regla
ANCHO_HIST = 0.05  # cm, ancho de cada intervalo del histograma de residuos

# Valores criticos (tablas) para 95 % de confianza: t(0,975; gl) y F(0,95; 1, gl)
T975 = {5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306}
F95 = {(1, 5): 6.61, (1, 6): 5.99, (1, 7): 5.59, (2, 6): 5.14, (3, 5): 5.41}

RAIZ = Path(__file__).parent
FIG = RAIZ / "figuras"
VALORES_TEX = RAIZ / "presentacion" / "valores.tex"

# Paleta y letra comunes a todo el proyecto (estilo.py)
from estilo import AZUL, GRIS, MORADO, NARANJA, ROJO, VERDE, comas  # noqa: E402


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


def k_de(a):
    """Constante del resorte (N/m) a partir de la pendiente a (cm/g): a = g/k."""
    return G / (a * 10)  # 1 cm/g = 10 m/kg


# ---------- 3. Recomendacion 1: intervalos de confianza y sensibilidad ----------
def intervalos(x, y):
    """Errores estandar, intervalos al 95 % de a, b y k, y bandas de la recta."""
    n, sx, sy, sxx, _, _ = sumas(x, y)
    a, b = ajustar(x, y)
    s = (error_S(a, b, x, y) / (n - 2)) ** 0.5   # error estandar de la regresion
    xm = sx / n
    sxx_c = sxx - n * xm * xm                     # suma de (x_i - xm)^2
    se_a = s / sxx_c ** 0.5
    se_b = s * (1 / n + xm * xm / sxx_c) ** 0.5
    t = T975[n - 2]
    a_lo, a_hi = a - t * se_a, a + t * se_a
    return dict(n=n, a=a, b=b, s=s, xm=xm, sxx_c=sxx_c, se_a=se_a, se_b=se_b, t=t,
                a_lo=a_lo, a_hi=a_hi, b_lo=b - t * se_b, b_hi=b + t * se_b,
                k=k_de(a), k_lo=k_de(a_hi), k_hi=k_de(a_lo), u_k=k_de(a) * se_a / a,
                t_b=b / se_b, t_a=a / se_a)


def banda(ic, xs, prediccion=False):
    """Semiancho de la banda de confianza (recta media) o de prediccion (dato nuevo)."""
    extra = 1.0 if prediccion else 0.0
    return ic["t"] * ic["s"] * np.sqrt(extra + 1 / ic["n"] + (xs - ic["xm"]) ** 2 / ic["sxx_c"])


def jackknife(x, y):
    """k al quitar cada dato, uno a la vez (sensibilidad a cada medicion)."""
    ks = []
    for i in range(len(x)):
        a, _ = ajustar(x[:i] + x[i + 1:], y[:i] + y[i + 1:])
        ks.append(k_de(a))
    return ks


# ---------- 4. Recomendacion 4: errores de los instrumentos ----------
def incertidumbre_instrumental():
    """Incertidumbre tipo B (distribucion rectangular: resolucion / (2*raiz(3)))."""
    u_lect = RES_REGLA / (2 * 3 ** 0.5)
    u_y = u_lect * LECTURAS_POR_DATO ** 0.5        # y combina tres lecturas
    e_max_y = LECTURAS_POR_DATO * RES_REGLA / 2     # peor caso: errores sumados
    u_x = RES_GRAMERA / (2 * 3 ** 0.5)
    return dict(u_lect=u_lect, u_y=u_y, e_max_y=e_max_y, u_x=u_x, e_max_x=RES_GRAMERA / 2)


def montecarlo(ui, repeticiones=20000, semilla=1):
    """Repite el ajuste perturbando cada lectura dentro del error de los instrumentos."""
    rng = np.random.default_rng(semilla)
    x, y = np.array(X, float), np.array(Y, float)
    m = len(x)
    # cada y viene de tres lecturas de la regla, cada una con error uniforme en +-0,05 cm
    dy = rng.uniform(-RES_REGLA / 2, RES_REGLA / 2, (repeticiones, m, LECTURAS_POR_DATO)).sum(axis=2)
    dx = rng.uniform(-RES_GRAMERA / 2, RES_GRAMERA / 2, (repeticiones, m))
    dx[:, 0] = 0.0  # sin carga: x = 0 exacto
    xx, yy = x + dx, y + dy
    xm, ym = xx.mean(axis=1, keepdims=True), yy.mean(axis=1, keepdims=True)
    a = ((xx - xm) * (yy - ym)).sum(axis=1) / ((xx - xm) ** 2).sum(axis=1)
    return k_de(a)


# ---------- 5. Recomendacion 2: regresion polinomica ----------
def polinomios(grados=(1, 2, 3, 4)):
    """Ajusta polinomios y compara S, RMSE, R2, R2 ajustado, AIC, validacion cruzada y prueba F."""
    x, y = np.array(X, float), np.array(Y, float)
    n = len(x)
    st = ((y - y.mean()) ** 2).sum()
    out = []
    for d in grados:
        p = d + 1
        c = np.polyfit(x, y, d)
        S = float(((y - np.polyval(c, x)) ** 2).sum())
        V = np.vander(x, p)
        cov = S / (n - p) * np.linalg.inv(V.T @ V)
        t_lider = abs(c[0]) / cov[0, 0] ** 0.5       # t del coeficiente de mayor grado
        loo = [(y[i] - np.polyval(np.polyfit(np.delete(x, i), np.delete(y, i), d), x[i])) ** 2 for i in range(n)]
        out.append(dict(grado=d, coef=c, S=S, rmse=(S / n) ** 0.5, r2=1 - S / st,
                        r2a=1 - (S / (n - p)) / (st / (n - 1)), aic=n * np.log(S / n) + 2 * p,
                        cv=float(np.mean(loo)) ** 0.5, t_lider=t_lider, t_crit=T975.get(n - p)))
    lin = out[0]
    for r in out[1:]:
        gl1, gl2 = r["grado"] - 1, n - r["grado"] - 1
        r["F"] = ((lin["S"] - r["S"]) / gl1) / (r["S"] / gl2)
        r["F_crit"] = F95.get((gl1, gl2))
    # Ley de Hooke pura: recta por el origen y = a x
    a0 = float((x * y).sum() / (x * x).sum())
    S0 = float(((y - a0 * x) ** 2).sum())
    return out, dict(a=a0, S=S0, rmse=(S0 / n) ** 0.5, k=k_de(a0))


# ---------- 6. Graficas ----------
def guardar(nombre):
    comas(plt.gcf())
    plt.tight_layout()
    plt.savefig(FIG / nombre, bbox_inches="tight")
    plt.close()


def puntos(ax, etiquetas=True):
    x, y = np.array(X, float), np.array(Y)
    ax.scatter(x, y, color=AZUL, s=40, zorder=3, label="Datos medidos")
    if etiquetas:
        for nom, xi, yi in zip(OBJETOS, x, y):
            ax.annotate(nom, (xi, yi), textcoords="offset points", xytext=(6, -11), fontsize=8, color=GRIS)
    ax.set_xlabel("Masa colgada x (g)")
    ax.set_ylabel("Estiramiento y (cm)")


def graficas(a, b):
    FIG.mkdir(exist_ok=True)
    x, y = np.array(X, float), np.array(Y)
    xs = np.linspace(-10, 430, 50)
    s_min = error_S(a, b, X, Y)

    # 1. Dispersion
    fig, ax = plt.subplots(figsize=(8, 5))
    puntos(ax)
    ax.set_title("Diagrama de dispersión: estiramiento vs. masa colgada")
    guardar("01_dispersion.png")

    # 2. Recta optima y otras rectas
    fig, ax = plt.subplots(figsize=(8, 5))
    puntos(ax, etiquetas=False)
    ax.plot(xs, a * xs + b, color=ROJO, lw=2.5, label=f"Óptima: a = {a:.4f};  b = {b:.3f};  S = {s_min:.2f}")
    for (a2, b2), est, col in zip(OTRAS_RECTAS, ["--", "-.", ":"], [NARANJA, VERDE, MORADO]):
        ax.plot(xs, a2 * xs + b2, est, color=col, lw=1.8, label=f"a = {a2};  b = {b2};  S = {error_S(a2, b2, X, Y):.2f}")
    ax.set_title("Recta de mínimos cuadrados comparada con otras rectas")
    ax.legend(fontsize=9)
    guardar("02_recta_ajuste.png")

    # Malla de S(a,b)
    A, B = np.meshgrid(np.linspace(0.005, 0.025, 200), np.linspace(-2, 2, 200))
    S = sum((yi - A * xi - B) ** 2 for xi, yi in zip(X, Y))

    # 3. Superficie
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(A, B, S, cmap="viridis", alpha=0.85)
    ax.scatter([a], [b], [s_min], color=ROJO, s=60, label=f"Mínimo ({a:.4f}; {b:.3f}; {s_min:.2f})")
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
    ax1.scatter([a], [s_min], color=ROJO, zorder=3)
    ax1.set_xlabel("a (cm/g)")
    ax1.set_ylabel("S (cm²)")
    ax1.set_title("Secciones con b constante: S(a, b₀)")
    ax1.legend(fontsize=8)
    bb = np.linspace(-2, 3.5, 200)
    for a0, nom in [(a, f"a = a* = {a:.4f}"), (0, "a = 0 (traza)"), (0.010, "a = 0.010"), (0.020, "a = 0.020")]:
        ax2.plot(bb, [error_S(a0, t, X, Y) for t in bb], label=nom)
    ax2.scatter([b], [s_min], color=ROJO, zorder=3)
    ax2.set_xlabel("b (cm)")
    ax2.set_ylabel("S (cm²)")
    ax2.set_title("Secciones con a constante: S(a₀, b)")
    ax2.legend(fontsize=8)
    guardar("04_trazas.png")

    # 5. Curvas de nivel
    fig, ax = plt.subplots(figsize=(8, 5.5))
    cs = ax.contour(A, B, S, levels=[2, 2.5, 4, 7, 12, 20, 35, 60, 100], cmap="viridis")
    ax.clabel(cs, fontsize=8)
    ax.plot(a, b, "*", color=ROJO, ms=14, label=f"(a*; b*) = ({a:.4f}; {b:.3f}),  S = {s_min:.2f}")
    ax.set_xlabel("a (cm/g)")
    ax.set_ylabel("b (cm)")
    ax.set_title("Curvas de nivel de S(a,b)")
    ax.legend()
    guardar("05_curvas_nivel.png")

    # 6. Residuos vs x
    e = np.array(residuos(a, b, X, Y))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0, color="k", lw=1)
    ax.vlines(x, 0, e, color=GRIS, lw=1)
    ax.scatter(x, e, color=ROJO, zorder=3)
    for nom, xi, ei in zip(OBJETOS, x, e):
        ax.annotate(nom, (xi, ei), textcoords="offset points", xytext=(5, 5), fontsize=8, color=GRIS)
    ax.set_xlabel("Masa colgada x (g)")
    ax.set_ylabel("Residuo e (cm)")
    ax.set_title("Residuos en función de x")
    guardar("06_residuos.png")

    # 7. Histograma de residuos
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bordes = np.arange(-0.70, 1.0 + ANCHO_HIST / 2, ANCHO_HIST)
    ax.hist(e, bins=bordes, edgecolor="white", color=NARANJA)
    ax.axvline(0, color="k", ls="--")
    ax.set_xticks(np.arange(-0.7, 1.01, 0.1))
    ax.tick_params(axis="x", labelsize=8)
    ax.set_yticks([0, 1, 2])
    ax.set_xlabel(f"Residuo e (cm), intervalos de {ANCHO_HIST:.2f} cm".replace(".", ","))
    ax.set_ylabel("Cantidad de datos")
    ax.set_title("Histograma de los residuos")
    guardar("07_histograma.png")

    # 8. Influencia de un dato (opcion B)
    i = OBJETOS.index("Reproductor / parlante")
    x2, y2 = X[:i] + X[i + 1:], Y[:i] + Y[i + 1:]
    a2, b2 = ajustar(x2, y2)
    fig, ax = plt.subplots(figsize=(8, 5))
    puntos(ax, etiquetas=False)
    ax.scatter([X[i]], [Y[i]], s=180, facecolors="none", edgecolors=ROJO, lw=1.5,
               label="Parlante (residuo más grande)")
    ax.tick_params(labelsize=12)
    ax.plot(xs, a * xs + b, color=ROJO, lw=2.5, label="Recta final (10 datos)")
    ax.plot(xs, a2 * xs + b2, "--", color=VERDE, lw=2.5, label="Prueba sin el parlante")
    ax.set_title("Sensibilidad de la recta al dato del parlante")
    ax.legend(fontsize=13)
    guardar("08_influencia.png")

    graficas_gradiente(a, b)


def graficas_gradiente(a, b):
    """Figuras del gradiente (secciones 5.1.2, 6.3.1 y 6.3.2)."""
    x, y = np.array(X, float), np.array(Y)
    s_min = error_S(a, b, X, Y)
    n, sx, sy, sxx, sxy, _ = sumas(X, Y)

    # 9. Aportes de cada dato a dS/da
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, (pa, pb, tit) in zip(axs, [(0, 0, "Recta A (a = 0, b = 0)"), (a, b, "Recta óptima (a*, b*)")]):
        ap = -2 * x * (y - pa * x - pb)
        col = [ROJO if v < 0 else AZUL for v in ap] if pa == 0 else [VERDE if v < 0 else AZUL for v in ap]
        ax.bar(CORTOS, ap, color=col, edgecolor="white")
        ax.axhline(0, color="k", lw=1)
        total = ap.sum() if abs(ap.sum()) > 1e-6 else 0.0
        ax.set_title(f"{tit}\nsuma de los 10 aportes = " + f"{total:,.1f}".replace(",", " ").replace(".", ","),
                     fontsize=12)
        ax.set_ylabel("aporte del dato a ∂S/∂a")
        ax.tick_params(axis="x", rotation=40)
        ax.grid(axis="x", visible=False)
    axs[0].text(0.08, 0.2, "los 10 aportes son negativos:\nla suma no se cancela", transform=axs[0].transAxes,
                color=ROJO, weight="bold")
    axs[1].text(0.04, 0.08, "positivos y negativos\nse cancelan: ∂S/∂a = 0", transform=axs[1].transAxes,
                color=VERDE, weight="bold")
    guardar("09_aportes_gradiente.png")

    # malla en a' = 100 a
    Ap, B = np.meshgrid(np.linspace(0, 2.6, 300), np.linspace(-1.6, 1.8, 300))
    S = sum((yi - Ap / 100 * xi - B) ** 2 for xi, yi in zip(X, Y))
    niveles = [2, 5, 10, 20, 40, 60, 80, 100]

    def grad(pa, pb):
        return -2 * (sxy - pa * sxx - pb * sx), -2 * (sy - pa * sx - n * pb)

    # 10. El gradiente sobre el mapa (3D + curvas de nivel)
    fig = plt.figure(figsize=(12, 5.2))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    Sm = np.where(S <= 110, S, np.nan)
    ax.plot_surface(Ap, B, Sm, cmap="viridis_r", alpha=0.9, rstride=4, cstride=4, lw=0)
    ax.scatter([0], [0], [93.04], color=ROJO, s=50)
    ax.text(0, 0, 100, "A (S = 93)", color=ROJO, weight="bold")
    ax.scatter([100 * a], [b], [s_min], color="k", s=40)
    ax.set_xlabel("a' = 100·a")
    ax.set_ylabel("b")
    ax.set_zlabel("S")
    ax.set_title("El valle visto de lado")
    ax.view_init(28, -60)
    ax = fig.add_subplot(1, 2, 2)
    ax.contourf(Ap, B, S, levels=[0] + niveles, cmap="viridis_r", alpha=0.9)
    cs = ax.contour(Ap, B, S, levels=niveles, colors="k", linewidths=0.7)
    ax.clabel(cs, fontsize=8)
    ga, gb = grad(0, 0)
    d = -np.array([ga / 100, gb])
    d = d / np.linalg.norm(d) * 0.8
    ax.annotate("", xy=(d[0], d[1]), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=ROJO, lw=2.5))
    ax.plot(0, 0, "o", color=ROJO)
    ax.text(0.05, -0.2, "A", color=ROJO, weight="bold", fontsize=13)
    ax.text(0.1, 0.95, "−∇S: hacia donde\nbaja el error", color=ROJO, weight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.plot(100 * a, b, "k*", ms=14)
    ax.text(100 * a + 0.08, b - 0.3, "mínimo", weight="bold", bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.set_xlabel("a' = 100·a")
    ax.set_ylabel("b")
    ax.set_title("El mismo valle visto desde arriba")
    ax.grid(False)
    guardar("10_gradiente_mapa.png")

    # 11. El gradiente como vector y el tamano del paso
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.contourf(Ap, B, S, levels=[0] + niveles, cmap="viridis_r", alpha=0.9)
    cs = ax1.contour(Ap, B, S, levels=niveles, colors="k", linewidths=0.7)
    ax1.clabel(cs, fontsize=8)
    for pa, pb, nom in [(0, 0, "A"), (0.012, 0.3, "B")]:
        ga, gb = grad(pa, pb)
        v = np.array([ga / 100, gb])
        v = v / np.linalg.norm(v) * 0.75
        P = np.array([100 * pa, pb])
        ax1.annotate("", xy=P + v, xytext=P, arrowprops=dict(arrowstyle="-|>", color=ROJO, lw=2.2))
        ax1.annotate("", xy=P - v, xytext=P, arrowprops=dict(arrowstyle="-|>", color="white", lw=2.2))
        ax1.plot(*P, "ko", ms=5)
        txt = f"{nom}: ∇S = ({ga:,.1f}; {gb:,.1f})".replace(",", " ").replace(".", ",")
        ox, oy = (-0.95, 0.35) if nom == "A" else (0.1, 0.55)
        ax1.text(P[0] + ox, P[1] + oy, txt, fontsize=9, bbox=dict(fc="white", ec="none", alpha=0.9))
    ax1.plot(100 * a, b, "k*", ms=13)
    ax1.set_xlim(-1.0, 2.6)
    ax1.set_xlabel("a' = 100·a")
    ax1.set_ylabel("b")
    ax1.set_title("rojo: ∇S (el error sube)   blanco: −∇S (baja)", fontsize=12)
    ax1.grid(False)
    ga, gb = grad(0, 0)
    eta = np.linspace(0, 2.6e-6, 300)
    Se = [error_S(-t * ga, -t * gb, X, Y) for t in eta]
    ax2.plot(eta * 1e6, Se, color=AZUL, lw=2.5)
    ax2.axhline(93.04, color=GRIS, ls=":")
    ax2.text(1.0, 96, "S de la recta A = 93,04", color=GRIS, fontsize=9)
    for t, col, txt, dx in [(0.1e-6, NARANJA, "η muy chico:\navanza poco", 0.12),
                            (1.0e-6, VERDE, "η adecuado", 0.1), (2.2e-6, ROJO, "η muy grande:\nse pasa del valle", -0.95)]:
        v = error_S(-t * ga, -t * gb, X, Y)
        ax2.plot(t * 1e6, v, "o", color=col, ms=9)
        ax2.text(t * 1e6 + dx, v + 4, txt, color=col, weight="bold", fontsize=10)
    ax2.set_ylim(0, 110)
    ax2.set_xlabel("tamaño del paso η (×10⁻⁶)")
    ax2.set_ylabel("S después de dar el paso")
    ax2.set_title("η no sale del gradiente: se escoge", fontsize=12)
    guardar("11_gradiente_paso.png")


def graficas_recomendaciones(a, b, ic, ui, ks_mc, ks_jk, polis, origen):
    """Figuras nuevas: incertidumbre, bandas, sensibilidad de k, polinomios y RMSE."""
    x, y = np.array(X, float), np.array(Y)
    xs = np.linspace(0, 420, 300)

    # 12. Datos con barras de error del instrumento
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(x, y, yerr=ui["e_max_y"], xerr=ui["e_max_x"], fmt="o", color=AZUL, ecolor=AZUL,
                capsize=4, ms=6, label=f"Datos ± error máx. del instrumento (±{ui['e_max_y']:.2f} cm)".replace(".", ","))
    ax.plot(xs, a * xs + b, color=ROJO, lw=2, label="Recta de mínimos cuadrados")
    rm = calidad(a, b, X, Y)[0]
    ax.fill_between(xs, a * xs + b - rm, a * xs + b + rm, color=ROJO, alpha=0.12,
                    label=f"± RMSE = ±{rm:.2f} cm".replace(".", ","))
    ax.set_xlabel("Masa colgada x (g)")
    ax.set_ylabel("Estiramiento y (cm)")
    ax.set_title("Error del instrumento vs. dispersión de los datos")
    ax.legend(fontsize=9, loc="upper left")
    guardar("12_incertidumbre.png")

    # 13. Bandas de confianza y de prediccion
    fig, ax = plt.subplots(figsize=(8, 5))
    yl = a * xs + b
    bp, bc = banda(ic, xs, True), banda(ic, xs)
    ax.fill_between(xs, yl - bp, yl + bp, color=NARANJA, alpha=0.18, label="Banda de predicción 95 % (un dato nuevo)")
    ax.fill_between(xs, yl - bc, yl + bc, color=ROJO, alpha=0.25, label="Banda de confianza 95 % (la recta)")
    ax.plot(xs, yl, color=ROJO, lw=2, label="Recta ajustada")
    ax.plot(xs, ic["a_lo"] * (xs - ic["xm"]) + y.mean(), ":", color=GRIS, lw=1.5, label="Pendiente mínima y máxima (IC 95 %)")
    ax.plot(xs, ic["a_hi"] * (xs - ic["xm"]) + y.mean(), ":", color=GRIS, lw=1.5)
    ax.scatter(x, y, color=AZUL, zorder=3, s=40, label="Datos medidos")
    ax.set_xlabel("Masa colgada x (g)")
    ax.set_ylabel("Estiramiento y (cm)")
    ax.set_title("Intervalos de confianza de la recta")
    ax.legend(fontsize=8.5, loc="upper left")
    guardar("13_bandas_confianza.png")

    # 14. Sensibilidad de k
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw=dict(width_ratios=[1.1, 1]))
    orden = np.argsort(ks_jk)
    ax1.barh(np.array(CORTOS)[orden], np.array(ks_jk)[orden] - ic["k"], left=ic["k"],
             color=[ROJO if CORTOS[i] == "parlante" else AZUL for i in orden])
    ax1.axvline(ic["k"], color="k", lw=1.2)
    ax1.axvspan(ic["k_lo"], ic["k_hi"], color=NARANJA, alpha=0.15, label="IC 95 % de k")
    ax1.set_xlabel("k calculado sin esa medición (N/m)")
    ax1.set_title("Sensibilidad de k a cada medición", fontsize=12)
    ax1.legend(loc="lower right", fontsize=9)
    ax1.grid(axis="y", visible=False)
    ax2.hist(ks_mc, bins=60, color=VERDE, alpha=0.85, label="Error de los instrumentos\n(Monte Carlo, 20 000 repeticiones)")
    ax2.axvspan(ic["k_lo"], ic["k_hi"], color=NARANJA, alpha=0.15, label="IC 95 % estadístico")
    ax2.axvline(ic["k"], color="k", lw=1.2)
    ax2.set_xlim(ic["k_lo"] - 3, ic["k_hi"] + 3)
    ax2.set_xlabel("k (N/m)")
    ax2.set_ylabel("frecuencia")
    ax2.set_title("Origen de la incertidumbre de k", fontsize=12)
    ax2.legend(fontsize=8.5, loc="upper right")
    guardar("14_sensibilidad_k.png")

    # 15. Regresion polinomica: curvas y diferencia de cada polinomio con la recta
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.4))
    xe = np.linspace(0, 410, 400)
    lin = polis[0]["coef"]
    colores, estilos = [ROJO, NARANJA, VERDE, MORADO], ["-", "--", "-.", ":"]
    ax1.scatter(x, y, color="k", zorder=4, s=45, label="Datos medidos")
    for r, col, est in zip(polis, colores, estilos):
        ax1.plot(xe, np.polyval(r["coef"], xe), est, color=col, lw=3 if r["grado"] == 1 else 2.4,
                 label="grado 1 (recta)" if r["grado"] == 1 else f"grado {r['grado']}")
    ax1.set_xlabel("Masa colgada x (g)")
    ax1.set_ylabel("Estiramiento y (cm)")
    ax1.set_title("Polinomios de grado 1 a 4 (mismos datos)")
    ax1.legend(fontsize=13, loc="upper left")
    ax2.axhline(0, color=ROJO, lw=3, label="recta (referencia)")
    ax2.scatter(x, y - np.polyval(lin, x), color="k", zorder=4, s=45, label="datos (residuo respecto a la recta)")
    for r, col, est in zip(polis[1:], colores[1:], estilos[1:]):
        ax2.plot(xe, np.polyval(r["coef"], xe) - np.polyval(lin, xe), est, color=col, lw=2.4, label=f"grado {r['grado']}")
    ax2.axhspan(-ic["s"], ic["s"], color=GRIS, alpha=0.15, label=f"± error estándar s = {ic['s']:.2f} cm".replace(".", ","))
    ax2.set_xlabel("Masa colgada x (g)")
    ax2.set_ylabel("Diferencia con la recta (cm)")
    ax2.set_title("Diferencia de cada polinomio con la recta (ampliada)")
    ax2.legend(fontsize=11.5, loc="upper left", ncol=2)
    ax2.set_ylim(-1.0, 1.6)
    for axx in (ax1, ax2):
        axx.tick_params(labelsize=13)
        axx.xaxis.label.set_size(14)
        axx.yaxis.label.set_size(14)
        axx.title.set_size(16)
    guardar("15_polinomios.png")

    # 17. Error de cada modelo con los datos usados y con datos nuevos
    fig, ax2 = plt.subplots(figsize=(10, 5.5))
    g = np.arange(len(polis))
    ax2.bar(g - 0.2, [r["rmse"] for r in polis], 0.4, color=AZUL, label="RMSE con los datos usados en el ajuste")
    cvs = [r["cv"] for r in polis]
    ax2.bar(g + 0.2, np.minimum(cvs, 1.2), 0.4, color=NARANJA,
            label="Error al predecir cada dato con un ajuste\nhecho con los otros 9 (validación cruzada)")
    for gi, v, rr in zip(g, cvs, polis):
        txt = f"{v:.2f}".replace(".", ",") + ("\n(barra recortada)" if v > 1.2 else "")
        ax2.text(gi + 0.2, min(v, 1.2) + 0.02, txt, ha="center", fontsize=12, weight="bold")
        ax2.text(gi - 0.2, rr["rmse"] + 0.02, f"{rr['rmse']:.2f}".replace(".", ","), ha="center", fontsize=12)
    ax2.set_xticks(g, ["grado 1\n(recta)", "grado 2", "grado 3", "grado 4"], fontsize=12)
    ax2.set_ylim(0, 1.5)
    ax2.set_ylabel("cm")
    ax2.set_title("Más grado baja el error en los datos usados, pero no predice mejor")
    ax2.legend(fontsize=10.5, loc="upper left")
    ax2.grid(axis="x", visible=False)
    guardar("17_polinomios_error.png")

    # 16. RMSE en unidades del fenomeno
    fig, ax = plt.subplots(figsize=(8, 4.2))
    rm = calidad(a, b, X, Y)[0]
    barras = [("Resolución de la regla", RES_REGLA, GRIS), ("Error instrumental de y (u_y)", ui["u_y"], VERDE),
              ("Error máx. de lectura de y", ui["e_max_y"], VERDE), ("RMSE del ajuste", rm, ROJO),
              ("Error estándar s (n − 2)", ic["s"], ROJO)]
    ax.barh([t for t, _, _ in barras][::-1], [v for _, v, _ in barras][::-1], color=[c for _, _, c in barras][::-1])
    for i, (_, v, _) in enumerate(barras[::-1]):
        ax.text(v + 0.01, i, f"{v:.2f} cm = {10 * v:.1f} mm".replace(".", ","), va="center", fontsize=9.5)
    ax.set_xlim(0, 0.68)
    ax.set_xlabel("cm")
    ax.set_title("Tamaño del RMSE comparado con la precisión de la regla", fontsize=12)
    ax.grid(axis="y", visible=False)
    guardar("16_rmse_escala.png")


# ---------- 7. Valores para la presentacion ----------
def coma(v, d):
    return f"{v:.{d}f}".replace(".", "{,}").replace("-", "-")


def escribir_valores(a, b, ic, ui, ks_mc, ks_jk, polis, origen):
    rm, r2 = calidad(a, b, X, Y)
    jmin, jmax = int(np.argmin(ks_jk)), int(np.argmax(ks_jk))
    mc_lo, mc_hi = np.percentile(ks_mc, [2.5, 97.5])
    v = {
        "aCI": coma(a, 5), "seA": coma(ic["se_a"], 5), "aLo": coma(ic["a_lo"], 5), "aHi": coma(ic["a_hi"], 5),
        "bCI": coma(b, 3), "seB": coma(ic["se_b"], 3), "bLo": coma(ic["b_lo"], 3), "bHi": coma(ic["b_hi"], 3),
        "tB": coma(ic["t_b"], 2), "tA": coma(ic["t_a"], 1),
        "sReg": coma(ic["s"], 2), "tCrit": coma(ic["t"], 3),
        "kVal": coma(ic["k"], 1), "kLo": coma(ic["k_lo"], 1), "kHi": coma(ic["k_hi"], 1), "uK": coma(ic["u_k"], 1),
        "kRango": coma(ic["k_hi"] - ic["k_lo"], 1),
        "jkMin": coma(ks_jk[jmin], 1), "jkMax": coma(ks_jk[jmax], 1),
        "jkMinObj": CORTOS[jmin], "jkMaxObj": CORTOS[jmax],
        "mcLo": coma(mc_lo, 1), "mcHi": coma(mc_hi, 1), "mcSd": coma(np.std(ks_mc), 2),
        "bandaP": coma(banda(ic, np.array([200.0]), True)[0], 2),
        "bandaC": coma(banda(ic, np.array([200.0]))[0], 2),
        "uLect": coma(ui["u_lect"], 3), "uY": coma(ui["u_y"], 2), "eMaxY": coma(ui["e_max_y"], 2),
        "uX": coma(ui["u_x"], 2), "eMaxX": coma(ui["e_max_x"], 1), "uXy": coma(a * ui["u_x"], 4),
        "razon": coma(rm / ui["u_y"], 0), "razonMax": coma(rm / ui["e_max_y"], 1),
        "rmse": coma(rm, 2), "rmseMm": coma(10 * rm, 1), "rmseG": coma(rm / a, 0),
        "rmseN": coma(rm / a / 1000 * G, 2), "rmseRango": coma(100 * rm / (max(Y) - min(Y)), 1),
        "rmseMedia": coma(100 * rm / (sum(Y) / len(Y)), 0), "rmseRes": coma(rm / RES_REGLA, 1),
        "orA": coma(origen["a"], 5), "orS": coma(origen["S"], 2), "orK": coma(origen["k"], 1),
        "orRmse": coma(origen["rmse"], 2),
    }
    for r in polis:
        g = "ABCD"[r["grado"] - 1]
        v[f"p{g}S"] = coma(r["S"], 2)
        v[f"p{g}rmse"] = coma(r["rmse"], 2)
        v[f"p{g}rr"] = coma(r["r2"], 4)
        v[f"p{g}ra"] = coma(r["r2a"], 4)
        v[f"p{g}aic"] = coma(r["aic"], 1)
        v[f"p{g}cv"] = coma(r["cv"], 2)
        v[f"p{g}t"] = coma(r["t_lider"], 2)
        v[f"p{g}tc"] = coma(r["t_crit"], 3)
        if "F" in r:
            v[f"p{g}F"] = coma(r["F"], 2)
            v[f"p{g}Fc"] = coma(r["F_crit"], 2)
    VALORES_TEX.parent.mkdir(exist_ok=True)
    lineas = ["% Generado por regresion_hooke.py: no editar a mano."]
    lineas += [f"\\newcommand{{\\v{k}}}{{{val}}}" for k, val in v.items()]
    VALORES_TEX.write_text("\n".join(lineas) + "\n", encoding="utf-8")


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

    # ---- Recomendaciones ----
    ic = intervalos(X, Y)
    print(f"\n[1] IC 95 %: a = {a:.5f} ± {ic['t'] * ic['se_a']:.5f}  ->  [{ic['a_lo']:.5f}, {ic['a_hi']:.5f}] cm/g")
    print(f"           b = {b:.3f} ± {ic['t'] * ic['se_b']:.3f}  ->  [{ic['b_lo']:.3f}, {ic['b_hi']:.3f}] cm (contiene 0)")
    print(f"           k = {ic['k']:.1f} N/m  ->  k_min = {ic['k_lo']:.1f}, k_max = {ic['k_hi']:.1f} N/m")
    ks_jk = jackknife(X, Y)
    print(f"    Quitando un dato a la vez: k entre {min(ks_jk):.1f} y {max(ks_jk):.1f} N/m")

    polis, origen = polinomios()
    print("\n[2] Grado   S      RMSE   R2      R2aj    AIC     RMSE_cv  t_lider/t_crit   F/F_crit")
    for r in polis:
        extra = f"  {r['F']:.2f}/{r['F_crit']}" if "F" in r else ""
        print(f"    {r['grado']}   {r['S']:.3f}  {r['rmse']:.3f}  {r['r2']:.4f}  {r['r2a']:.4f}  {r['aic']:6.2f}"
              f"  {r['cv']:.3f}    {r['t_lider']:.2f}/{r['t_crit']}{extra}")
    print(f"    Recta por el origen y = a x: a = {origen['a']:.5f}, S = {origen['S']:.3f}, k = {origen['k']:.1f} N/m")
    for r in polis[1:]:
        assert r["F"] < r["F_crit"], "Un polinomio de mayor grado mejora significativamente"

    print(f"\n[3] RMSE = {rmse:.3f} cm = {10 * rmse:.1f} mm  ~ {rmse / a:.0f} g de masa  ~ {rmse / a / 1000 * G:.2f} N")

    ui = incertidumbre_instrumental()
    ks_mc = montecarlo(ui)
    print(f"\n[4] Regla: u(lectura) = {ui['u_lect']:.3f} cm, u(y) = {ui['u_y']:.3f} cm, error max y = ±{ui['e_max_y']:.2f} cm")
    print(f"    Gramera: u(x) = {ui['u_x']:.2f} g  ->  efecto en y = {a * ui['u_x']:.4f} cm")
    print(f"    RMSE / u(y) = {rmse / ui['u_y']:.1f}: la dispersion no viene de los instrumentos")
    print(f"    Monte Carlo (instrumentos): k = {np.mean(ks_mc):.1f} ± {np.std(ks_mc):.2f} N/m")

    graficas(a, b)
    graficas_recomendaciones(a, b, ic, ui, ks_mc, ks_jk, polis, origen)
    escribir_valores(a, b, ic, ui, ks_mc, ks_jk, polis, origen)
    print(f"\nGraficas guardadas en {FIG}\nValores para la presentacion en {VALORES_TEX}")


if __name__ == "__main__":
    main()

"""Genera los dos documentos Word del proyecto a partir de los datos:

- Ley_de_Hooke_Completado.docx   (informe final)
- Guia_paso_a_paso_a_mano.docx   (procedimiento manual completo)

Todos los numeros se calculan aqui, asi el texto nunca queda desfasado de los datos.
Uso:  python regresion_hooke.py && python diagramas.py && python generar_documentos.py
"""
import re
from pathlib import Path

import docx
import pypandoc
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from regresion_hooke import OBJETOS, OTRAS_RECTAS, X, Y, ajustar, calidad, error_S, residuos, sumas

RAIZ = Path(__file__).parent
L0 = 3.3  # longitud del resorte sin carga (cm)
LARGO_OBJETO = [None, 7.5, 7.1, 9.5, 11.0, 10.9, 15.8, 13.1, 20.0, 22.4]
LECTURA_TOTAL = [3.3, 10.9, 10.8, 14.4, 16.2, 16.7, 22.0, 20.6, 28.1, 31.3]
G = 9.8  # m/s^2


def c(v, d=None):
    """Numero con coma decimal. d = decimales (None: los necesarios)."""
    s = f"{v:.{d}f}" if d is not None else (f"{v:.6f}".rstrip("0").rstrip(".") if "." in f"{v:.6f}" else str(v))
    return s.replace(".", ",")


def cadena(vals, d=None):
    return " + ".join(c(v, d) for v in vals)


# ------------------------------------------------------------------ calculos
n, Sx, Sy, Sxx, Sxy, Syy = sumas(X, Y)
Sy, Sxy, Syy = round(Sy, 6), round(Sxy, 6), round(Syy, 6)
D = n * Sxx - Sx * Sx
a_cod, b_cod = ajustar(X, Y)
S_cod = error_S(a_cod, b_cod, X, Y)

# "A mano": lo que da la calculadora redondeando a 7 decimales
a = round((n * Sxy - Sx * Sy) / D, 7)
b = round((Sy - a * Sx) / n, 7)
yp = [round(a * xi + b, 4) for xi in X]
e = [round(yi - p, 4) for yi, p in zip(Y, yp)]
e2 = [round(t * t, 6) for t in e]
S = round(sum(e2), 4)
ym = Sy / n
ST = round(Syy - n * ym * ym, 4)
R2 = 1 - S / ST
RMSE = (S / n) ** 0.5

import numpy as np  # noqa: E402  (solo para la columna "biblioteca")

a_lib, b_lib = np.polyfit(X, Y, 1)
S_lib = error_S(a_lib, b_lib, X, Y)

detH = 4 * D
traza = 2 * Sxx + 2 * n
disc = traza**2 - 4 * detH
lam1, lam2 = (traza + disc**0.5) / 2, (traza - disc**0.5) / 2

# Opcion B: sin el parlante
ip = OBJETOS.index("Reproductor / parlante")
X2, Y2 = X[:ip] + X[ip + 1:], Y[:ip] + Y[ip + 1:]
n2, Sx2, Sy2, Sxx2, Sxy2, Syy2 = sumas(X2, Y2)
D2 = n2 * Sxx2 - Sx2 * Sx2
a2 = round((n2 * Sxy2 - Sx2 * Sy2) / D2, 7)
b2 = round((Sy2 - a2 * Sx2) / n2, 7)
S2 = error_S(a2, b2, X2, Y2)
RMSE2, R22 = calidad(a2, b2, X2, Y2)

k = G / (a * 10)  # a en cm/g  ->  10a en m/kg
k2 = G / (a2 * 10)
orden = sorted(range(n), key=lambda i: -abs(e[i]))

V = {
    "n": n, "Sx": Sx, "Sy": c(Sy), "Sxx": Sxx, "Sxy": c(Sxy), "Syy": c(Syy),
    "nSxy": c(n * Sxy), "SxSy": c(Sx * Sy), "numA": c(n * Sxy - Sx * Sy),
    "nSxx": n * Sxx, "SxSx": Sx * Sx, "D": D,
    "a": c(a, 7), "b": c(b, 7), "a4": c(a, 4), "b3": c(b, 3), "aSx": c(a * Sx, 7), "SyaSx": c(Sy - a * Sx, 7),
    "fac": c(Sx / n), "e2a": c(Sx / n * Sx), "e2c": c(Sx / n * Sy),
    "da": c(Sxx - Sx / n * Sx), "dc": c(Sxy - Sx / n * Sy),
    "chk1": c(Sxx * a + Sx * b, 2), "chk1a": c(Sxx * a, 3), "chk1b": c(Sx * b, 3),
    "chk2": c(Sx * a + n * b, 4), "chk2b": c(n * b, 6),
    "H11": 2 * Sxx, "H12": 2 * Sx, "H22": 2 * n, "p1": 2 * Sxx * 2 * n, "p2": 4 * Sx * Sx, "detH": detH,
    "traza": traza, "traza2": traza**2, "detH4": 4 * detH, "disc": disc, "rdisc": c(disc**0.5, 3),
    "lam1": c(lam1, 1), "lam2": c(lam2, 3),
    "S": c(S, 4), "S2d": c(S, 2), "aSxy": c(a * Sxy, 4), "bSy": c(b * Sy, 4), "Salt": c(Syy - a * Sxy - b * Sy, 4),
    "ym": c(ym), "ym2": c(ym * ym), "nym2": c(n * ym * ym), "ST": c(ST),
    "SST": c(S / ST, 4), "R2": c(R2, 4), "R2p": c(100 * R2, 1), "Sn": c(S / n, 5), "RMSE": c(RMSE, 4), "RMSE2d": c(RMSE, 2),
    "rango": c(max(Y) - min(Y)), "rmsep": c(100 * RMSE / (max(Y) - min(Y)), 1),
    "2Sxy": c(2 * Sxy), "2Sy": c(2 * Sy), "av0": c(Sxy / Sxx, 5), "Sav0": c(Syy - Sxy**2 / Sxx, 2),
    "2Sxxd": 2 * Sxx,
    "a10": c(a * 10, 6), "k": c(k, 1), "k2": c(k2, 1),
    "n2": n2, "Sx2": Sx2, "Sy2": c(Sy2), "Sxx2": Sxx2, "Sxy2": c(Sxy2),
    "nSxy2": c(n2 * Sxy2), "SxSy2": c(Sx2 * Sy2), "numA2": c(n2 * Sxy2 - Sx2 * Sy2),
    "nSxx2": n2 * Sxx2, "SxSx2": Sx2 * Sx2, "D2": D2, "a2": c(a2, 7), "b2": c(b2, 7), "a24": c(a2, 4), "b23": c(b2, 3),
    "aSx2": c(a2 * Sx2, 6), "SyaSx2": c(Sy2 - a2 * Sx2, 6),
    "S2": c(S2, 2), "RMSE2": c(RMSE2, 2), "R22": c(R22, 4),
    "dap": c(100 * (a2 - a) / a, 1), "db": c(b2 - b, 3), "xp": X[ip], "yp": c(Y[ip]), "ep": c(e[ip], 2),
    "o1": OBJETOS[orden[0]].lower(), "o1x": X[orden[0]], "o1e": c(e[orden[0]], 2),
    "o2": OBJETOS[orden[1]].lower(), "o2x": X[orden[1]], "o2e": c(e[orden[1]], 2),
    "o3": OBJETOS[orden[2]].lower(), "o3x": X[orden[2]], "o3e": c(e[orden[2]], 2),
    "sume": c(abs(round(sum(e), 3)), 3), "L0": c(L0),
}


def llenar(texto):
    """«k» -> valor (coma decimal).  «m:k» -> valor para modo matematico ({,})."""
    texto = re.sub(r"«m:(\w+)»", lambda m: str(V[m[1]]).replace(",", "{,}"), texto)
    return re.sub(r"«(\w+)»", lambda m: str(V[m[1]]), texto)


def tabla(cab, filas, anchos=None):
    """anchos: proporciones de columna (pandoc las toma del largo de los guiones)."""
    out = ["| " + " | ".join(cab) + " |", "|" + "".join("-" * (3 * w) + "|" for w in anchos or [1] * len(cab))]
    out += ["| " + " | ".join(str(t) for t in f) + " |" for f in filas]
    return "\n".join(out)


# ------------------------------------------------------------------ tablas
T_DATOS = tabla(
    ["N.º", "Objeto colgado", "Masa colgada x (g)", "Largo del objeto (cm)", "Lectura total (cm)",
     "Longitud del resorte L (cm)", "Estiramiento y (cm)"],
    [[i + 1, OBJETOS[i], X[i], "—" if LARGO_OBJETO[i] is None else c(LARGO_OBJETO[i], 1), c(LECTURA_TOTAL[i], 1),
      c(L0 + Y[i], 1), c(Y[i], 1)] for i in range(n)], anchos=[2, 7, 4, 4, 4, 5, 5])

T_RESTAS = tabla(
    ["N.º", "Objeto", "L = lectura total − largo del objeto", "y = L − «L0»"],
    [[i + 1, OBJETOS[i],
      f"{c(L0, 1)} (lectura directa)" if LARGO_OBJETO[i] is None
      else f"{c(LECTURA_TOTAL[i], 1)} − {c(LARGO_OBJETO[i], 1)} = {c(L0 + Y[i], 1)}",
      f"{c(L0 + Y[i], 1)} − {c(L0, 1)} = {c(Y[i], 1)}"] for i in range(n)])

T_SUMAS = tabla(
    ["i", "xᵢ", "yᵢ", "xᵢ² = xᵢ·xᵢ", "xᵢ·yᵢ", "yᵢ² = yᵢ·yᵢ"],
    [[i + 1, X[i], c(Y[i], 1), f"{X[i]}·{X[i]} = {X[i] ** 2}", f"{X[i]}·{c(Y[i], 1)} = {c(X[i] * Y[i])}",
      f"{c(Y[i], 1)}·{c(Y[i], 1)} = {c(Y[i] ** 2)}"] for i in range(n)]
    + [["**Suma**", f"**{Sx}**", f"**{c(Sy)}**", f"**{Sxx}**", f"**{c(Sxy)}**", f"**{c(Syy)}**"]])

T_RES_MANO = tabla(
    ["i", "xᵢ", "yᵢ", "ŷᵢ = a\\*·xᵢ + b\\*", "eᵢ = yᵢ − ŷᵢ", "eᵢ²"],
    [[i + 1, X[i], c(Y[i], 1), f"{c(a, 7)}·{X[i]} − {c(-b, 7)} = {c(yp[i], 4)}",
      f"{c(Y[i], 1)} − ({c(yp[i], 4)}) = {c(e[i], 4)}", c(e2[i], 6)] for i in range(n)]
    + [["**Suma**", "", "", "", f"**{c(sum(e), 4)}**", f"**{c(sum(e2), 6)}**"]], anchos=[2, 2, 2, 12, 9, 4])

T_ST = tabla(
    ["i", "yᵢ", "yᵢ − ȳ", "(yᵢ − ȳ)²"],
    [[i + 1, c(Y[i], 1), f"{c(Y[i], 1)} − {c(ym)} = {c(Y[i] - ym, 1)}", c((Y[i] - ym) ** 2, 2)] for i in range(n)]
    + [["**Suma**", "", f"**{c(abs(round(sum(Y) - n * ym, 6)))}**", f"**{c(sum((yi - ym) ** 2 for yi in Y), 2)}**"]])

T_RESIDUOS = tabla(
    ["Objeto", "x (g)", "y medido (cm)", "ŷ predicho (cm)", "Residuo e (cm)"],
    [[OBJETOS[i], X[i], c(Y[i], 1), c(yp[i], 2), ("+" if e[i] > 0 else "") + c(e[i], 2)] for i in range(n)])

T_COMP = tabla(
    ["Parámetro", "Analítico (a mano)", "Código propio", "Biblioteca (numpy.polyfit)", "Diferencia máxima"],
    [[nom, c(m, 7), c(co, 7), c(li, 7), f"{max(abs(m - co), abs(m - li), abs(co - li)):.1e}".replace(".", ",")]
     for nom, m, co, li in [("a (cm/g)", a, a_cod, a_lib), ("b (cm)", b, b_cod, b_lib), ("S mín (cm²)", S, S_cod, S_lib)]])

T_OTRAS = tabla(
    ["Recta", "a (cm/g)", "b (cm)", "S(a, b) (cm²)"],
    [["**Óptima (mínimos cuadrados)**", f"**{c(a, 4)}**", f"**{c(b, 3)}**", f"**{c(S, 2)}**"]]
    + [[f"Recta de prueba {j + 1}", c(p), c(q), c(error_S(p, q, X, Y), 2)] for j, (p, q) in enumerate(OTRAS_RECTAS)])

T_INFL = tabla(
    ["Ajuste", "a (cm/g)", "b (cm)", "S mín (cm²)", "RMSE (cm)", "R²", "k (N/m)"],
    [["Con los 10 datos", c(a, 5), c(b, 3), c(S, 2), c(RMSE, 2), c(R2, 4), c(k, 1)],
     ["Sin el parlante (9 datos)", c(a2, 5), c(b2, 3), c(S2, 2), c(RMSE2, 2), c(R22, 4), c(k2, 1)]])

T_SUMAS2 = tabla(
    ["Suma", "Con 10 datos", "Se resta (parlante)", "Con 9 datos"],
    [["n", n, 1, n2], ["Σx", Sx, X[ip], Sx2], ["Σy", c(Sy), c(Y[ip]), c(Sy2)],
     ["Σx²", Sxx, f"{X[ip]}² = {X[ip] ** 2}", Sxx2], ["Σxy", c(Sxy), f"{X[ip]}·{c(Y[ip])} = {c(X[ip] * Y[ip])}", c(Sxy2)]])

FOTOS = """
| | | |
|:---:|:---:|:---:|
| ![](fotos/img3.jpg){width=4.2cm} | ![](fotos/img5.jpg){width=4.2cm} | ![](fotos/img4.jpg){width=4.2cm} |
| Resorte sin carga | Tornillo grande | Herradura |
| ![](fotos/img7.jpg){width=4.2cm} | ![](fotos/img2.jpg){width=4.2cm} | ![](fotos/img6.jpg){width=4.2cm} |
| Teléfono LG | Reproductor / parlante | Alicate |

: Fotografías del montaje tomadas por el equipo.

| | | | |
|:---:|:---:|:---:|:---:|
| ![](fotos/img8.jpg){width=3.2cm} | ![](fotos/img9.jpg){width=3.2cm} | ![](fotos/img10.jpg){width=3.2cm} | ![](fotos/img11.jpg){width=3.2cm} |
| Llave grande | Taza plástica | Rollo de cinta | Libro pequeño |

: Imágenes ilustrativas de las otras cuatro cargas. No son fotografías de la medición: representan cómo se colgó cada objeto. Los valores de la tabla para estos objetos sí fueron medidos por el equipo.
"""

PSEUDO = """
```
ALGORITMO AjusteMinimosCuadrados
  LEER los n pares (x_i, y_i)

  // 1. Sumas (Diagrama 2)
  n <- 0; Sx <- 0; Sy <- 0; Sxx <- 0; Sxy <- 0; Syy <- 0
  PARA CADA par (x_i, y_i) HACER
      n   <- n + 1
      Sx  <- Sx  + x_i
      Sy  <- Sy  + y_i
      Sxx <- Sxx + x_i * x_i
      Sxy <- Sxy + x_i * y_i
      Syy <- Syy + y_i * y_i
  FIN PARA

  // 2. Punto critico: solucion de grad S = 0
  D <- n * Sxx - Sx * Sx
  SI D = 0 ENTONCES
      ESCRIBIR "Todos los x son iguales: no hay solucion unica"
      TERMINAR
  FIN SI
  a <- (n * Sxy - Sx * Sy) / D
  b <- (Sy - a * Sx) / n

  // 3. Error minimo y calidad (Diagrama 3)
  S <- 0; ST <- 0; ym <- Sy / n
  PARA CADA par (x_i, y_i) HACER
      e_i <- y_i - (a * x_i + b)
      S   <- S  + e_i * e_i
      ST  <- ST + (y_i - ym) * (y_i - ym)
  FIN PARA
  RMSE <- raiz(S / n)
  R2   <- 1 - S / ST

  // 4. Hessiano y criterio de la segunda derivada
  H    <- [[2*Sxx, 2*Sx], [2*Sx, 2*n]]
  detH <- 4 * D
  SI 2*Sxx > 0 Y detH > 0 ENTONCES
      ESCRIBIR "El punto critico es un minimo"
  SINO
      ESCRIBIR "El punto critico NO es un minimo"
  FIN SI

  // 5. Verificacion y salida
  (a_lib, b_lib) <- regresion de la biblioteca (numpy.polyfit)
  ESCRIBIR a, b, S, RMSE, R2, H, detH y las diferencias con la biblioteca
  DIBUJAR dispersion, rectas, superficie, trazas, curvas de nivel y residuos
FIN ALGORITMO
```
"""

# ------------------------------------------------------------------ informe
INFORME = r"""---
title: "Ley de Hooke: estiramiento de un resorte y masa colgada"
subtitle: "Proyecto final de Cálculo Multivariable — Regresión lineal y optimización mediante funciones de varias variables"
author:
  - "Integrantes: ____________________________________________"
  - "Docente: M.Sc. Alejandro Molina"
  - "Ingeniería de Software — Universidad Cooperativa de Colombia, San Juan de Pasto"
date: "2026B"
lang: es
toc-title: "Contenido"
---

# 1. Introducción y planteamiento del problema

Cuando se cuelga una masa de un resorte, este se estira. La **Ley de Hooke** afirma que, mientras el resorte no supere su límite elástico, la fuerza aplicada es proporcional al estiramiento:

$$F = k\,y$$

donde $k$ es la constante elástica del resorte. Si la fuerza es el peso de la masa colgada, $F = m g$, entonces

$$y = \frac{g}{k}\,m .$$

Es decir, la teoría predice que el estiramiento $y$ depende **linealmente** de la masa colgada. Por eso este experimento es un buen problema real para ajustar un modelo de la forma

$$y = a x + b ,$$

con $x$ la masa colgada (en gramos) y $y$ el estiramiento (en centímetros). La pendiente $a$ se relaciona con la constante del resorte ($a = g/k$) y el intercepto $b$ debería ser cercano a cero.

Los datos reales nunca caen exactamente sobre una recta. Para escoger la mejor recta se define el error cuadrático total

$$S(a,b) = \sum_{i=1}^{n} \left(y_i - a x_i - b\right)^2 ,$$

que es una **función de dos variables** ($a$ y $b$). Encontrar la mejor recta equivale a encontrar el punto $(a^*, b^*)$ donde $S$ es mínima: un problema de optimización de Cálculo Multivariable.

## 1.1 Pregunta central

> ¿Cómo se puede utilizar el Cálculo Multivariable para determinar y analizar el modelo lineal que mejor representa un conjunto de datos?

La respuesta se construye desde tres perspectivas: el análisis analítico (derivadas parciales, gradiente y Hessiano), la interpretación geométrica (superficie, trazas y curvas de nivel) y el análisis computacional (programa propio comparado con una biblioteca).

## 1.2 Objetivo general

Aplicar conceptos de Cálculo Multivariable para formular, resolver y analizar un problema de regresión lineal mediante la construcción y minimización de una función de error de dos variables, comparando los resultados obtenidos a mano con los obtenidos por computador.

## 1.3 Objetivos específicos

1. Medir el estiramiento de un resorte con distintas masas e identificar si la relación es aproximadamente lineal.
2. Formular la función de error cuadrático $S(a,b)$.
3. Calcular a mano las derivadas parciales de $S$.
4. Usar el gradiente para plantear la condición de punto crítico.
5. Resolver a mano el sistema de ecuaciones y obtener $a^*$ y $b^*$.
6. Calcular el Hessiano de $S$ y demostrar con él que el punto crítico es un mínimo.
7. Programar el procedimiento y compararlo con el cálculo manual y con una biblioteca.
8. Construir gráficas que muestren geométricamente la minimización.
9. Analizar la calidad del ajuste y las limitaciones del modelo lineal.

# 2. Montaje experimental y datos

## 2.1 Montaje

Se colgó un resorte de un soporte fijo y, al lado, se fijó una regla de madera. El soporte y la regla no se movieron durante todo el experimento; lo único que cambió fue el objeto colgado. Las lecturas se registraron con una resolución de 0,1 cm.

Para cada objeto se midió:

- su **masa** en gramos;
- su **largo** sin el resorte;
- la **lectura total** del conjunto resorte + objeto.

Con esas medidas se calculó:

- longitud del resorte bajo carga: $L = \text{lectura total} - \text{largo del objeto}$;
- estiramiento: $y = L - L_0$, con $L_0 = «m:L0»$ cm (longitud del resorte sin carga).

El resorte tiene una masa propia de 30 g. Esa masa no se cuenta como carga: en el primer dato la masa colgada es $x = 0$ g y el estiramiento es $y = 0$ cm por definición.

## 2.2 Tabla de datos

Variable independiente: $x$ = masa colgada (g). Variable dependiente: $y$ = estiramiento del resorte (cm).

«T_DATOS»

: Datos experimentales.

## 2.3 Fotografías

«FOTOS»

# 3. Exploración de los datos

![Diagrama de dispersión de los datos.](figuras/01_dispersion.png){width=14cm}

El diagrama de dispersión muestra que el estiramiento crece cuando crece la masa y que los puntos se agrupan alrededor de una línea recta, sin una curvatura clara. Por eso el modelo $y = ax + b$ es razonable para estos datos, y además es el que predice la Ley de Hooke.

También se ven dos detalles que se analizan más adelante: con las cargas más livianas (15 g y 70 g) el resorte casi no se estira, y el punto del parlante (220 g) queda por encima de la tendencia de sus vecinos.

# 4. Construcción del modelo

Se propone el modelo lineal

$$y = a x + b .$$

Para cada masa $x_i$ el modelo predice el estiramiento

$$y_{\text{pred},i} = a x_i + b ,$$

y la diferencia con el valor medido es el **residuo**

$$e_i = y_i - y_{\text{pred},i} = y_i - (a x_i + b) .$$

Como unos residuos son positivos y otros negativos, se suman sus cuadrados:

$$S(a,b) = \sum_{i=1}^{n} e_i^2 = \sum_{i=1}^{n} \left(y_i - a x_i - b\right)^2 .$$

Los datos $x_i$, $y_i$ son números fijos; las variables de $S$ son $a$ y $b$. Con los datos de este experimento ($n = «n»$) la función queda

$$S(a,b) = «m:Sxx»\,a^2 + «m:H12»\,ab + «n»\,b^2 - «m:2Sxy»\,a - «m:2Sy»\,b + «m:Syy» ,$$

un polinomio de segundo grado en $a$ y $b$ (un paraboloide).

# 5. Procedimiento analítico

Esta parte se hizo a mano. El desarrollo completo, operación por operación, está en el documento **Guía paso a paso a mano**; aquí se presenta el resumen.

## 5.1 Derivadas parciales

Se deriva cada término con la regla de la cadena:

$$\frac{\partial S}{\partial a} = \sum_{i=1}^{n} 2\,(y_i - a x_i - b)\,(-x_i) = -2\sum_{i=1}^{n} x_i\,(y_i - a x_i - b)$$

$$\frac{\partial S}{\partial b} = \sum_{i=1}^{n} 2\,(y_i - a x_i - b)\,(-1) = -2\sum_{i=1}^{n} (y_i - a x_i - b)$$

## 5.2 Condición de punto crítico

El punto crítico cumple $\nabla S(a,b) = \mathbf{0}$, es decir, las dos derivadas parciales valen cero. Al dividir entre $-2$ y separar las sumas se obtiene el sistema de **ecuaciones normales**:

$$\begin{aligned}
a\sum x_i^2 + b\sum x_i &= \sum x_i y_i \\
a\sum x_i + n\,b &= \sum y_i
\end{aligned}$$

## 5.3 Determinación de los parámetros

Las sumas de los datos son

$$n = «n», \qquad \sum x_i = «m:Sx», \qquad \sum y_i = «m:Sy», \qquad \sum x_i^2 = «m:Sxx», \qquad \sum x_i y_i = «m:Sxy» .$$

El sistema numérico es

$$\begin{aligned}
«m:Sxx»\,a + «m:Sx»\,b &= «m:Sxy» \\
«m:Sx»\,a + «n»\,b &= «m:Sy»
\end{aligned}$$

Al resolverlo:

$$a^* = \frac{n\sum x_i y_i - \sum x_i \sum y_i}{n\sum x_i^2 - \left(\sum x_i\right)^2} = \frac{«m:nSxy» - «m:SxSy»}{«m:nSxx» - «m:SxSx»} = \frac{«m:numA»}{«m:D»} = «m:a»\ \text{cm/g}$$

$$b^* = \frac{\sum y_i - a^*\sum x_i}{n} = \frac{«m:Sy» - «m:aSx»}{«n»} = «m:b»\ \text{cm}$$

La recta de mejor ajuste es

$$y = «m:a4»\,x - 0{,}070 \qquad (x \text{ en g},\ y \text{ en cm}),$$

y el error mínimo es $S(a^*, b^*) = «m:S»$ cm².

## 5.4 Análisis mediante el Hessiano

Las segundas derivadas son constantes:

$$S_{aa} = 2\sum x_i^2 = «m:H11», \qquad S_{bb} = 2n = «m:H22», \qquad S_{ab} = S_{ba} = 2\sum x_i = «m:H12» .$$

$$H = \begin{pmatrix} «m:H11» & «m:H12» \\ «m:H12» & «m:H22» \end{pmatrix}, \qquad \det H = («m:H11»)(«m:H22») - («m:H12»)^2 = «m:p1» - «m:p2» = «m:detH» .$$

Criterio de la segunda derivada: como $\det H = «m:detH» > 0$ y $S_{aa} = «m:H11» > 0$, el punto crítico $(a^*, b^*)$ es un **mínimo local**. Además, como el Hessiano es el mismo en todos los puntos y es definido positivo, $S$ es una función convexa: el mínimo es **único y global**.

Esto no depende de la suerte con los datos. En general $\det H = 4\left[n\sum x_i^2 - (\sum x_i)^2\right] = 4n\sum (x_i - \bar{x})^2$, que es positivo siempre que haya al menos dos masas distintas.

# 6. Interpretación geométrica

## 6.1 Superficie de error

![Superficie z = S(a,b). El punto rojo es el mínimo.](figuras/03_superficie.png){width=12cm}

La superficie $z = S(a,b)$ es un paraboloide elíptico que abre hacia arriba, con forma de valle. Se graficó para $0{,}005 \le a \le 0{,}025$ y $-2 \le b \le 2$, intervalo que contiene al mínimo. El punto más bajo del valle está en $(a^*, b^*) = («m:a4»;\ «m:b3»)$, con altura $S = «m:S2d»$ cm². En cualquier dirección en que uno se aleje de ese punto, el error sube.

## 6.2 Trazas y secciones transversales

![Secciones transversales de la superficie. El punto rojo es el mínimo global.](figuras/04_trazas.png){width=16cm}

Al cortar la superficie con un plano vertical se obtiene una curva de una sola variable:

- **Secciones con $b$ fijo** (izquierda): cada curva $S(a, b_0)$ es una parábola que abre hacia arriba. La traza con el plano $b = 0$ es $S(a,0) = «m:Sxx»\,a^2 - «m:2Sxy»\,a + «m:Syy»$, con vértice en $a = «m:av0»$ y $S = «m:Sav0»$. La sección con $b = b^*$ es la única que baja hasta el mínimo global.
- **Secciones con $a$ fijo** (derecha): cada curva $S(a_0, b)$ también es una parábola. La traza con el plano $a = 0$ es $S(0,b) = «n»\,b^2 - «m:2Sy»\,b + «m:Syy»$, con vértice en $b = «m:ym»$, que es justamente el promedio de los $y_i$: si se obliga a la recta a ser horizontal, la mejor es $y = \bar{y}$, y su error es $«m:ST»$ cm² (mucho mayor que «S2d»).

Las secciones muestran dos cosas. Primero, todas son parábolas hacia arriba, lo que confirma que $S$ tiene un solo mínimo. Segundo, el vértice de cada sección se desplaza cuando cambia el valor fijo: el mejor $a$ depende del $b$ escogido y viceversa. Por eso no se pueden optimizar $a$ y $b$ por separado y hace falta resolver el sistema de dos ecuaciones.

## 6.3 Curvas de nivel

![Curvas de nivel de S(a,b) con el mínimo señalado.](figuras/05_curvas_nivel.png){width=13cm}

Cada curva de nivel reúne todas las parejas $(a,b)$ que producen el mismo error $S$. Son elipses concéntricas cuyo centro es $(a^*, b^*)$: cuanto más pequeña es la elipse, menor es el error, y el punto obtenido a mano cae exactamente en el centro de la más pequeña.

Las elipses están inclinadas hacia abajo a la derecha. Eso significa que $a$ y $b$ se compensan: si se aumenta la pendiente, se puede bajar el intercepto y el error casi no cambia. Esa inclinación viene del término cruzado $«m:H12»\,ab$, es decir, de $S_{ab} \neq 0$.

## 6.4 Síntesis geométrica

La superficie muestra que existe un único punto más bajo; las secciones muestran que desde cualquier dirección se llega a él bajando por una parábola; y las curvas de nivel lo ubican en el plano $(a,b)$ como el centro de las elipses. Las tres representaciones señalan el mismo punto que se obtuvo con $\nabla S = \mathbf{0}$.

# 7. Verificación computacional

## 7.1 Programa

El programa `regresion_hooke.py` (Python) hace lo siguiente:

1. carga los datos;
2. calcula las sumas y, con las fórmulas deducidas en la sección 5, obtiene $a^*$ y $b^*$ **sin usar ninguna función de regresión**;
3. calcula $S(a^*, b^*)$, RMSE y $R^2$;
4. dibuja los datos con la recta óptima y con otras rectas de comparación;
5. construye la superficie, las secciones transversales y las curvas de nivel con el mínimo marcado;
6. calcula el Hessiano;
7. verifica numéricamente sus propiedades: determinante positivo, valores propios positivos y coincidencia con el Hessiano aproximado por diferencias finitas;
8. solo al final compara con `numpy.polyfit`.

## 7.2 Pseudocódigo

«PSEUDO»

## 7.3 Diagramas de flujo

![Diagrama de flujo general.](diagramas/diagrama_1_general.png){width=12.5cm}

![Diagrama de flujo del cálculo de las sumas.](diagramas/diagrama_2_sumas.png){width=12cm}

![Diagrama de flujo del cálculo del error y la calidad.](diagramas/diagrama_3_error.png){width=12cm}

## 7.4 Relación entre el código y el modelo

| Modelo matemático | Código |
|---|---|
| Sumas $\sum x_i$, $\sum y_i$, $\sum x_i^2$, $\sum x_i y_i$ | función `sumas` |
| Solución de $\nabla S = \mathbf{0}$ | función `ajustar` |
| $S(a,b) = \sum (y_i - a x_i - b)^2$ | función `error_S` |
| Hessiano $H$ | función `hessiano` |
| Residuos $e_i$ | función `residuos` |
| RMSE y $R^2$ | función `calidad` |

## 7.5 Verificación numérica del Hessiano

El programa obtuvo $\det H = «m:detH» > 0$ y los valores propios $\lambda_1 \approx «m:lam1»$ y $\lambda_2 \approx «m:lam2»$, ambos positivos, lo que confirma que $H$ es definido positivo. El Hessiano calculado por diferencias finitas coincidió con el analítico.

El valor propio grande corresponde a la dirección en la que el error crece muy rápido (cambiar la pendiente) y el pequeño a la dirección en la que crece despacio (el eje largo de las elipses).

## 7.6 Recta ajustada y otras rectas

![Datos, recta óptima y tres rectas de comparación.](figuras/02_recta_ajuste.png){width=14cm}

«T_OTRAS»

: Error de la recta óptima y de otras rectas.

Las rectas de prueba se parecen a la óptima, pero todas tienen un error mayor. Ninguna otra pareja $(a,b)$ puede dar un error menor que «S2d» cm², porque ese es el mínimo global de $S$.

# 8. Comparación entre el procedimiento analítico y el computacional

«T_COMP»

: Comparación de resultados.

Los tres métodos coinciden. El código propio y la biblioteca dan el mismo resultado hasta la precisión de la máquina. La pequeña diferencia de la columna manual se debe únicamente al redondeo: a mano se trabajó con 7 decimales en $a^*$ y con 4 decimales en los residuos, mientras que el computador usa unas 16 cifras. Esa diferencia es miles de veces menor que la resolución de la regla (0,1 cm), así que no tiene ningún efecto práctico.

# 9. Análisis de la recta de ajuste

La recta $y = «m:a4»\,x - 0{,}070$ representa bien la tendencia general: sube con los datos y deja puntos a ambos lados.

«T_RESIDUOS»

: Valores predichos y residuos.

- **Puntos con mayor desviación:** el «o1» («o1x» g), con un residuo de «o1e» cm; el «o2» («o2x» g), con «o2e» cm; y el «o3» («o3x» g), con «o3e» cm.
- **Punto alejado de la tendencia:** el parlante se estiró bastante más de lo que la recta predice. Es el candidato a dato atípico y su influencia se estudia en la sección 12.
- **Punto con más palanca:** el alicate (410 g) es la masa más alejada del resto, así que es el dato que más controla la pendiente de la recta.
- **Intercepto:** $b^* = «m:b3»$ cm es menor que la resolución de la regla, es decir, prácticamente cero, como predice la Ley de Hooke (sin carga no hay estiramiento).

# 10. Análisis de los residuos

![Residuos en función de la masa.](figuras/06_residuos.png){width=13cm}

![Histograma de los residuos.](figuras/07_histograma.png){width=10cm}

- **Centrados en cero:** sí. La suma de los residuos es cero (salvo redondeo), lo cual es consecuencia directa de la ecuación $\partial S/\partial b = 0$. Hay 5 residuos positivos y 5 negativos.
- **Tendencia o patrón:** los signos se alternan sin un orden claro a lo largo de $x$; no se ve una curva definida. Hay un indicio leve: en los dos extremos con mayor desviación (70 g y 410 g) el residuo es negativo, y en la zona media-alta (190 g a 300 g) es positivo. Con solo 10 datos no se puede afirmar que sea una desviación sistemática.
- **Dispersión:** no aumenta ni disminuye de forma ordenada con $x$. Los residuos grandes aparecen tanto en masas bajas (70 g) como altas (220 g y 410 g).
- **Valores atípicos:** el parlante («ep» cm) es el único residuo que se separa del grupo; en el histograma es la barra aislada a la derecha. Los otros nueve están entre −0,6 y +0,4 cm.
- **Regiones con desviación:** con las cargas livianas (15 g y 70 g) el resorte se estira menos de lo que indicaría la pendiente general. Es un comportamiento conocido de los resortes de espiras juntas: tienen una tensión inicial y necesitan una fuerza mínima antes de empezar a abrirse.

En conjunto, el comportamiento de los residuos es compatible con un modelo lineal: están centrados en cero y no muestran una estructura evidente. Las desviaciones se explican mejor por la forma de medir que por una falla del modelo.

# 11. Evaluación de la calidad del modelo

**Raíz del error cuadrático medio:**

$$\text{RMSE} = \sqrt{\frac{1}{n}\sum e_i^2} = \sqrt{\frac{«m:S»}{«n»}} = «m:RMSE2d»\ \text{cm}$$

El RMSE es el tamaño típico del error de la recta: en promedio, el estiramiento medido se aparta unos «RMSE2d» cm del predicho. Los estiramientos van de 0 a «rango» cm, así que ese error equivale al «rmsep» % del rango. También es unas cuatro veces la resolución de la regla (0,1 cm): la dispersión no viene de leer mal la regla, sino del método (objetos de formas muy distintas, punto de enganche, y un estiramiento que se obtiene restando dos longitudes).

**Coeficiente de determinación:**

$$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2} = 1 - \frac{«m:S»}{«m:ST»} = «m:R2»$$

El denominador («ST» cm²) es el error de la mejor recta horizontal $y = \bar{y}$, la misma traza $a = 0$ de la sección 6.2. $R^2$ dice entonces que usar la masa como variable explicativa elimina el «R2p» % de ese error: casi toda la variación del estiramiento se explica por la masa colgada.

**Relación con el propósito del modelo.** El propósito es comprobar la Ley de Hooke y estimar la constante del resorte. Para describir la tendencia y estimar $k$, el ajuste es adecuado. Para predecir el estiramiento de un objeto concreto la precisión es limitada: un error típico de «RMSE2d» cm es grande cuando el estiramiento es de 1 o 2 cm (cargas menores de 150 g), y pequeño frente a los 5 cm de las cargas mayores.

# 12. Análisis adicional: influencia de un dato (opción B)

Se retiró temporalmente el dato del parlante ($x = «xp»$ g, $y = «yp»$ cm), que tiene el residuo más grande, y se repitió todo el ajuste con los 9 datos restantes.

![Recta con los 10 datos y recta sin el parlante.](figuras/08_influencia.png){width=14cm}

«T_INFL»

: Efecto de retirar el dato del parlante.

- La pendiente cambia un «dap» % y el intercepto cambia «db» cm. La recta casi no se mueve.
- El error sí cambia mucho: $S$ baja de «S2d» a «S2» cm², porque ese solo punto aportaba casi la mitad del error total.
- La constante del resorte pasa de «k» a «k2» N/m.

Conclusión: el parlante es un dato **atípico pero poco influyente**. Empeora las medidas de calidad, pero no cambia de forma importante la recta, porque su masa (220 g) está cerca del centro de los datos. Un punto igual de desviado en un extremo, como el alicate, habría girado la recta mucho más. Por eso se decidió conservar el dato: fue medido igual que los demás y no hay una razón experimental para descartarlo.

# 13. Interpretación física: constante del resorte

La pendiente relaciona estiramiento y masa: $a^* = g/k$. Pasando a unidades del Sistema Internacional:

$$a^* = «m:a»\ \frac{\text{cm}}{\text{g}} = «m:a10»\ \frac{\text{m}}{\text{kg}} \qquad\Longrightarrow\qquad k = \frac{g}{a^*} = \frac{9{,}8\ \text{m/s}^2}{«m:a10»\ \text{m/kg}} \approx «m:k»\ \text{N/m}$$

Es decir, hacen falta unos «k» N (el peso de unos 6,6 kg) para estirar este resorte un metro, o de forma más práctica: **cada 100 g colgados lo estiran aproximadamente 1,5 cm**.

# 14. Conclusiones

1. **Respuesta a la pregunta central.** El Cálculo Multivariable convierte el problema de "encontrar la mejor recta" en el de minimizar una función de dos variables, $S(a,b)$. Las derivadas parciales y la condición $\nabla S = \mathbf{0}$ producen un sistema de dos ecuaciones cuya solución es la recta; el Hessiano demuestra que esa solución es un mínimo; y la superficie, las secciones y las curvas de nivel permiten verlo.
2. **Resultado.** Para el resorte estudiado la mejor recta es $y = «m:a4»\,x - 0{,}070$ (cm, con $x$ en g), con error mínimo $S = «m:S2d»$ cm².
3. **El mínimo es único.** $\det H = «m:detH» > 0$ y $S_{aa} > 0$; como el Hessiano es constante, $S$ es convexa y no existe otra recta mejor. Las curvas de nivel elípticas y las secciones parabólicas muestran lo mismo.
4. **Los tres métodos coinciden.** El cálculo a mano, el código propio y `numpy.polyfit` dan los mismos parámetros; la única diferencia es el redondeo del cálculo manual. El computador verificó el resultado, no lo reemplazó.
5. **La Ley de Hooke se cumple razonablemente.** $R^2 = «m:R2»$, el intercepto es prácticamente cero y los residuos no muestran un patrón claro. La constante estimada es $k \approx «m:k»$ N/m.
6. **Las curvas de nivel enseñan algo que la recta no muestra.** La inclinación de las elipses indica que pendiente e intercepto se compensan: los datos determinan mejor la combinación de ambos que cada uno por separado.
7. **Un dato atípico no siempre es influyente.** Retirar el parlante reduce el error a menos de la mitad, pero cambia la pendiente menos del 3 %.

## 14.1 Reflexión crítica y limitaciones

- **Pocos datos.** Con 10 puntos no se puede distinguir una curvatura leve del ruido de medición.
- **Una sola lectura por objeto.** No hay repeticiones, así que no se puede estimar la incertidumbre de cada punto ni poner barras de error.
- **Método indirecto.** El estiramiento se obtuvo restando el largo del objeto a la lectura total. Los objetos tienen formas muy distintas y no todos cuelgan del mismo punto, lo que explica una dispersión (0,43 cm) mayor que la resolución de la regla (0,1 cm).
- **Tensión inicial del resorte.** Con cargas livianas el resorte casi no se estira. El modelo lineal no describe bien esa zona; un modelo más fiel usaría solo las cargas que superan esa tensión inicial.
- **Rango de validez.** La recta solo vale entre 0 y 410 g. No se debe extrapolar: con más carga el resorte puede superar su límite elástico y deformarse de forma permanente.
- **Registro fotográfico incompleto.** Cuatro de las cargas se documentan con imágenes ilustrativas y no con fotografías de la medición.

## 14.2 Recomendaciones

Usar pesas de masa conocida con un mismo gancho, medir directamente la posición del extremo inferior del resorte, repetir cada lectura dos o tres veces, fotografiar todas las cargas y agregar más masas entre 0 y 100 g para estudiar la zona de tensión inicial.

# Referencias

- Harris, C. R., Millman, K. J., van der Walt, S. J., et al. (2020). Array programming with NumPy. *Nature*, 585, 357–362.
- Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90–95.
- Molina, A. (2026). *Proyecto de Cálculo Multivariable: Regresión lineal y optimización mediante funciones de varias variables*. Universidad Cooperativa de Colombia.
- Serway, R. A., y Jewett, J. W. (2018). *Física para ciencias e ingeniería* (10.ª ed.). Cengage Learning.
- Stewart, J. (2018). *Cálculo de varias variables: Trascendentes tempranas* (8.ª ed.). Cengage Learning.
"""

# ------------------------------------------------------------------ guia
GUIA = r"""---
title: "Guía paso a paso a mano"
subtitle: "Ley de Hooke — Regresión lineal por mínimos cuadrados con Cálculo Multivariable"
date: "Proyecto final de Cálculo Multivariable, 2026B"
lang: es
toc-title: "Contenido"
---

# Cómo usar esta guía

Esta guía contiene **todas** las operaciones del procedimiento analítico, en el orden en que deben hacerse en el cuaderno. No se salta ningún paso ni se da por conocido ningún resultado. Cada integrante debería poder repetirla con una calculadora sencilla.

Reglas de redondeo usadas (para que a todos les dé lo mismo):

- las sumas se dejan exactas;
- $a^*$ y $b^*$ se redondean a 7 decimales;
- los valores predichos $\hat{y}_i$ y los residuos $e_i$ se redondean a 4 decimales;
- los resultados finales se reportan con 2 a 4 decimales.

Material: calculadora, la tabla de datos y papel.

# Paso 0. De las mediciones al estiramiento

La longitud del resorte sin carga es $L_0 = «m:L0»$ cm. Para cada objeto:

$$L = \text{lectura total} - \text{largo del objeto}, \qquad y = L - L_0 .$$

«T_RESTAS»

La variable $x$ es la masa colgada en gramos. Para el resorte sin carga, $x = 0$ (los 30 g de masa propia del resorte no son carga colgada).

**Datos finales** $(x_i, y_i)$:

(0; 0,0), (15; 0,1), (70; 0,4), (92; 1,6), (150; 1,9), (185; 2,5), (190; 2,9), (220; 4,2), (300; 4,8), (410; 5,6).

# Paso 1. Escribir la función de error

Modelo: $y = ax + b$. Residuo de cada dato: $e_i = y_i - a x_i - b$. Función de error:

$$S(a,b) = \sum_{i=1}^{10} (y_i - a x_i - b)^2$$

Escrita término por término con los datos:

$$\begin{aligned}
S(a,b) ={} & (0 - 0a - b)^2 + (0{,}1 - 15a - b)^2 + (0{,}4 - 70a - b)^2 + (1{,}6 - 92a - b)^2 \\
& + (1{,}9 - 150a - b)^2 + (2{,}5 - 185a - b)^2 + (2{,}9 - 190a - b)^2 \\
& + (4{,}2 - 220a - b)^2 + (4{,}8 - 300a - b)^2 + (5{,}6 - 410a - b)^2
\end{aligned}$$

Las incógnitas son $a$ y $b$. Los $x_i$ y $y_i$ son números.

# Paso 2. Derivadas parciales

## 2.1 Derivada de un solo término

Tomar un término cualquiera: $u_i^2$, con $u_i = y_i - a x_i - b$.

Regla de la cadena: $\dfrac{\partial}{\partial a}\left(u_i^2\right) = 2 u_i \cdot \dfrac{\partial u_i}{\partial a}$.

**Respecto de $a$** ($b$, $x_i$, $y_i$ se tratan como constantes):

$$\frac{\partial u_i}{\partial a} = \frac{\partial}{\partial a}(y_i) - \frac{\partial}{\partial a}(a x_i) - \frac{\partial}{\partial a}(b) = 0 - x_i - 0 = -x_i$$

$$\frac{\partial}{\partial a}\left(u_i^2\right) = 2\,(y_i - a x_i - b)\,(-x_i) = -2 x_i\,(y_i - a x_i - b)$$

**Respecto de $b$** ($a$, $x_i$, $y_i$ se tratan como constantes):

$$\frac{\partial u_i}{\partial b} = 0 - 0 - 1 = -1$$

$$\frac{\partial}{\partial b}\left(u_i^2\right) = 2\,(y_i - a x_i - b)\,(-1) = -2\,(y_i - a x_i - b)$$

## 2.2 Derivada de la suma

La derivada de una suma es la suma de las derivadas:

$$\frac{\partial S}{\partial a} = -2\sum_{i=1}^{n} x_i\,(y_i - a x_i - b)$$

$$\frac{\partial S}{\partial b} = -2\sum_{i=1}^{n} (y_i - a x_i - b)$$

## 2.3 Repartir las sumas

Multiplicar dentro del paréntesis y separar ($a$ y $b$ salen de la suma porque no dependen de $i$; además $\sum_{i=1}^{n} b = nb$):

$$\frac{\partial S}{\partial a} = -2\sum (x_i y_i - a x_i^2 - b x_i) = -2\left[\sum x_i y_i - a\sum x_i^2 - b\sum x_i\right]$$

$$\frac{\partial S}{\partial b} = -2\left[\sum y_i - a\sum x_i - n b\right]$$

# Paso 3. Gradiente igual a cero

El gradiente es $\nabla S = \left(\dfrac{\partial S}{\partial a},\ \dfrac{\partial S}{\partial b}\right)$. En el punto crítico $\nabla S = (0, 0)$:

$$-2\left[\sum x_i y_i - a\sum x_i^2 - b\sum x_i\right] = 0$$

$$-2\left[\sum y_i - a\sum x_i - n b\right] = 0$$

Dividir cada ecuación entre $-2$:

$$\sum x_i y_i - a\sum x_i^2 - b\sum x_i = 0$$

$$\sum y_i - a\sum x_i - n b = 0$$

Pasar al otro lado los términos con $a$ y $b$. Resultado, las **ecuaciones normales**:

$$\begin{aligned}
\text{(E1)}\qquad a\sum x_i^2 + b\sum x_i &= \sum x_i y_i \\
\text{(E2)}\qquad a\sum x_i + n\,b &= \sum y_i
\end{aligned}$$

# Paso 4. Tabla auxiliar de sumas

Calcular para cada dato $x_i^2$, $x_i y_i$ y $y_i^2$ (este último se usa en los pasos 8 y 9):

«T_SUMAS»

Sumas, columna por columna:

- $\sum x_i$ = «CH_X» = **«Sx»**
- $\sum y_i$ = «CH_Y» = **«Sy»**
- $\sum x_i^2$ = «CH_XX» = **«Sxx»**
- $\sum x_i y_i$ = «CH_XY» = **«Sxy»**
- $\sum y_i^2$ = «CH_YY» = **«Syy»**
- $n$ = **«n»**

# Paso 5. Resolver el sistema

Reemplazar las sumas en (E1) y (E2):

$$\begin{aligned}
\text{(E1)}\qquad «m:Sxx»\,a + «m:Sx»\,b &= «m:Sxy» \\
\text{(E2)}\qquad «m:Sx»\,a + «n»\,b &= «m:Sy»
\end{aligned}$$

## 5.1 Método de eliminación

Se quiere eliminar $b$. En (E1) el coeficiente de $b$ es «Sx» y en (E2) es «n». Multiplicar (E2) por $«m:Sx» \div «n» = «m:fac»$:

- $«m:fac» \times «m:Sx» = «m:e2a»$
- $«m:fac» \times «n» = «m:Sx»$
- $«m:fac» \times «m:Sy» = «m:e2c»$

$$\text{(E2')}\qquad «m:e2a»\,a + «m:Sx»\,b = «m:e2c»$$

Restar (E1) − (E2'):

- coeficiente de $a$: $«m:Sxx» - «m:e2a» = «m:da»$
- coeficiente de $b$: $«m:Sx» - «m:Sx» = 0$
- lado derecho: $«m:Sxy» - «m:e2c» = «m:dc»$

$$«m:da»\,a = «m:dc» \qquad\Longrightarrow\qquad a^* = \frac{«m:dc»}{«m:da»} = «m:a»$$

Despejar $b$ de (E2): $«n»\,b = «m:Sy» - «m:Sx»\,a$.

- $«m:Sx» \times «m:a» = «m:aSx»$
- $«m:Sy» - «m:aSx» = «m:SyaSx»$
- $b^* = «m:SyaSx» \div «n» = «m:b»$

## 5.2 Comprobación con la fórmula general (regla de Cramer)

$$a^* = \frac{n\sum x_i y_i - \sum x_i\sum y_i}{n\sum x_i^2 - \left(\sum x_i\right)^2}$$

- $n\sum x_i y_i = «n» \times «m:Sxy» = «m:nSxy»$
- $\sum x_i \sum y_i = «m:Sx» \times «m:Sy» = «m:SxSy»$
- numerador: $«m:nSxy» - «m:SxSy» = «m:numA»$
- $n\sum x_i^2 = «n» \times «m:Sxx» = «m:nSxx»$
- $\left(\sum x_i\right)^2 = «m:Sx» \times «m:Sx» = «m:SxSx»$
- denominador: $«m:nSxx» - «m:SxSx» = «m:D»$

$$a^* = \frac{«m:numA»}{«m:D»} = «m:a» \quad\checkmark$$

$$b^* = \frac{\sum y_i - a^*\sum x_i}{n} = \frac{«m:Sy» - «m:aSx»}{«n»} = «m:b» \quad\checkmark$$

## 5.3 Comprobación reemplazando en el sistema

- (E1): $«m:Sxx» \times «m:a» + «m:Sx» \times («m:b») = «m:chk1a» + («m:chk1b») = «m:chk1»$. Debe dar «Sxy». ✓
- (E2): $«m:Sx» \times «m:a» + «n» \times («m:b») = «m:aSx» + («m:chk2b») = «m:chk2»$. Debe dar «Sy». ✓

(Las diferencias en los últimos decimales se deben al redondeo de $a^*$ y $b^*$.)

## 5.4 Resultado

$$a^* = «m:a»\ \text{cm/g}, \qquad b^* = «m:b»\ \text{cm}, \qquad \boxed{y = «m:a4»\,x - 0{,}070}$$

# Paso 6. Hessiano y prueba de que es un mínimo

## 6.1 Segundas derivadas

Partir de las primeras derivadas del paso 2.3:

$$\frac{\partial S}{\partial a} = -2\sum x_i y_i + 2a\sum x_i^2 + 2b\sum x_i \qquad\qquad \frac{\partial S}{\partial b} = -2\sum y_i + 2a\sum x_i + 2nb$$

Derivar otra vez:

- $S_{aa} = \dfrac{\partial}{\partial a}\left(\dfrac{\partial S}{\partial a}\right) = 0 + 2\sum x_i^2 + 0 = 2 \times «m:Sxx» = «m:H11»$
- $S_{ab} = \dfrac{\partial}{\partial b}\left(\dfrac{\partial S}{\partial a}\right) = 0 + 0 + 2\sum x_i = 2 \times «m:Sx» = «m:H12»$
- $S_{ba} = \dfrac{\partial}{\partial a}\left(\dfrac{\partial S}{\partial b}\right) = 0 + 2\sum x_i + 0 = «m:H12»$ (igual a $S_{ab}$, como debe ser)
- $S_{bb} = \dfrac{\partial}{\partial b}\left(\dfrac{\partial S}{\partial b}\right) = 0 + 0 + 2n = 2 \times «n» = «m:H22»$

## 6.2 Matriz Hessiana y determinante

$$H = \begin{pmatrix} S_{aa} & S_{ab} \\ S_{ba} & S_{bb} \end{pmatrix} = \begin{pmatrix} «m:H11» & «m:H12» \\ «m:H12» & «m:H22» \end{pmatrix}$$

$$\det H = S_{aa} S_{bb} - (S_{ab})^2$$

- $«m:H11» \times «m:H22» = «m:p1»$
- $«m:H12» \times «m:H12» = «m:p2»$
- $\det H = «m:p1» - «m:p2» = «m:detH»$

## 6.3 Criterio de la segunda derivada

| Condición | Conclusión |
|---|---|
| $\det H > 0$ y $S_{aa} > 0$ | mínimo local |
| $\det H > 0$ y $S_{aa} < 0$ | máximo local |
| $\det H < 0$ | punto de silla |
| $\det H = 0$ | el criterio no decide |

Aquí $\det H = «m:detH» > 0$ y $S_{aa} = «m:H11» > 0$, por lo tanto **$(a^*, b^*)$ es un mínimo**.

Como $H$ no depende de $a$ ni de $b$ (todas las segundas derivadas son constantes), la función es convexa en todo el plano y el mínimo es único y global.

## 6.4 Comprobación opcional con valores propios

Los valores propios cumplen $\lambda^2 - (\text{traza})\,\lambda + \det H = 0$.

- traza $= «m:H11» + «m:H22» = «m:traza»$
- ecuación: $\lambda^2 - «m:traza»\,\lambda + «m:detH» = 0$
- discriminante: $«m:traza»^2 - 4 \times «m:detH» = «m:traza2» - «m:detH4» = «m:disc»$
- raíz del discriminante: $\sqrt{«m:disc»} = «m:rdisc»$
- $\lambda_1 = \dfrac{«m:traza» + «m:rdisc»}{2} = «m:lam1»$
- $\lambda_2 = \dfrac{«m:traza» - «m:rdisc»}{2} = «m:lam2»$

Los dos son positivos: $H$ es definida positiva. ✓

## 6.5 Por qué siempre da un mínimo

$$\det H = 4n\sum x_i^2 - 4\left(\sum x_i\right)^2 = 4\left[n\sum x_i^2 - \left(\sum x_i\right)^2\right] = 4 \times «m:D» = «m:detH»$$

La expresión entre corchetes es igual a $n\sum (x_i - \bar{x})^2$, una suma de cuadrados: solo vale cero si todas las masas son iguales.

# Paso 7. Error mínimo $S(a^*, b^*)$

Para cada dato: valor predicho $\hat{y}_i = a^* x_i + b^*$, residuo $e_i = y_i - \hat{y}_i$ y su cuadrado.

«T_RES_MANO»

$$S(a^*, b^*) = \sum e_i^2 = «m:S»\ \text{cm}^2$$

**Comprobación 1.** La suma de los residuos debe ser cero (es la ecuación E2). Da «sume», que es cero salvo redondeo. ✓

**Comprobación 2.** En el mínimo se cumple $S = \sum y_i^2 - a^*\sum x_i y_i - b^*\sum y_i$:

- $a^* \sum x_i y_i = «m:a» \times «m:Sxy» = «m:aSxy»$
- $b^* \sum y_i = («m:b») \times «m:Sy» = «m:bSy»$
- $S = «m:Syy» - «m:aSxy» - («m:bSy») = «m:Salt»$ ✓ (coincide salvo redondeo)

# Paso 8. Medidas de calidad

## 8.1 RMSE

$$\text{RMSE} = \sqrt{\frac{S}{n}}$$

- $S \div n = «m:S» \div «n» = «m:Sn»$
- $\sqrt{«m:Sn»} = «m:RMSE»$ cm

## 8.2 Coeficiente de determinación $R^2$

Promedio: $\bar{y} = \dfrac{\sum y_i}{n} = \dfrac{«m:Sy»}{«n»} = «m:ym»$ cm.

«T_ST»

$$S_T = \sum (y_i - \bar{y})^2 = «m:ST»$$

Atajo para comprobar: $S_T = \sum y_i^2 - n\bar{y}^2 = «m:Syy» - «n» \times «m:ym2» = «m:Syy» - «m:nym2» = «m:ST»$ ✓

$$R^2 = 1 - \frac{S}{S_T} = 1 - \frac{«m:S»}{«m:ST»} = 1 - «m:SST» = «m:R2»$$

# Paso 9. Trazas y curvas de nivel a mano

## 9.1 Forma desarrollada de $S$

Desarrollar el cuadrado de un término:

$$(y_i - a x_i - b)^2 = y_i^2 + a^2 x_i^2 + b^2 - 2a x_i y_i - 2b y_i + 2ab x_i$$

Sumar sobre todos los datos:

$$S(a,b) = a^2\sum x_i^2 + 2ab\sum x_i + n b^2 - 2a\sum x_i y_i - 2b\sum y_i + \sum y_i^2$$

Con los números (usando $2 \times «m:Sx» = «m:H12»$, $2 \times «m:Sxy» = «m:2Sxy»$, $2 \times «m:Sy» = «m:2Sy»$):

$$S(a,b) = «m:Sxx»\,a^2 + «m:H12»\,ab + «n»\,b^2 - «m:2Sxy»\,a - «m:2Sy»\,b + «m:Syy»$$

## 9.2 Traza con el plano $b = 0$

Poner $b = 0$: $S(a, 0) = «m:Sxx»\,a^2 - «m:2Sxy»\,a + «m:Syy»$.

Es una parábola que abre hacia arriba. Su vértice está en

$$a = \frac{«m:2Sxy»}{2 \times «m:Sxx»} = \frac{«m:2Sxy»}{«m:2Sxxd»} = «m:av0», \qquad S = «m:Sav0» .$$

## 9.3 Traza con el plano $a = 0$

Poner $a = 0$: $S(0, b) = «n»\,b^2 - «m:2Sy»\,b + «m:Syy»$.

Vértice en $b = \dfrac{«m:2Sy»}{2 \times «n»} = «m:ym»$ (el promedio $\bar{y}$), con $S = «n» \times «m:ym2» - «m:2Sy» \times «m:ym» + «m:Syy» = «m:ST»$.

## 9.4 Curvas de nivel

Una curva de nivel es $S(a,b) = c$ con $c$ constante:

$$«m:Sxx»\,a^2 + «m:H12»\,ab + «n»\,b^2 - «m:2Sxy»\,a - «m:2Sy»\,b + «m:Syy» = c$$

Es una cónica. Para clasificarla se calcula $B^2 - 4AC$ con $A = «m:Sxx»$, $B = «m:H12»$, $C = «n»$:

$$B^2 - 4AC = «m:p2» - «m:nSxx4» = «m:conica» < 0 \quad\Longrightarrow\quad \text{elipse}$$

Para $c > «m:S2d»$ son elipses con centro en $(a^*, b^*)$; para $c = S_{\min}$ la elipse se reduce a ese punto; para $c$ menor no hay curva (el error no puede ser menor que el mínimo).

# Paso 10. Constante del resorte

Ley de Hooke con el peso como fuerza: $k\,y = m\,g$, entonces $y = \dfrac{g}{k}\,m$ y la pendiente es $a^* = \dfrac{g}{k}$.

Convertir unidades: $1\ \text{cm} = 0{,}01\ \text{m}$ y $1\ \text{g} = 0{,}001\ \text{kg}$.

$$a^* = «m:a»\ \frac{\text{cm}}{\text{g}} = «m:a» \times \frac{0{,}01\ \text{m}}{0{,}001\ \text{kg}} = «m:a» \times 10\ \frac{\text{m}}{\text{kg}} = «m:a10»\ \frac{\text{m}}{\text{kg}}$$

$$k = \frac{g}{a^*} = \frac{9{,}8}{«m:a10»} = «m:k»\ \text{N/m}$$

(Unidades: $\dfrac{\text{m/s}^2}{\text{m/kg}} = \dfrac{\text{kg}}{\text{s}^2} = \dfrac{\text{N}}{\text{m}}$.)

# Paso 11. Análisis adicional: quitar el dato del parlante

Se retira el punto $(«m:xp»;\ «m:yp»)$ y se repiten los pasos 4 y 5 con 9 datos. No hace falta rehacer la tabla: basta restar a cada suma lo que aportaba ese punto.

«T_SUMAS2»

- $n\sum x_i y_i = «n2» \times «m:Sxy2» = «m:nSxy2»$
- $\sum x_i\sum y_i = «m:Sx2» \times «m:Sy2» = «m:SxSy2»$
- numerador: $«m:nSxy2» - «m:SxSy2» = «m:numA2»$
- $n\sum x_i^2 = «n2» \times «m:Sxx2» = «m:nSxx2»$
- $\left(\sum x_i\right)^2 = «m:Sx2» \times «m:Sx2» = «m:SxSx2»$
- denominador: $«m:nSxx2» - «m:SxSx2» = «m:D2»$

$$a^* = \frac{«m:numA2»}{«m:D2»} = «m:a2»$$

- $«m:Sx2» \times «m:a2» = «m:aSx2»$
- $«m:Sy2» - «m:aSx2» = «m:SyaSx2»$
- $b^* = «m:SyaSx2» \div «n2» = «m:b2»$

Recta sin el parlante: $y = «m:a24»\,x - «m:b23abs»$. La pendiente cambió un «dap» %.

# Resumen de resultados

| Cantidad | Valor |
|---|---|
| $\sum x_i$, $\sum y_i$ | «Sx»; «Sy» |
| $\sum x_i^2$, $\sum x_i y_i$, $\sum y_i^2$ | «Sxx»; «Sxy»; «Syy» |
| $a^*$ | «a» cm/g |
| $b^*$ | «b» cm |
| Hessiano | [[«H11», «H12»], [«H12», «H22»]] |
| $\det H$ | «detH» (positivo) |
| $S(a^*, b^*)$ | «S» cm² |
| RMSE | «RMSE» cm |
| $R^2$ | «R2» |
| $k$ | «k» N/m |
"""

V.update({
    "CH_X": cadena(X), "CH_Y": cadena(Y, 1), "CH_XX": cadena([x * x for x in X]),
    "CH_XY": cadena([x * y for x, y in zip(X, Y)]), "CH_YY": cadena([y * y for y in Y]),
    "nSxx4": 4 * Sxx * n, "conica": (2 * Sx) ** 2 - 4 * Sxx * n, "b23abs": c(-b2, 3),
    "T_DATOS": T_DATOS, "T_RESTAS": T_RESTAS, "T_SUMAS": T_SUMAS, "T_RES_MANO": T_RES_MANO, "T_ST": T_ST,
    "T_RESIDUOS": T_RESIDUOS, "T_COMP": T_COMP, "T_OTRAS": T_OTRAS, "T_INFL": T_INFL, "T_SUMAS2": T_SUMAS2,
    "FOTOS": FOTOS, "PSEUDO": PSEUDO,
})


def bordes(ruta):
    """Pone bordes a todas las tablas (el estilo por defecto de pandoc no los trae)."""
    d = docx.Document(ruta)
    for t in d.tables:
        pr = t._tbl.tblPr
        b = OxmlElement("w:tblBorders")
        for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{lado}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:color"), "808080")
            b.append(el)
        pr.append(b)
    d.save(ruta)


def construir(md, nombre):
    texto = llenar(llenar(md))  # dos pasadas: las tablas insertadas tambien traen marcas
    faltan = re.findall(r"«[^»]*»", texto)
    assert not faltan, f"Marcas sin reemplazar: {faltan}"
    salida = RAIZ / nombre
    pypandoc.convert_text(texto, "docx", format="markdown", outputfile=str(salida),
                          extra_args=[f"--resource-path={RAIZ}", "--toc", "--toc-depth=2"])
    bordes(salida)
    print("Generado:", salida)


if __name__ == "__main__":
    # El calculo "a mano" (redondeado) debe coincidir con el codigo dentro del redondeo
    assert abs(a - a_cod) < 1e-7 and abs(b - b_cod) < 1e-4 and abs(S - S_cod) < 1e-3
    construir(INFORME, "Ley_de_Hooke_Completado.docx")
    construir(GUIA, "Guia_paso_a_paso_a_mano.docx")

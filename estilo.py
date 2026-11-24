"""Estilo comun del proyecto: misma letra (Fira Sans) y mismos colores en graficas,
diagramas, informes Word y presentacion.

Los colores son los de la presentacion (presentacion/presentacion_hooke.tex) y los
de los documentos Word (generar_documentos.py).
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

FUENTES = Path(__file__).parent / "fuentes"

# Paleta
AZUL = "#1F4E79"
AZUL_CLARO = "#E8EEF5"
NARANJA = "#E07A1F"
NARANJA_CLARO = "#FCEBDD"
VERDE = "#2E8B57"
VERDE_CLARO = "#E3F1E9"
ROJO = "#C0392B"
ROJO_CLARO = "#F8E1DE"
GRIS = "#6B7280"
MORADO = "#7B4FA0"
TEXTO = "#262626"

for f in sorted(FUENTES.glob("FiraSans-*.ttf")):
    font_manager.fontManager.addfont(str(f))

plt.rcParams.update({
    # Fira Sans y, para simbolos que no tiene (√, ≈, →, subindices), DejaVu Sans
    "font.family": ["Fira Sans", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlecolor": AZUL,
    "axes.labelsize": 11, "axes.labelcolor": TEXTO, "text.color": TEXTO,
    "xtick.color": TEXTO, "ytick.color": TEXTO, "axes.edgecolor": "#9CA3AF",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
    "legend.frameon": False,
    "axes.prop_cycle": plt.cycler(color=[AZUL, NARANJA, VERDE, ROJO, MORADO, GRIS]),
    "savefig.dpi": 200, "figure.dpi": 100,
})


def comas(fig):
    """Escribe los decimales con coma (como en el informe y la presentacion) en ejes, leyendas y textos."""
    import re

    from matplotlib.ticker import FixedLocator

    patron = re.compile(r"(?<=\d)\.(?=\d)")
    fig.canvas.draw()
    for ax in fig.axes:
        ejes = [ax.xaxis, ax.yaxis] + ([ax.zaxis] if hasattr(ax, "zaxis") else [])
        for eje in ejes:
            etiquetas = eje.get_ticklabels()
            if any(patron.search(t.get_text()) for t in etiquetas):
                eje.set_major_locator(FixedLocator(eje.get_ticklocs()))
                eje.set_ticklabels([patron.sub(",", t.get_text()) for t in etiquetas])
        textos = list(ax.texts) + ([ax.title] if ax.get_title() else [])
        if ax.get_legend():
            textos += ax.get_legend().get_texts()
        for t in textos:
            t.set_text(patron.sub(",", t.get_text()))

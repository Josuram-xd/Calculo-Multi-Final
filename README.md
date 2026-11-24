# Proyecto final de Cálculo Multivariable: Ley de Hooke

Regresión lineal por mínimos cuadrados del estiramiento de un resorte en función de la masa colgada.

- `Ley_de_Hooke_Completado.docx`: informe final.
- `Guia_paso_a_paso_a_mano.docx`: procedimiento manual completo, operación por operación.
- `regresion_hooke.py`: programa de ajuste (fórmulas propias, Hessiano, comparación con `numpy.polyfit`) y gráficas en `figuras/`. Incluye el análisis de las recomendaciones del docente: intervalos de confianza y sensibilidad de `k`, regresión polinómica (grados 1 a 4), RMSE en unidades del fenómeno y errores de la regla y la gramera.
- `presentacion/presentacion_hooke.pdf`: diapositivas (Beamer), con poco texto.
- `presentacion/presentacion_hooke_notas.pdf`: las mismas diapositivas con el guion de quien expone debajo (las explicaciones van en `\note{}`).
- Fuente de las diapositivas: `presentacion_hooke.tex`; `presentacion/valores.tex` lo genera `regresion_hooke.py`.
- `diagramas.py`: diagramas de flujo del pseudocódigo en `diagramas/`.
- `estilo.py` y `estilo_word.py`: letra (Fira Sans, en `fuentes/`, licencia OFL) y colores comunes a gráficas, diagramas, informes Word y presentación. La letra va incrustada en los .docx para que se vea igual en cualquier computador.
- `generar_documentos.py`: reconstruye los dos documentos Word a partir de los datos.

## Cómo regenerar todo

```
pip install -r requirements.txt python-docx
python regresion_hooke.py
python diagramas.py
python generar_documentos.py
cd presentacion && latexmk -pdf presentacion_hooke.tex presentacion_hooke_notas.tex
```

La presentación necesita LaTeX con Beamer y el tema `metropolis` (en Debian/Ubuntu: `texlive-latex-extra texlive-fonts-extra texlive-lang-spanish`).

Supuesto: la gramera tiene resolución de 1 g (`RES_GRAMERA` en `regresion_hooke.py`); si era otra, se cambia ahí y se regenera todo.

Si cambian los datos, se editan en `regresion_hooke.py` (`X`, `Y`) y en `generar_documentos.py` (`LARGO_OBJETO`, `LECTURA_TOTAL`).

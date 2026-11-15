# Proyecto final de Cálculo Multivariable: Ley de Hooke

Regresión lineal por mínimos cuadrados del estiramiento de un resorte en función de la masa colgada.

- `Ley_de_Hooke_Completado.docx`: informe final.
- `Guia_paso_a_paso_a_mano.docx`: procedimiento manual completo, operación por operación.
- `regresion_hooke.py`: programa de ajuste (fórmulas propias, Hessiano, comparación con `numpy.polyfit`) y gráficas en `figuras/`.
- `diagramas.py`: diagramas de flujo del pseudocódigo en `diagramas/`.
- `generar_documentos.py`: reconstruye los dos documentos Word a partir de los datos.

## Cómo regenerar todo

```
pip install -r requirements.txt python-docx
python regresion_hooke.py
python diagramas.py
python generar_documentos.py
```

Si cambian los datos, se editan en `regresion_hooke.py` (`X`, `Y`) y en `generar_documentos.py` (`LARGO_OBJETO`, `LECTURA_TOTAL`).

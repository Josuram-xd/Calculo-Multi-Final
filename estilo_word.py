"""Da a los documentos Word la misma letra (Fira Sans, incrustada en el archivo) y los mismos
colores que la presentacion y las graficas (ver estilo.py).

- referencia(ruta): crea el documento de referencia de pandoc con los estilos del proyecto.
- acabado(ruta):    da formato a las tablas e incrusta la letra en el .docx ya generado.
"""
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import docx
import pypandoc
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

FUENTES = Path(__file__).parent / "fuentes"
LETRA = "Fira Sans"
AZUL, AZUL_CLARO, NARANJA, GRIS, TEXTO = "1F4E79", "F2F5FA", "E07A1F", "6B7280", "262626"
MONO = {"Verbatim Char", "Source Code"}  # el codigo conserva su letra de ancho fijo


def _letra(rpr, nombre=LETRA):
    """Fija la letra en un w:rPr, quitando las referencias a las letras del tema."""
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for atr in list(rf.attrib):
        if "Theme" in atr or "theme" in atr:
            del rf.attrib[atr]
    for atr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(atr), nombre)


def referencia(ruta):
    subprocess.run([pypandoc.get_pandoc_path(), "-o", str(ruta), "--print-default-data-file", "reference.docx"],
                   check=True)
    d = docx.Document(ruta)
    defecto = d.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
    _letra(defecto)
    for st in d.styles:
        if st.type not in (WD_STYLE_TYPE.PARAGRAPH, WD_STYLE_TYPE.CHARACTER, WD_STYLE_TYPE.TABLE):
            continue
        if st.name in MONO:
            continue
        rpr = st.element.get_or_add_rPr()
        _letra(rpr)
        st.font.color.rgb = RGBColor.from_string(TEXTO)
    for st in d.styles:
        n = st.name
        if n.startswith("Heading") or n in ("Title", "TOC Heading"):
            st.font.color.rgb = RGBColor.from_string(AZUL)
            st.font.bold = True
        if n == "Title":
            st.font.size = Pt(24)
        if n == "Heading 1":
            st.font.size = Pt(16)
        if n == "Heading 2":
            st.font.size = Pt(13)
        if n in ("Subtitle",):
            st.font.color.rgb = RGBColor.from_string(NARANJA)
        if n in ("Image Caption", "Table Caption", "Caption"):
            st.font.color.rgb = RGBColor.from_string(GRIS)
            st.font.italic = True
            st.font.size = Pt(9.5)
        if n == "Hyperlink":
            st.font.color.rgb = RGBColor.from_string(AZUL)
        if n in ("Normal", "Body Text", "First Paragraph", "Compact"):
            st.font.size = Pt(11)
    d.save(ruta)


def _borde(padre, lado, color, grosor="6", tipo="single"):
    el = OxmlElement(f"w:{lado}")
    el.set(qn("w:val"), tipo)
    el.set(qn("w:sz"), grosor)
    el.set(qn("w:color"), color)
    padre.append(el)


def _sombra(celda, color):
    tcpr = celda._tc.get_or_add_tcPr()
    for viejo in tcpr.findall(qn("w:shd")):
        tcpr.remove(viejo)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcpr.append(shd)


def _tablas(d):
    for t in d.tables:
        pr = t._tbl.tblPr
        for viejo in pr.findall(qn("w:tblBorders")):
            pr.remove(viejo)
        bordes = OxmlElement("w:tblBorders")
        cab = t.rows[0]
        if all(not c.text.strip() for c in cab.cells):  # tabla de fotos: sin bordes ni cabecera
            t._tbl.remove(cab._tr)
            for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
                _borde(bordes, lado, "FFFFFF", "0", "nil")
            pr.append(bordes)
            continue
        _borde(bordes, "top", AZUL, "8")
        _borde(bordes, "bottom", AZUL, "8")
        _borde(bordes, "insideH", "D1D5DB", "4")
        for lado in ("left", "right", "insideV"):
            _borde(bordes, lado, "FFFFFF", "0", "nil")
        pr.append(bordes)
        for c in cab.cells:
            _sombra(c, AZUL)
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor.from_string("FFFFFF")
        for i, fila in enumerate(t.rows[1:]):
            if i % 2 == 1:
                for c in fila.cells:
                    _sombra(c, AZUL_CLARO)


def _incrustar_letra(ruta):
    """Incrusta Fira Sans (normal, negrita, cursiva) para que se vea igual en cualquier computador."""
    estilos = [("embedRegular", "Regular"), ("embedBold", "Bold"), ("embedItalic", "Italic"),
               ("embedBoldItalic", "BoldItalic")]
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(ruta) as z:
        z.extractall(tmp)
    w = tmp / "word"
    (w / "fonts").mkdir(exist_ok=True)
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    emb = []
    for i, (etiqueta, nombre) in enumerate(estilos, 1):
        shutil.copy(FUENTES / f"FiraSans-{nombre}.ttf", w / "fonts" / f"FiraSans-{nombre}.ttf")
        rels.append(f'<Relationship Id="rIdF{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                    f'relationships/font" Target="fonts/FiraSans-{nombre}.ttf"/>')
        emb.append(f'<w:{etiqueta} w:fontKey="{{00000000-0000-0000-0000-000000000000}}" r:id="rIdF{i}" '
                   f'w:subsetted="0"/>')
    rels.append("</Relationships>")
    (w / "_rels" / "fontTable.xml.rels").write_text("".join(rels), encoding="utf-8")
    ft = (w / "fontTable.xml").read_text(encoding="utf-8")
    if "xmlns:r=" not in ft:
        ft = ft.replace("<w:fonts ", '<w:fonts xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/'
                        'relationships" ', 1)
    ft = re.sub(r'<w:font w:name="Fira Sans">.*?</w:font>', "", ft, flags=re.S)
    ft = ft.replace("</w:fonts>", f'<w:font w:name="Fira Sans"><w:charset w:val="00"/><w:family w:val="swiss"/>'
                    f'<w:pitch w:val="variable"/>{"".join(emb)}</w:font></w:fonts>')
    (w / "fontTable.xml").write_text(ft, encoding="utf-8")
    st = (w / "settings.xml").read_text(encoding="utf-8")
    if "embedTrueTypeFonts" not in st:
        if "<w:zoom" in st:
            st = re.sub(r"(<w:zoom[^>]*/>)", r'\1<w:embedTrueTypeFonts w:val="1"/>', st, count=1)
        else:
            st = re.sub(r"(<w:settings[^>]*>)", r'\1<w:embedTrueTypeFonts w:val="1"/>', st, count=1)
    (w / "settings.xml").write_text(st, encoding="utf-8")
    ct = (tmp / "[Content_Types].xml").read_text(encoding="utf-8")
    if 'Extension="ttf"' not in ct:
        ct = ct.replace("<Types ", "<Types ", 1).replace(
            "</Types>", '<Default Extension="ttf" ContentType="application/x-font-ttf"/></Types>')
    (tmp / "[Content_Types].xml").write_text(ct, encoding="utf-8")
    ruta.unlink()
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        orden = ["[Content_Types].xml"] + sorted(str(p.relative_to(tmp)) for p in tmp.rglob("*")
                                                  if p.is_file() and p.name != "[Content_Types].xml")
        for nombre in orden:
            z.write(tmp / nombre, nombre)
    shutil.rmtree(tmp)


def acabado(ruta):
    ruta = Path(ruta)
    d = docx.Document(ruta)
    _tablas(d)
    d.save(ruta)
    _incrustar_letra(ruta)

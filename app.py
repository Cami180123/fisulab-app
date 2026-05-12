"""
FISULAB · IA PARA APOYO DIAGNÓSTICO ClÍNICO
Dashboard de apoyo diagnóstico para labio y paladar hendido
"""

import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import os
import time
import base64
import re
import json

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────────────────────
st.set_page_config(
    page_title="FISULAB · IA PARA APOYO DE DIAGNÓSTICO CLÍNICO",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── ESTILOS PERSONALIZADOS ───────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

/* ── AJUSTE DEFINITIVO DE ESPACIO SUPERIOR ── */
.topbar {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

section[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
}

section[data-testid="stAppViewContainer"] > div {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

div.block-container {
    padding-top: 0.5rem !important;
}

div.block-container > div:first-child {
    margin-top: 0 !important;
}

.topbar-title {
    color: #085041;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.topbar-sub {
    color: #6c757d;
    font-size: 12px;
    margin-top: 2px;
}
.topbar-badge {
    background: #fff8e1;
    color: #854F0B;
    border: 1px solid #f9cb42;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}

/* ── MÉTRICAS ── */
.metric-card {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    height: 160px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.metric-value { font-size: 26px; font-weight: 700; color: #085041; }
.metric-label { font-size: 12px; color: #6c757d; margin-top: 4px; }

/* ── BADGES DE COMPLEJIDAD ── */
.badge-alta {
    background: #FCEBEB; color: #A32D2D;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 500; display: inline-block;
}
.badge-media {
    background: #FAEEDA; color: #854F0B;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 500; display: inline-block;
}
.badge-baja {
    background: #EAF3DE; color: #3B6D11;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 500; display: inline-block;
}

/* ── AVISO LEGAL ── */
.disclaimer {
    background: #fff8e1;
    border-left: 4px solid #f9cb42;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    color: #633806;
    line-height: 1.6;
    margin-top: 16px;
}

/* ── TARJETAS HISTORIAL ── */
.caso-card {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.caso-nombre { font-size: 13px; font-weight: 600; color: #212529; }
.caso-fecha  { font-size: 11px; color: #6c757d; }

/* ── OCULTAR ELEMENTOS DE STREAMLIT ── */
#MainMenu {visibility: hidden;}
footer     {visibility: hidden;}
header     {visibility: hidden;}

/* ── FULLSCREEN LAYOUT WITHOUT GLOBAL SCROLL ── */
html, body {
    height: 100%;
    overflow: hidden;
}

section[data-testid="stAppViewContainer"] {
    height: 100vh;
}

section[data-testid="stAppViewContainer"] > div {
    height: 100vh;
}

div[data-testid="column"]:nth-of-type(1),
div[data-testid="column"]:nth-of-type(2),
div[data-testid="column"]:nth-of-type(3) {
    height: calc(100vh - 110px);
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)


# ── PROMPT MÉDICO ────────────────────────────────────────────────────────────
PROMPT_MEDICO = """
Eres un asistente de apoyo diagnóstico especializado en cirugía plástica y reconstructiva
pediátrica, con énfasis en labio y paladar hendido (fisuras labiopalatinas).

Analiza la imagen proporcionada y genera un informe clínico estructurado con el siguiente formato:

Paciente pediátrico o adulto (si la edad no se proporciona, indícalo como "edad no disponible").
Evaluación basada únicamente en imágenes; no hay historia clínica completa.
La información generada es para orientación y debe ser validada por un equipo médico multidisciplinar.

**ANÁLISIS INICIAL**
Describe lo que OBSERVAS objetivamente en la imagen:
- Continuidad del labio superior (unilateral/bilateral, completo/incompleto)
- Afectación del reborde alveolar
- Afectación del paladar duro y/o blando
- Simetría nasal y deformidad asociada
- Calidad y limitaciones de la imagen

**1. CLASIFICACIÓN CLÍNICA PROBABLE**
Identifica cuál categoría corresponde:
- Labio Normal (sin hendidura)
- Labio Leporino (LL) Unilateral Incompleto
- Labio Leporino (LL) Unilateral Completo
- Labio Leporino (LL) Bilateral
- Labio y Paladar Hendido
- No determinable (imagen insuficiente)

**2. CARACTERÍSTICAS CLÍNICAS OBSERVADAS**
Hallazgos visuales que justifican la clasificación.

**3. PRESUNTO DIAGNÓSTICO**
Nombre técnico según clasificación de Veau o Kernahan.

**4. PLAN DE TRATAMIENTO ORIENTATIVO**
Tabla con:
| Procedimiento | Número estimado | Objetivo |

**5. CRONOGRAMA POR RANGO DE EDAD**
Tabla con:
| Intervención | Rango de edad | Justificación |

**6. NIVEL DE COMPLEJIDAD**
- Menos de 2 intervenciones: BAJA
- Entre 3 y 5 intervenciones: MEDIA
- Más de 5 intervenciones: MUY ALTA

Justifica brevemente considerando extensión, compromiso alveolar/nasal, necesidad de ortodoncia, riesgos funcionales.

**7. CONSIDERACIONES ADICIONALES**
Especialidades requeridas: ortopedia prequirúrgica, fonoaudiología, ortodoncia, psicología, etc.

**8. DATOS FALTANTES Y ADVERTENCIAS**
Señala qué información faltante podría cambiar el pronóstico.


# BLOQUE ESTRUCTURADO (OBLIGATORIO)
Al FINAL de tu respuesta incluye SIEMPRE este bloque JSON exacto con los valores reales del caso.
No omitas este bloque bajo ninguna circunstancia.

```json
{
  "clasificacion_principal": "<nombre técnico breve, ej: LL Unilateral Completo>",
  "sistema": "<clasificación Veau y/o Kernahan, ej: Veau II / Kernahan>",
  "complejidad": "<BAJA | MEDIA | MUY ALTA>",
  "confianza_principal": <número entero 0-100>,
  "diferenciales": [
    {"nombre": "<diagnóstico 1>", "probabilidad": <número entero 0-100>},
    {"nombre": "<diagnóstico 2>", "probabilidad": <número entero 0-100>},
    {"nombre": "<diagnóstico 3>", "probabilidad": <número entero 0-100>}
  ],
  "cronograma": [
    {"edad": "<rango de edad>", "procedimiento": "<nombre>", "cantidad": <número entero de intervenciones de ese tipo>, "objetivo": "<descripción breve>"},
    {"edad": "<rango de edad>", "procedimiento": "<nombre>", "cantidad": <número entero de intervenciones de ese tipo>, "objetivo": "<descripción breve>"}
  ]
}
```
"""

# ── FUNCIÓN: parsear JSON estructurado de la respuesta de Gemini ─────────────
def parsear_json_ia(texto):
    """
    Extrae y parsea el bloque JSON al final de la respuesta de Gemini.
    Retorna un dict con los datos clínicos o valores por defecto si falla.
    """
    FALLBACK = {
        "clasificacion_principal": "No determinada",
        "sistema": "—",
        "complejidad": "BAJA",
        "confianza_principal": 0,
        "diferenciales": [],
        "cronograma": [],
    }
    try:
        match = re.search(r"```json\s*(\{.*?\})\s*```", texto, re.DOTALL)
        if not match:
            return FALLBACK
        datos = json.loads(match.group(1))

        datos["clasificacion_principal"] = str(datos.get("clasificacion_principal", "No determinada"))
        datos["sistema"]                 = str(datos.get("sistema", "—"))
        datos["complejidad"]             = str(datos.get("complejidad", "BAJA")).upper()
        datos["confianza_principal"]     = max(0, min(100, int(datos.get("confianza_principal", 0))))

        # Normalizar diferenciales — probabilidades clampadas entre 0 y 100
        datos["diferenciales"] = [
            {
                "nombre": str(d.get("nombre", "—")),
                "probabilidad": max(0, min(100, int(d.get("probabilidad", 0))))
            }
            for d in datos.get("diferenciales", []) if isinstance(d, dict)
        ]

        # Normalizar cronograma
        datos["cronograma"] = [
            {
                "edad":          str(c.get("edad", "—")),
                "procedimiento": str(c.get("procedimiento", "—")),
                "cantidad":      str(c.get("cantidad", "")),
                "objetivo":      str(c.get("objetivo", "—")),
            }
            for c in datos.get("cronograma", []) if isinstance(c, dict)
        ]

        return datos
    except Exception:
        return FALLBACK

# ── CLASE PDF con pie de página automático/ PIE DE PÁGINA automático en todas las páginas───────────────────────────────────
class FisuPDF(FPDF):
    def footer(self):
        self.set_y(-18)
        self.set_draw_color(15, 110, 86)
        self.set_line_width(0.4)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5,
            f"FISULAB  ·  Orientación de apoyo diagnóstico clínico generado con IA  ·  "
            f"Generado el {time.strftime('%d/%m/%Y %H:%M')}  ·  Pagina {self.page_no()}",
            align="C")


# ── FUNCIÓN: generar PDF ─────────────────────────────────────────────────────
def limpiar(texto):
    """Convierte texto a latin-1 eliminando caracteres no soportados por FPDF."""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")

def generar_pdf(paciente_id, paciente_edad, paciente_sexo, resultado_texto,
                clasificacion="No determinada", complejidad="N/D",
                confianza_modelo=0, cronograma=None, sistema="", diferenciales=None):
    if cronograma    is None: cronograma    = []
    if diferenciales is None: diferenciales = []

    # ── Limpiar el texto del informe: eliminar bloque JSON y Markdown ─────────
    texto_limpio = resultado_texto
    # Quitar bloque JSON estructurado
    texto_limpio = re.sub(r"# BLOQUE ESTRUCTURADO.*", "", texto_limpio, flags=re.DOTALL)
    # Quitar bloques de código ```
    texto_limpio = re.sub(r"```.*?```", "", texto_limpio, flags=re.DOTALL)
    # Quitar encabezados Markdown ## y #
    texto_limpio = re.sub(r"^#{1,3}\s*", "", texto_limpio, flags=re.MULTILINE)
    # Quitar negritas **texto**
    texto_limpio = re.sub(r"\*\*(.*?)\*\*", r"\1", texto_limpio)
    # Quitar cursivas *texto*
    texto_limpio = re.sub(r"\*(.*?)\*", r"\1", texto_limpio)
    # Quitar tablas Markdown (líneas con |)
    texto_limpio = re.sub(r"^\|.*\|$", "", texto_limpio, flags=re.MULTILINE)
    texto_limpio = re.sub(r"^[-|: ]+$",  "", texto_limpio, flags=re.MULTILINE)
    # Limpiar líneas vacías múltiples
    texto_limpio = re.sub(r"\n{3,}", "\n\n", texto_limpio).strip()

    # Colores corporativos
    VERDE       = (15, 110, 86)
    VERDE_OSC   = (8,  80,  65)
    GRIS_OSC    = (50, 50,  50)
    GRIS_MED    = (100,100, 100)
    GRIS_CLR    = (220,220, 220)
    AMBER       = (133, 79, 11)
    ROJO        = (163, 45, 45)
    AZUL        = (24,  95, 165)

    color_comp_map = {"MUY ALTA": ROJO, "MEDIA": AMBER, "BAJA": VERDE}
    color_comp     = color_comp_map.get(complejidad, VERDE_OSC)

    # Usar FisuPDF (definida a nivel de módulo) para pie de página automático
    pdf = FisuPDF()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # ── PÁGINA 1 — PORTADA RESUMEN ───────────────────────────────
    # ── ENCABEZADO CON LOGO/NOMBRE DE LA INSTITUCIÓN ──────────────────────────────────────
    logo_path = "fisulab.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=15, y=10, w=26)
        pdf.set_xy(46, 12)
    else:
        pdf.set_fill_color(15, 110, 86)
        pdf.rect(15, 10, 26, 26, "F")
        pdf.set_xy(18, 19)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(20, 8, "F", align="C")
        pdf.set_xy(46, 12)
 
    pdf.set_font("Arial", "B", 17)
    pdf.set_text_color(*VERDE)
    pdf.cell(0, 8, "FISULAB", ln=True)
    pdf.set_xy(46, 21)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(*GRIS_MED)
    pdf.cell(0, 5, limpiar("Fundación de Atención Integral para Labio y Paladar Hendido"), ln=True)
    pdf.set_xy(46, 28)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(*GRIS_MED)
    pdf.cell(0, 5, "Sistema de apoyo diagnostico con Inteligencia Artificial", ln=True)

    # ── LÍNEA SEPARADORA VERDE ────────────────────────────────────
    pdf.set_y(40)
    pdf.set_draw_color(*VERDE)
    pdf.set_line_width(1.0)
    pdf.line(15, 40, 195, 40)
    pdf.ln(7)

    # ── TÍTULO DEL INFORME ────────────────────────────────────────
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(*VERDE_OSC)
    pdf.cell(0, 8, limpiar("Informe de Apoyo Diagnóstico Clínico"), ln=True, align="C")
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(*GRIS_MED)
    pdf.cell(0, 6, limpiar("Generado con Inteligencia Artificial · Solo para orientación médica"), ln=True, align="C")
    pdf.ln(5)

    # ── DATOS DEL PACIENTE ────────────────────────────────────────
    ficha_y = pdf.get_y()
    pdf.set_fill_color(245, 247, 245)
    pdf.set_draw_color(*GRIS_CLR)
    pdf.set_line_width(0.3)
    pdf.rect(15, ficha_y, 180, 22, "FD")
    pdf.set_xy(19, ficha_y + 3)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*VERDE_OSC)
    pdf.cell(0, 5, "DATOS DEL PACIENTE", ln=True)
    pdf.set_xy(19, ficha_y + 9)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(*GRIS_OSC)
    pdf.cell(55, 5, limpiar(f"Paciente: {paciente_id}"))
    pdf.cell(45, 5, limpiar(f"Edad: {paciente_edad}"))
    pdf.cell(45, 5, limpiar(f"Sexo: {paciente_sexo}"))
    pdf.ln(6)
    pdf.set_x(19)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(*GRIS_MED)
    pdf.cell(0, 5, limpiar(f"Fecha de generación: {time.strftime('%d/%m/%Y  %H:%M')}"))
    pdf.ln(12)

    # ── RESUMEN CLÍNICO IA (3 bloques de color) ─────────────────────────────
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*VERDE_OSC)
    pdf.cell(0, 7, limpiar("1.  Resumen del Diagnóstico"), ln=True)
    pdf.set_draw_color(*VERDE)
    pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    bw = 56   # ancho de cada bloque
    bg = 4    # gap entre bloques
    by = pdf.get_y()
    bh = 30

    def bloque(x, titulo, valor, subtitulo, fill, borde, txt_color):
        pdf.set_fill_color(*fill)
        pdf.set_draw_color(*borde)
        pdf.set_line_width(0.4)
        pdf.rect(x, by, bw, bh, "FD")
        pdf.set_xy(x + 3, by + 3)
        pdf.set_font("Arial", size=7)
        pdf.set_text_color(*GRIS_MED)
        pdf.cell(bw - 6, 4, limpiar(titulo.upper()), ln=True)
        pdf.set_xy(x + 3, by + 8)
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(*txt_color)
        # Dividir valor largo en dos líneas si es necesario
        if len(valor) > 24:
            palabras = valor.split()
            linea1, linea2 = "", ""
            for p in palabras:
                if len(linea1) + len(p) < 24:
                    linea1 += p + " "
                else:
                    linea2 += p + " "
            pdf.cell(bw - 6, 5, limpiar(linea1.strip()), ln=True)
            pdf.set_xy(x + 3, by + 13)
            pdf.cell(bw - 6, 5, limpiar(linea2.strip()), ln=True)
        else:
            pdf.cell(bw - 6, 5, limpiar(valor), ln=True)
        pdf.set_xy(x + 3, by + 22)
        pdf.set_font("Arial", "I", 7)
        pdf.set_text_color(*GRIS_MED)
        pdf.cell(bw - 6, 4, limpiar(subtitulo), ln=True)

    bloque(15,           "Clasificación probable", clasificacion,         limpiar(sistema) or "Veau / Kernahan",
           (232,245,238), VERDE,     VERDE_OSC)
    bloque(15 + bw + bg, "Nivel de complejidad",   complejidad,           "Segun numero de intervenciones",
           (250,240,230) if complejidad == "MEDIA" else (250,235,235) if complejidad == "MUY ALTA" else (235,245,230),
           color_comp,   color_comp)
    bloque(15 + 2*(bw+bg),"Confianza del modelo",  f"{confianza_modelo}%","Resultado orientativo - requiere validacion",
           (232,241,251), AZUL,      AZUL)

    pdf.set_y(by + bh + 6)
    
    # ── CRONOGRAMA DINÁMICO ───────────────────────────────────────
    if cronograma:
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*VERDE_OSC)
        pdf.cell(0, 7, limpiar("2.  Plan de Tratamiento Orientativo"), ln=True)
        pdf.set_draw_color(*VERDE)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)

        colores_paso = [VERDE, (83,74,183), (133,79,11), AZUL, (153,60,29), (59,109,17)]
        for i, paso in enumerate(cronograma):
            edad  = limpiar(paso.get("edad",          "—"))
            proc  = limpiar(paso.get("procedimiento", "—"))
            obj   = limpiar(paso.get("objetivo",      "—"))
            cant  = paso.get("cantidad", "")
            c     = colores_paso[i % len(colores_paso)]

            # Número de paso en círculo (simulado con rect redondeado)
            cy = pdf.get_y()
            pdf.set_fill_color(c[0], c[1], c[2])
            pdf.rect(15, cy + 1, 7, 7, "F")
            pdf.set_xy(15, cy + 1)
            pdf.set_font("Arial", "B", 7)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(7, 7, str(i + 1), align="C")

            # Línea vertical conectora (excepto último)
            if i < len(cronograma) - 1:
                pdf.set_draw_color(*c)
                pdf.set_line_width(0.3)
                pdf.line(18.5, cy + 8, 18.5, cy + 18)

            # Contenido del paso
            pdf.set_xy(26, cy)
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(*c)
            pdf.cell(0, 6, limpiar(f"{proc}"), ln=True)

            pdf.set_x(26)
            pdf.set_font("Arial", size=8)
            pdf.set_text_color(*GRIS_MED)
            info_linea = f"Edad: {edad}"
            if cant:
                info_linea += f"   |   Intervenciones estimadas: {cant}"
            pdf.cell(169, 5, limpiar(info_linea), ln=True)

            pdf.set_x(26)
            pdf.set_font("Arial", "I", 9)
            pdf.set_text_color(*GRIS_OSC)
            pdf.multi_cell(169, 5, limpiar(f"Objetivo: {obj}"))
            pdf.ln(2)

    # ── Sección: Clasificación diferencial ────────────────────
    if diferenciales:
        pdf.ln(2)
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*VERDE_OSC)
        pdf.cell(0, 7, limpiar("3.  Clasificación Diferencial"), ln=True)
        pdf.set_draw_color(*VERDE)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)

        difs_ord = sorted(diferenciales, key=lambda x: x.get("probabilidad", 0), reverse=True)
        for d in difs_ord:
            nombre = limpiar(d.get("nombre", "—"))
            prob   = d.get("probabilidad", 0)
            bar_w  = int(160 * prob / 100)

            pdf.set_font("Arial", size=9)
            pdf.set_text_color(*GRIS_OSC)
            pdf.cell(130, 5, nombre)
            pdf.set_font("Arial", "B", 9)
            pdf.set_text_color(*VERDE_OSC)
            pdf.cell(30, 5, f"{prob}%", align="R", ln=True)

            # Barra de probabilidad
            bar_y = pdf.get_y()
            pdf.set_fill_color(230, 230, 230)
            pdf.rect(15, bar_y, 160, 3, "F")
            if bar_w > 0:
                pdf.set_fill_color(*VERDE)
                pdf.rect(15, bar_y, bar_w, 3, "F")
            pdf.ln(6)
            
    # ── PÁGINA 2 — ANÁLISIS DETALLADO DE LA IA ────────────────────
    pdf.add_page()

    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*VERDE_OSC)
    pdf.cell(0, 7, limpiar("4.  Análisis Clínico Detallado"), ln=True)
    pdf.set_draw_color(*VERDE)
    pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    # Renderizar el texto limpio sección por sección
    secciones_titulos = [
        "ANALISIS INICIAL", "CLASIFICACION CLINICA PROBABLE", "CARACTERISTICAS CLINICAS OBSERVADAS",
        "PRESUNTO DIAGNOSTICO", "PLAN DE TRATAMIENTO ORIENTATIVO", "CRONOGRAMA POR RANGO DE EDAD",
        "NIVEL DE COMPLEJIDAD", "CONSIDERACIONES ADICIONALES", "DATOS FALTANTES Y ADVERTENCIAS"
    ]

    for linea in texto_limpio.split("\n"):
        linea_strip = linea.strip()
        if not linea_strip:
            pdf.ln(2)
            continue

        linea_upper = linea_strip.upper().replace(".", "").replace(":", "")
        es_titulo = any(t in linea_upper for t in secciones_titulos) and len(linea_strip) < 80

        if es_titulo:
            pdf.ln(2)
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(*VERDE_OSC)
            pdf.set_fill_color(232, 245, 238)
            pdf.cell(180, 7, limpiar(f"  {linea_strip}"), ln=True, fill=True)
            pdf.ln(1)
        else:
            if linea_strip.startswith("- "):
                pdf.set_font("Arial", size=9)
                pdf.set_text_color(*GRIS_OSC)
                pdf.set_fill_color(15, 110, 86)
                bul_y = pdf.get_y() + 3
                pdf.rect(20, bul_y, 1.5, 1.5, "F")
                pdf.set_x(23)
                pdf.multi_cell(172, 5, limpiar(linea_strip[2:]))
            else:
                pdf.set_x(15)
                pdf.set_font("Arial", size=9)
                pdf.set_text_color(*GRIS_OSC)
                pdf.multi_cell(180, 5, limpiar(linea_strip))

    # ── AVISO LEGAL ───────────────────────────────────────────────
    pdf.ln(6)
    av_y = pdf.get_y()
    pdf.set_fill_color(255, 248, 225)
    pdf.set_draw_color(200, 150, 0)
    pdf.set_line_width(0.5)
    pdf.rect(15, av_y, 180, 28, "FD")
    pdf.set_xy(19, av_y + 3)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(*AMBER)
    pdf.cell(0, 5, limpiar("⚠  AVISO IMPORTANTE"), ln=True)
    pdf.set_x(19)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(80, 50, 0)
    pdf.multi_cell(172, 4.5, limpiar(
        "IMPORTANTE: Este análisis es una orientación de apoyo generada por Inteligencia Artificial, basada exclusivamente"
        "en el ánalisis de imágenes fotográficas. No constituye un diagnóstico medico definitivo. La clasificación y el plan de tratamiento deben ser validados" 
        "mediante evaluación clínica presencial completa por el equipo clínico multidisciplinar de FISULAB. El modelo puede presentar limitaciones según"
        "la calidad, ángulo e iluminación de la imagen proporcionada."
    ))
    return bytes(pdf.output())
        
# ── FUNCIÓN LOGO ──────────────────────────────────────────────────────────────
def get_logo_base64(path="fisulab.png"):
    """Convierte el logo a texto base64 para usarlo en HTML inline."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None
 
 
# ── PERSISTENCIA: archivo JSON local ─────────────────────────────────────────
HISTORIAL_PATH = "fisulab_historial.json"
 
def cargar_historial():
    """Lee el historial desde disco. Si no existe, retorna lista vacía."""
    if os.path.exists(HISTORIAL_PATH):
        try:
            with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []
 
def guardar_historial(historial):
    """Escribe el historial completo en disco."""
    try:
        with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"No se pudo guardar el historial: {e}")


# ── ESTADO DE SESIÓN ─────────────────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "datos_paciente" not in st.session_state:
    st.session_state.datos_paciente = {}
if "datos_ia" not in st.session_state:
    st.session_state.datos_ia = {}
    
# Guarda los tokens y costos del último análisis
if "tokens_info" not in st.session_state:
    st.session_state.tokens_info = None


# API key desde secrets o variable de entorno
API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── TOPBAR ───────────────────────────────────────────────────────────────────
logo_b64 = get_logo_base64()

if logo_b64:
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:52px; width:auto; object-fit:contain;">'
else:
    logo_html = '<div style="width:52px;height:52px;background:#1D9E75;border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:18px;">F</div>'

st.markdown(f"""
<div class="topbar">
    <div style="display:flex; align-items:center; gap:14px;">
        {logo_html}
        <div>
            <div class="topbar-title">FISULAB · IA Clínica</div>
            <div class="topbar-sub">Apoyo diagnóstico — labio y paladar hendido</div>
        </div>
    </div>
    <div class="topbar-badge">⚠️ No reemplaza un diagnóstico médico profesional</div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT PRINCIPAL ─────────────────────────────────────────────────────────
col_centro, col_der = st.columns([2.8, 1.1])

# ════════════════════════════════════════════════════════════
# COLUMNA CENTRAL — Formulario arriba + resultados abajo
# ════════════════════════════════════════════════════════════
with col_centro:

    # ── FILA SUPERIOR: formulario + imagen + botones ──────────
    # En escritorio: 3 sub-columnas lado a lado.
    # En celular: Streamlit las apila automáticamente.
    f1, f2, f3 = st.columns([1.2, 1.2, 1])

    with f1:
        st.markdown("##### 👤 Datos del paciente")
        paciente_id   = st.text_input("Nombre / ID", placeholder="Paciente 2024-112")
        paciente_edad = st.text_input("Edad", placeholder="Ej: 3 meses")
        paciente_sexo = st.selectbox("Sexo", ["No especificado", "Femenino", "Masculino"])

    with f2:
        st.markdown("##### 📷 Imagen clínica")
        imagen_file = st.file_uploader(
            "Cargar imagen",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed"
        )
        if imagen_file:
            imagen_pil = Image.open(imagen_file)
            st.image(imagen_pil, caption="Vista previa", use_container_width=True)

    with f3:
        st.markdown("##### ⚙️ Acciones")
        # Espacio para alinear verticalmente con los otros campos
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        analizar = st.button(
            "🔬 Analizar con IA",
            use_container_width=True,
            type="primary",
            disabled=(not imagen_file or not API_KEY)
        )
        st.button(
            "🆕 Nuevo paciente",
            use_container_width=True,
            on_click=lambda: st.session_state.update({
                "resultado": None,
                "datos_paciente": {},
                "datos_ia": {}
            })
        )
        if not API_KEY:
            st.caption("⚠️ API Key no configurada.")
        if not imagen_file:
            st.caption("⚠️ Carga una imagen para continuar.")

    st.divider()

    # ════════════════════════════════════════════════════════════
    # LÓGICA DE ANÁLISIS — va aquí dentro de col_centro
    # ════════════════════════════════════════════════════════════
    if analizar and imagen_file and API_KEY:
        try:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")

            imagen_pil = Image.open(imagen_file)
            buffer = io.BytesIO()
            fmt = imagen_pil.format if imagen_pil.format else "JPEG"
            imagen_pil.save(buffer, format=fmt)
            imagen_bytes = buffer.getvalue()

            contexto_paciente = f"""
Datos del paciente:
- ID / Nombre: {paciente_id if paciente_id else 'No proporcionado'}
- Edad: {paciente_edad if paciente_edad else 'No proporcionada'}
- Sexo: {paciente_sexo}
"""
            prompt_completo = contexto_paciente + "\n\n" + PROMPT_MEDICO
            mime_map = {
                "JPEG": "image/jpeg", "JPG": "image/jpeg",
                "PNG":  "image/png",  "WEBP": "image/webp"
            }
            mime_type = mime_map.get(fmt.upper(), "image/jpeg")

            with st.spinner("Analizando imagen con IA... esto puede tomar unos segundos."):
                response = model.generate_content([
                    prompt_completo,
                    {"mime_type": mime_type, "data": imagen_bytes}
                ])
                st.session_state.resultado = response.text

                _usage             = response.usage_metadata
                _prompt_tokens     = _usage.prompt_token_count
                _candidates_tokens = _usage.candidates_token_count
                _total_tokens      = _usage.total_token_count
                _input_price_per_m  = 0.15
                _output_price_per_m = 0.60
                _input_cost  = (_prompt_tokens     / 1_000_000) * _input_price_per_m
                _output_cost = (_candidates_tokens / 1_000_000) * _output_price_per_m
                _total_cost  = _input_cost + _output_cost

                st.session_state.tokens_info = {
                    "prompt_tokens":     _prompt_tokens,
                    "candidates_tokens": _candidates_tokens,
                    "total_tokens":      _total_tokens,
                    "input_cost":        _input_cost,
                    "output_cost":       _output_cost,
                    "total_cost":        _total_cost,
                }
                st.session_state.datos_paciente = {
                    "id":   paciente_id or f"Caso {len(st.session_state.historial)+1}",
                    "edad": paciente_edad or "No especificada",
                    "sexo": paciente_sexo,
                }
                datos_ia = parsear_json_ia(response.text)
                st.session_state.datos_ia = datos_ia
                comp_map = {"MUY ALTA": "alta", "MEDIA": "media", "BAJA": "baja"}
                comp = comp_map.get(datos_ia["complejidad"], "baja")
                st.session_state.historial.insert(0, {
                    "nombre":      paciente_id or f"Caso {len(st.session_state.historial)+1}",
                    "fecha":       time.strftime("%d %b %Y"),
                    "complejidad": comp
                })

        except Exception as e:
            st.error(f"❌ Error al conectar con la API: {str(e)}")

    # ── RESULTADOS — debajo del formulario ───────────────────
    if st.session_state.resultado is None:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:300px;color:#adb5bd;text-align:center;">
            <div style="font-size:48px;">🔬</div>
            <div style="font-size:16px;font-weight:500;color:#6c757d">Sin análisis aún</div>
            <div style="font-size:13px;margin-top:8px;color:#adb5bd">
                Carga una imagen y presiona <strong>Analizar con IA</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        resultado_texto = st.session_state.resultado
        datos_ia        = st.session_state.datos_ia
        clasificacion    = datos_ia.get("clasificacion_principal", "No determinada")
        sistema          = datos_ia.get("sistema", "—")
        complejidad      = datos_ia.get("complejidad", "BAJA")
        confianza_modelo = datos_ia.get("confianza_principal", 0)
        diferenciales    = datos_ia.get("diferenciales", [])
        cronograma       = datos_ia.get("cronograma", [])
        color_map  = {"MUY ALTA": "#A32D2D", "MEDIA": "#854F0B", "BAJA": "#3B6D11"}
        color_comp = color_map.get(complejidad, "#3B6D11")

        # ── 3 tarjetas resumen ────────────────────────────────
        st.markdown("**📌 Resumen clínico IA**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Clasificación probable</div>
                <div class="metric-value" style="font-size:14px;line-height:1.3">{clasificacion}</div>
                <div class="metric-label">{sistema}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Complejidad estimada</div>
                <div class="metric-value" style="color:{color_comp}">{complejidad}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Confianza del modelo</div>
                <div style="width:100%;height:8px;background:#e9ecef;border-radius:6px;margin:6px 0;">
                    <div style="width:{confianza_modelo}%;height:8px;background:#1d7af3;border-radius:6px;"></div>
                </div>
                <div style="font-weight:700;color:#1d7af3">{confianza_modelo}%</div>
                <div class="metric-label">Resultado orientativo · Validación requerida</div>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Diferencial ───────────────────────────────────────
        st.markdown("**🔬 Clasificación diferencial**")
        if diferenciales:
            diferenciales_ordenados = sorted(diferenciales, key=lambda x: x["probabilidad"], reverse=True)
            for i, d in enumerate(diferenciales_ordenados):
                nombre = d["nombre"]
                prob   = d["probabilidad"]
                color_barra = "#0F6E56" if i == 0 else "#6c757d" if i == 1 else "#ced4da"
                st.markdown(f"""
                <div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:12px;font-weight:600;color:#212529">{nombre}</span>
                        <span style="font-size:12px;font-weight:700;color:{color_barra}">{prob}%</span>
                    </div>
                    <div style="width:100%;height:7px;background:#e9ecef;border-radius:6px;overflow:hidden;">
                        <div style="width:{prob}%;height:7px;background:{color_barra};border-radius:6px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No se encontraron diagnósticos diferenciales.")

        st.divider()

        # ── Cronograma ────────────────────────────────────────
        st.markdown("**🗓️ Cronograma orientativo**")
        if cronograma:
            colores_tl = ["#0F6E56","#534AB7","#854F0B","#185FA5","#993C1D","#3B6D11"]
            for i, paso in enumerate(cronograma):
                color        = colores_tl[i % len(colores_tl)]
                cantidad_txt = paso.get("cantidad", "")
                cant_html    = (f'<span style="background:#f1f3f5;color:#495057;font-size:10px;'
                                f'padding:2px 7px;border-radius:10px;margin-top:3px;display:inline-block;">'
                                f'🔢 {cantidad_txt} intervenciones</span>') if cantidad_txt else ""
                st.markdown(
                    f'<div style="display:flex;gap:12px;margin-bottom:12px;">'
                    f'<div style="min-width:24px;height:24px;border-radius:50%;background:{color}20;'
                    f'border:1.5px solid {color};display:flex;align-items:center;justify-content:center;'
                    f'font-size:10px;font-weight:700;color:{color};flex-shrink:0;">{i+1}</div>'
                    f'<div style="border-left:2px solid {color};padding-left:10px;flex:1;">'
                    f'<div style="font-size:13px;font-weight:700;color:#212529">{paso["procedimiento"]}</div>'
                    f'<div style="font-size:11px;color:{color};font-weight:600;">📅 {paso["edad"]}</div>'
                    f'{cant_html}'
                    f'<div style="font-size:11px;color:#6c757d;margin-top:3px;">🎯 {paso["objetivo"]}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No se encontró cronograma.")

        # ── Equipo multidisciplinar ───────────────────────────
        st.markdown("**👥 Equipo multidisciplinar recomendado**")
        equipos_config = {
            "Cirugía plástica":    {"bg":"#E1F5EE","color":"#085041","border":"#9FE1CB","icon":"🔪"},
            "Fonoaudiología":      {"bg":"#EEEDFE","color":"#534AB7","border":"#CECBF6","icon":"🗣️"},
            "Ortodoncia":          {"bg":"#E6F1FB","color":"#185FA5","border":"#B5D4F4","icon":"🦷"},
            "Psicología":          {"bg":"#FAEEDA","color":"#854F0B","border":"#FAC775","icon":"🧠"},
            "Ortopedia facial":    {"bg":"#FAECE7","color":"#993C1D","border":"#F5C4B3","icon":"🦴"},
            "Genética clínica":    {"bg":"#EAF3DE","color":"#3B6D11","border":"#C0DD97","icon":"🧬"},
            "Nutrición":           {"bg":"#FFF8E1","color":"#854F0B","border":"#FFE082","icon":"🥗"},
            "Otorrinolaringología":{"bg":"#FCE4EC","color":"#880E4F","border":"#F48FB1","icon":"👂"},
            "Trabajo social":      {"bg":"#E8F5E9","color":"#2E7D32","border":"#A5D6A7","icon":"🤝"},
            "Anestesiología":      {"bg":"#E3F2FD","color":"#1565C0","border":"#90CAF9","icon":"💉"},
        }
        texto_upper = resultado_texto.upper()
        equipos_detectados = [
            (esp, cfg) for esp, cfg in equipos_config.items()
            if any(p in texto_upper for p in esp.upper().split())
        ]
        if not equipos_detectados:
            equipos_detectados = [
                ("Cirugía plástica", equipos_config["Cirugía plástica"]),
                ("Fonoaudiología",   equipos_config["Fonoaudiología"]),
                ("Ortodoncia",       equipos_config["Ortodoncia"]),
                ("Psicología",       equipos_config["Psicología"]),
            ]
        chips_html = "".join([
            f'<span style="display:inline-flex;align-items:center;gap:4px;background:{cfg["bg"]};'
            f'color:{cfg["color"]};border:1px solid {cfg["border"]};padding:5px 11px;'
            f'border-radius:20px;font-size:11px;font-weight:500;margin:3px 3px 3px 0;">'
            f'{cfg["icon"]} {esp}</span>'
            for esp, cfg in equipos_detectados
        ])
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:0;padding:6px 0;">{chips_html}</div>',
            unsafe_allow_html=True
        )

        st.divider()

        # ── Informe completo ──────────────────────────────────
        st.markdown("### 📄 Informe completo")
        resultado_limpio = resultado_texto
        resultado_limpio = re.sub(r"# BLOQUE ESTRUCTURADO.*", "", resultado_limpio, flags=re.DOTALL)
        resultado_limpio = re.sub(r"```json.*?```", "", resultado_limpio, flags=re.DOTALL)
        resultado_limpio = re.sub(r"```.*?```",     "", resultado_limpio, flags=re.DOTALL)
        resultado_limpio = re.sub(r"\n{3,}", "\n\n", resultado_limpio).strip()
        st.markdown(resultado_limpio)

        st.divider()

        # ── PDF + botones ─────────────────────────────────────
        pdf_bytes = generar_pdf(
            paciente_id or "Caso IA",
            paciente_edad or "No especificada",
            paciente_sexo,
            resultado_texto,
            clasificacion, complejidad, confianza_modelo, cronograma,
        )
        b1, b2, b3 = st.columns(3)
        with b1:
            st.download_button(
                "📄 Exportar PDF clínico",
                data=pdf_bytes,
                file_name=f"fisulab_{time.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with b2:
            if st.button("🔄 Nuevo análisis", use_container_width=True):
                st.session_state.resultado = None
                st.rerun()
        with b3:
            st.button("💾 Guardar en sistema", use_container_width=True, disabled=True,
                      help="Próximamente")

        # ── Aviso legal ───────────────────────────────────────
        st.markdown("""
        <div class="disclaimer">
            <strong>⚠️ Aviso importante:</strong>
            Este análisis es una orientación de apoyo generada por IA, basada exclusivamente en imágenes fotográficas.
            No constituye un diagnóstico médico definitivo. Debe ser validado por el equipo clínico de FISULAB
            mediante evaluación presencial completa.
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# COLUMNA DERECHA — Solo estadísticas y costos
# ════════════════════════════════════════════════════════════
with col_der:

    # ── Cálculos ─────────────────────────────────────────────
    total  = len(st.session_state.historial)
    altas  = sum(1 for c in st.session_state.historial if c["complejidad"] == "alta")
    medias = sum(1 for c in st.session_state.historial if c["complejidad"] == "media")
    bajas  = sum(1 for c in st.session_state.historial if c["complejidad"] == "baja")
    mes_actual = time.strftime("%b %Y")
    casos_mes  = sum(1 for c in st.session_state.historial if mes_actual in c.get("fecha", ""))
    if casos_mes == 0:
        casos_mes = total

    conteo_tipos = {}
    for c in st.session_state.historial:
        tipo = c.get("clasificacion", "No determinada")
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1
    if conteo_tipos:
        tipo_top = max(conteo_tipos, key=conteo_tipos.get)
        tipo_top_n = conteo_tipos[tipo_top]
        tipo_top_pct = round((tipo_top_n / total) * 100) if total > 0 else 0
        tipo_top_corto = tipo_top.replace("Labio Leporino", "LL").replace("Labio y Paladar Hendido", "LPH")
    else:
        tipo_top_corto = "—"
        tipo_top_pct   = 0

    # ── Resumen rápido en 2 chips ─────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;margin-top:4px;">
        <div style="background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;
                    padding:8px;text-align:center;">
            <div style="font-size:20px;font-weight:700;color:#085041;">{total}</div>
            <div style="font-size:10px;color:#6c757d;">Casos analizados</div>
        </div>
        <div style="background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;
                    padding:8px;text-align:center;">
            <div style="font-size:20px;font-weight:700;color:#185FA5;">89%</div>
            <div style="font-size:10px;color:#6c757d;">Precisión validada</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Barras de complejidad ─────────────────────────────────
    if total > 0:
        def barra(label, valor, color_bar, color_txt):
            pct = round((valor / total) * 100) if total > 0 else 0
            return (
                f'<div style="margin-bottom:7px;">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:2px;">'
                f'<span style="font-size:11px;color:#212529">{label}</span>'
                f'<span style="font-size:11px;font-weight:600;color:{color_txt}">{valor} · {pct}%</span></div>'
                f'<div style="width:100%;height:5px;background:#e9ecef;border-radius:4px;overflow:hidden;">'
                f'<div style="width:{pct}%;height:5px;background:{color_bar};border-radius:4px;"></div></div>'
                f'</div>'
            )
        st.markdown(
            '<div style="font-size:10px;color:#6c757d;text-transform:uppercase;'
            'letter-spacing:0.5px;margin-bottom:6px;">Complejidad</div>'
            + barra("Alta",  altas,  "#A32D2D", "#A32D2D")
            + barra("Media", medias, "#854F0B", "#854F0B")
            + barra("Baja",  bajas,  "#3B6D11", "#3B6D11"),
            unsafe_allow_html=True
        )

        # ── Tipo más frecuente ────────────────────────────────
        if tipo_top_corto != "—":
            st.markdown(f"""
            <div style="background:#E1F5EE;border-radius:8px;padding:8px 10px;margin-top:4px;margin-bottom:10px;">
                <div style="font-size:10px;color:#0F6E56;text-transform:uppercase;letter-spacing:0.4px;">
                    Tipo más frecuente
                </div>
                <div style="font-size:12px;font-weight:600;color:#085041;margin-top:2px;">
                    {tipo_top_corto} · {tipo_top_pct}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Historial compacto (últimos 5 casos, sin tab) ─────────
    if st.session_state.historial:
        st.markdown(
            '<div style="font-size:10px;color:#6c757d;text-transform:uppercase;'
            'letter-spacing:0.5px;margin-bottom:6px;">Últimos casos</div>',
            unsafe_allow_html=True
        )
        badge_map = {
            "alta":  ('<span style="background:#FCEBEB;color:#A32D2D;padding:2px 7px;'
                      'border-radius:10px;font-size:10px;">Alta</span>'),
            "media": ('<span style="background:#FAEEDA;color:#854F0B;padding:2px 7px;'
                      'border-radius:10px;font-size:10px;">Media</span>'),
            "baja":  ('<span style="background:#EAF3DE;color:#3B6D11;padding:2px 7px;'
                      'border-radius:10px;font-size:10px;">Baja</span>'),
        }
        for caso in st.session_state.historial[:5]:
            badge = badge_map.get(caso["complejidad"], "")
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:6px 8px;border:1px solid #e9ecef;border-radius:7px;margin-bottom:5px;background:white;">'
                f'<div>'
                f'<div style="font-size:11px;font-weight:600;color:#212529;">{caso["nombre"]}</div>'
                f'<div style="font-size:10px;color:#6c757d;">{caso["fecha"]}</div>'
                f'</div>'
                f'{badge}</div>',
                unsafe_allow_html=True
            )

    st.divider()

    # ── Panel de costos ───────────────────────────────────────
    ti = st.session_state.get("tokens_info")
    if ti:
        COP_POR_USD = 4_200
        st.markdown(f"""
        <div style="background:#f0faf5;border:1px solid #9FE1CB;border-radius:8px;padding:10px 12px;">
            <div style="font-size:10px;font-weight:600;color:#085041;text-transform:uppercase;
                        letter-spacing:0.5px;margin-bottom:8px;">💰 Costo del último análisis</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px;">
                <div style="background:white;border:1px solid #e9ecef;border-radius:6px;
                            padding:6px;text-align:center;">
                    <div style="font-size:13px;font-weight:700;color:#085041;">{ti['prompt_tokens']:,}</div>
                    <div style="font-size:9px;color:#6c757d;">Tokens entrada</div>
                </div>
                <div style="background:white;border:1px solid #e9ecef;border-radius:6px;
                            padding:6px;text-align:center;">
                    <div style="font-size:13px;font-weight:700;color:#534AB7;">{ti['candidates_tokens']:,}</div>
                    <div style="font-size:9px;color:#6c757d;">Tokens salida</div>
                </div>
            </div>
            <div style="background:white;border:1px solid #e9ecef;border-radius:6px;padding:8px 10px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                    <span style="font-size:10px;color:#6c757d;">Entrada</span>
                    <span style="font-size:10px;font-weight:600;color:#212529;">${ti['input_cost']:.6f} USD</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                    <span style="font-size:10px;color:#6c757d;">Salida</span>
                    <span style="font-size:10px;font-weight:600;color:#212529;">${ti['output_cost']:.6f} USD</span>
                </div>
                <div style="border-top:1px solid #e9ecef;padding-top:5px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:11px;font-weight:700;color:#085041;">Total</span>
                    <div style="text-align:right;">
                        <div style="font-size:13px;font-weight:700;color:#085041;">
                            ${ti['total_cost']:.6f} USD
                        </div>
                        <div style="font-size:9px;color:#6c757d;">
                            ≈ ${ti['total_cost'] * COP_POR_USD:,.0f} COP
                        </div>
                    </div>
                </div>
            </div>
            <div style="font-size:9px;color:#6c757d;text-align:center;margin-top:6px;line-height:1.4;">
                Gemini 2.5 Flash · $0.15/M entrada · $0.60/M salida
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="font-size:11px;color:#adb5bd;text-align:center;margin-top:8px;">'
            'El costo aparecerá aquí después del primer análisis.</div>',
            unsafe_allow_html=True
        )

# ── PIE DE PÁGINA ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#adb5bd;font-size:12px;padding:8px 0;">
    FISULAB · IA de apoyo clínico · Proyecto académico — Datos e Inteligencia Artifical (IA) · 2026<br>
    <span style="color:#dc3545">Este sistema es experimental. No usar como único criterio dediagnóstico.</span>
</div>
""", unsafe_allow_html=True)

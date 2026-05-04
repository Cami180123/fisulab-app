"""
FISULAB · IA PARA APOYO DIAGNÓSTICO ClÍNICO
Dashboard de apoyo diagnóstico para labio y paladar hendido
Requiere: pip install streamlit google-generativeai pillow fpdf2
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
    page_title="FISULAB ·  IA PARA APOYO DIAGNÓSTICO ClÍNICO",
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

## ANÁLISIS INICIAL
## Describe lo que OBSERVAS objetivamente en la imagen:
- Continuidad del labio superior (unilateral/bilateral, completo/incompleto)
- Afectación del reborde alveolar
- Afectación del paladar duro y/o blando
- Simetría nasal y deformidad asociada
- Calidad y limitaciones de la imagen

## 1. CLASIFICACIÓN CLÍNICA PROBABLE
Identifica cuál categoría corresponde:
- Labio Normal (sin hendidura)
- Labio Leporino (LL) Unilateral Incompleto
- Labio Leporino (LL) Unilateral Completo
- Labio Leporino (LL) Bilateral
- Labio y Paladar Hendido
- No determinable (imagen insuficiente)

## 2. CARACTERÍSTICAS CLÍNICAS OBSERVADAS
Hallazgos visuales que justifican la clasificación.

## 3. PRESUNTO DIAGNÓSTICO
Nombre técnico según clasificación de Veau o Kernahan.

## 4. PLAN DE TRATAMIENTO ORIENTATIVO
Tabla con:
| Procedimiento | Número estimado | Objetivo |

## 5. CRONOGRAMA POR RANGO DE EDAD
Tabla con:
| Intervención | Rango de edad | Justificación |

## 6. NIVEL DE COMPLEJIDAD
- Menos de 2 intervenciones: BAJA
- Entre 3 y 5 intervenciones: MEDIA
- Más de 5 intervenciones: MUY ALTA

Justifica brevemente considerando extensión, compromiso alveolar/nasal, necesidad de ortodoncia, riesgos funcionales.

## 7. CONSIDERACIONES ADICIONALES
Especialidades requeridas: ortopedia prequirúrgica, fonoaudiología, ortodoncia, psicología, etc.

## 8. DATOS FALTANTES Y ADVERTENCIAS
Señala qué información faltante podría cambiar el pronóstico.

---
IMPORTANTE: Este análisis es una guía de apoyo para el médico tratante. No constituye un
diagnóstico médico definitivo. Es fundamental una evaluación clínica completa y multidisciplinar.

---
## BLOQUE ESTRUCTURADO (OBLIGATORIO)
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
    {"edad": "<rango de edad>", "procedimiento": "<nombre>", "objetivo": "<descripción breve>"},
    {"edad": "<rango de edad>", "procedimiento": "<nombre>", "objetivo": "<descripción breve>"}
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
                "objetivo":      str(c.get("objetivo", "—")),
            }
            for c in datos.get("cronograma", []) if isinstance(c, dict)
        ]

        return datos
    except Exception:
        return FALLBACK


# ── FUNCIÓN: generar PDF ─────────────────────────────────────────────────────
def generar_pdf(paciente_id, paciente_edad, paciente_sexo, resultado_texto,
                clasificacion="No determinada", complejidad="N/D",
                confianza_modelo=0, cronograma=None):
    if cronograma is None:
        cronograma = []

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # ── ENCABEZADO CON LOGO ──────────────────────────────────────
    logo_path = "fisulab.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=15, y=10, w=28, h=0)

    # ── NOMBRE DE LA INSTITUCIÓN ──────────────────────────────────
    pdf.set_xy(48, 14)
    pdf.set_font("Arial", "B", 15)
    pdf.set_text_color(74, 140, 40)
    pdf.cell(0, 7, "FISULAB", ln=True)

    pdf.set_xy(48, 22)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Fundación de Atención Integral para Labio y Paladar Hendido", ln=True)

    # ── LÍNEA SEPARADORA VERDE ────────────────────────────────────
    pdf.set_y(42)
    pdf.set_draw_color(74, 140, 40)
    pdf.set_line_width(0.8)
    pdf.line(15, 42, 195, 42)
    pdf.ln(6)

    # ── TÍTULO DEL INFORME ────────────────────────────────────────
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(8, 80, 65)
    pdf.cell(0, 9, "Informe para apoyo diagnóstico clínico - generado con IA", ln=True, align="C")
    pdf.ln(2)

    # ── DATOS DEL PACIENTE ────────────────────────────────────────
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 7, f"Paciente: {paciente_id}   |   Edad: {paciente_edad}   |   Sexo: {paciente_sexo}", ln=True)
    pdf.cell(0, 7, f"Fecha de generacion: {time.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(3)

    # ── RESUMEN CLÍNICO IA (TARJETAS) ─────────────────────────────
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(8, 80, 65)
    pdf.cell(0, 8, "Resumen clínico IA", ln=True)
    pdf.ln(2)

    card_y = pdf.get_y()
    card_h = 26
    card_w = 58
    gap    = 4

    def draw_card(x, title, value, subtitle="", color=(8, 80, 65)):
        pdf.set_xy(x, card_y)
        pdf.set_draw_color(220, 220, 220)
        pdf.rect(x, card_y, card_w, card_h)
        pdf.set_xy(x + 2, card_y + 3)
        pdf.set_font("Arial", size=8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(card_w - 4, 4, title, ln=True)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*color)
        valor_corto = value[:28] + "..." if len(value) > 28 else value
        pdf.cell(card_w - 4, 8, valor_corto, ln=True)
        if subtitle:
            pdf.set_font("Arial", size=7)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(card_w - 4, 4, subtitle, ln=True)

    x0 = 15
    draw_card(x0,                    "Clasificacion",  clasificacion, "Veau / Kernahan")
    draw_card(x0 + card_w + gap,     "Complejidad",    complejidad)
    draw_card(x0 + 2*(card_w + gap), "Confianza IA",   f"{confianza_modelo} %",
              "Resultado orientativo", color=(29, 122, 243))
    pdf.ln(card_h + 6)

    # ── CRONOGRAMA DINÁMICO ───────────────────────────────────────
    if cronograma:
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(8, 80, 65)
        pdf.cell(0, 8, "Cronograma orientativo", ln=True)
        pdf.ln(2)

        for paso in cronograma:
            edad = paso["edad"].encode("latin-1", errors="replace").decode("latin-1")
            proc = paso["procedimiento"].encode("latin-1", errors="replace").decode("latin-1")
            obj  = paso["objetivo"].encode("latin-1", errors="replace").decode("latin-1")

            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(15, 110, 86)
            pdf.cell(0, 6, f"{edad}  -  {proc}", ln=True)
            pdf.set_font("Arial", size=9)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(0, 5, f"   {obj}", ln=True)
            pdf.ln(1)

    # ── LÍNEA SEPARADORA GRIS ─────────────────────────────────────
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # ── AVISO LEGAL ───────────────────────────────────────────────
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 100, 0)
    pdf.multi_cell(0, 5,
        "IMPORTANTE: Este informe es una orientacion de apoyo, basada en imagenes fotograficas. "
        "No constituye un diagnostico medico definitivo. "
        "Es fundamental una evaluacion clinica completa y multidisciplinar por parte del equipo "
        "de FISULAB mediante evaluacion presencial completa."
    )
    pdf.ln(5)

    # ── CONTENIDO DEL DIAGNÓSTICO ─────────────────────────────────
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(30, 30, 30)
    texto_limpio = resultado_texto.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 6, texto_limpio)
    pdf.ln(8)

    # ── PIE DE PÁGINA ─────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_draw_color(74, 140, 40)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5,
             f"FISULAB · IA PARA APOYO DIAGNOSTICO CLINICO · "
             f"Generado el {time.strftime('%d/%m/%Y')} · Pagina {pdf.page_no()}",
             align="C")

    return bytes(pdf.output())


# ── FUNCIÓN LOGO ──────────────────────────────────────────────────────────────
def get_logo_base64(path="fisulab.png"):
    """Convierte el logo a texto base64 para usarlo en HTML inline."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# ── ESTADO DE SESIÓN ─────────────────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "datos_paciente" not in st.session_state:
    st.session_state.datos_paciente = {}
if "datos_ia" not in st.session_state:
    st.session_state.datos_ia = {}

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
col_izq, col_centro, col_der = st.columns([1.2, 2.5, 1.1])

# ════════════════════════════════════════════════════════════
# COLUMNA IZQUIERDA
# ════════════════════════════════════════════════════════════
with col_izq:
    st.markdown("#### 👤 Datos del paciente")
    paciente_id   = st.text_input("Nombre / ID", placeholder="Paciente 2024-112")
    paciente_edad = st.text_input("Edad", placeholder="Ej: 3 meses")
    paciente_sexo = st.selectbox("Sexo", ["No especificado", "Femenino", "Masculino"])
    tipo_imagen   = st.selectbox("Tipo de imagen", ["Fotografía frontal", "Fotografía lateral",
                                                     "Intraoral", "Radiografía panorámica"])

    st.divider()

    st.markdown("#### 📷 Imagen clínica")
    imagen_file = st.file_uploader(
        "Cargar imagen",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )

    if imagen_file:
        imagen_pil = Image.open(imagen_file)
        st.image(imagen_pil, caption="Vista previa", use_container_width=True)

    analizar = st.button(
        "🔬 Analizar con IA",
        use_container_width=True,
        type="primary",
        disabled=(not imagen_file or not API_KEY)
    )

    if not API_KEY:
        st.caption("⚠️ API Key no configurada. Agrégala en Streamlit Secrets.")
    if not imagen_file:
        st.caption("⚠️ Carga una imagen para continuar.")

    st.divider()

    if st.button("🆕 Nuevo paciente", use_container_width=True):
        st.session_state.resultado    = None
        st.session_state.datos_paciente = {}
        st.session_state.datos_ia     = {}
        st.rerun()

# ════════════════════════════════════════════════════════════
# LÓGICA DE ANÁLISIS
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
- Tipo de imagen: {tipo_imagen}
"""
        prompt_completo = contexto_paciente + "\n\n" + PROMPT_MEDICO

        mime_map = {
            "JPEG": "image/jpeg", "JPG": "image/jpeg",
            "PNG":  "image/png",  "WEBP": "image/webp"
        }
        mime_type = mime_map.get(fmt.upper(), "image/jpeg")

        with col_centro:
            with st.spinner("Analizando imagen con IA... esto puede tomar unos segundos."):
                response = model.generate_content([
                    prompt_completo,
                    {"mime_type": mime_type, "data": imagen_bytes}
                ])
                st.session_state.resultado = response.text
                st.session_state.datos_paciente = {
                    "id":   paciente_id or f"Caso {len(st.session_state.historial)+1}",
                    "edad": paciente_edad or "No especificada",
                    "sexo": paciente_sexo,
                }

                # Parsear JSON estructurado de la respuesta
                datos_ia = parsear_json_ia(response.text)
                st.session_state.datos_ia = datos_ia

                # Complejidad desde el JSON — ya no depende de búsqueda en texto libre
                comp_map = {"MUY ALTA": "alta", "MEDIA": "media", "BAJA": "baja"}
                comp = comp_map.get(datos_ia["complejidad"], "baja")

                st.session_state.historial.insert(0, {
                    "nombre":      paciente_id or f"Caso {len(st.session_state.historial)+1}",
                    "fecha":       time.strftime("%d %b %Y"),
                    "complejidad": comp
                })

    except Exception as e:
        with col_centro:
            st.error(f"❌ Error al conectar con la API: {str(e)}")

# ════════════════════════════════════════════════════════════
# COLUMNA CENTRO — Panel de resultados
# ════════════════════════════════════════════════════════════
with col_centro:

    if st.session_state.resultado is None:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:400px;color:#adb5bd;text-align:center;">
            <div style="font-size:48px;">🔬</div>
            <div style="font-size:16px;font-weight:500;color:#6c757d">
                Sin análisis aún
            </div>
            <div style="font-size:13px;margin-top:8px;color:#adb5bd">
                Carga una imagen y presiona <strong>Analizar con IA</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        resultado_texto = st.session_state.resultado
        datos_ia        = st.session_state.datos_ia

        # ── Datos dinámicos del JSON parseado ───────────────────────
        clasificacion    = datos_ia.get("clasificacion_principal", "No determinada")
        sistema          = datos_ia.get("sistema", "—")
        complejidad      = datos_ia.get("complejidad", "BAJA")
        confianza_modelo = datos_ia.get("confianza_principal", 0)
        diferenciales    = datos_ia.get("diferenciales", [])
        cronograma       = datos_ia.get("cronograma", [])

        color_map  = {"MUY ALTA": "#A32D2D", "MEDIA": "#854F0B", "BAJA": "#3B6D11"}
        color_comp = color_map.get(complejidad, "#3B6D11")

        st.markdown("### 📌 Resumen clínico IA")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Clasificación probable</div>
                <div class="metric-value" style="font-size:15px; line-height:1.3">{clasificacion}</div>
                <div class="metric-label">{sistema}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Complejidad estimada</div>
                <div class="metric-value" style="color:{color_comp}">
                    {complejidad}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Confianza del modelo</div>
                <div style="width:100%;height:8px;background:#e9ecef;border-radius:6px;margin:6px 0;">
                    <div style="width:{confianza_modelo}%;
                                height:8px;background:#1d7af3;border-radius:6px;"></div>
                </div>
                <div style="font-weight:700;color:#1d7af3">
                    {confianza_modelo} %
                </div>
                <div class="metric-label">
                    Resultado orientativo · Validación clínica requerida
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── Clasificación diferencial — dinámica ──────────────────────
        st.markdown("### 🔬 Clasificación diferencial")

        if diferenciales:
            for d in diferenciales:
                nombre    = d["nombre"]
                prob      = d["probabilidad"]
                pct_float = max(0.0, min(1.0, prob / 100))
                st.markdown(f"**{nombre}** — {prob}%")
                st.progress(pct_float)
        else:
            st.caption("No se encontraron diagnósticos diferenciales en la respuesta.")

        st.divider()

        # ── Cronograma orientativo — dinámico ─────────────────────────
        st.markdown("### 🗓️ Cronograma orientativo")

        if cronograma:
            for paso in cronograma:
                st.markdown(f"""
                <div style="border-left:3px solid #0F6E56; padding-left:12px; margin-bottom:10px">
                    <strong>{paso['edad']}</strong><br>
                    {paso['procedimiento']}<br>
                    <span style="color:#6c757d;font-size:12px">{paso['objetivo']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No se encontró cronograma en la respuesta.")

        st.divider()

        st.markdown("### 📄 Informe completo")
        with st.container(height=400):
            st.markdown(resultado_texto)

        # PDF con todos los datos dinámicos incluyendo cronograma
        pdf_bytes = generar_pdf(
            paciente_id or "Caso IA",
            paciente_edad or "No especificada",
            paciente_sexo,
            resultado_texto,
            clasificacion,
            complejidad,
            confianza_modelo,
            cronograma,
        )

        st.download_button(
            "📄 Exportar PDF clínico",
            data=pdf_bytes,
            file_name=f"fisulab_{time.strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("""
        <div class="disclaimer">
            <strong>⚠️ Aviso importante:</strong>
            Este análisis es una orientación basada en imagen.
            No constituye diagnóstico médico definitivo.
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# COLUMNA DERECHA — Historial y estadísticas
# ════════════════════════════════════════════════════════════
with col_der:
    tab1, tab2 = st.tabs(["📁 Historial", "📊 Estadísticas"])

    with tab1:
        st.markdown("")
        if not st.session_state.historial:
            st.caption("Aún no hay casos analizados.")
        else:
            badge_map = {
                "alta":  '<span class="badge-alta">Complejidad alta</span>',
                "media": '<span class="badge-media">Complejidad media</span>',
                "baja":  '<span class="badge-baja">Complejidad baja</span>',
            }
            for caso in st.session_state.historial[:8]:
                badge = badge_map.get(caso["complejidad"], "")
                st.markdown(f"""
                <div class="caso-card">
                    <div class="caso-nombre">🗂️ {caso['nombre']}</div>
                    <div class="caso-fecha">📅 {caso['fecha']}</div>
                    <div style="margin-top:6px">{badge}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.markdown("")
        total  = len(st.session_state.historial)
        altas  = sum(1 for c in st.session_state.historial if c["complejidad"] == "alta")
        medias = sum(1 for c in st.session_state.historial if c["complejidad"] == "media")
        bajas  = sum(1 for c in st.session_state.historial if c["complejidad"] == "baja")

        st.metric("Total de casos", total)
        st.metric("Complejidad alta",  altas)
        st.metric("Complejidad media", medias)
        st.metric("Complejidad baja",  bajas)

        if total > 0:
            st.divider()
            tipo_frecuente = max(
                [("Alta", altas), ("Media", medias), ("Baja", bajas)],
                key=lambda x: x[1]
            )
            st.markdown(f"""
            <div style="background:#E1F5EE;border-radius:8px;padding:10px 12px;">
                <div style="font-size:13px;font-weight:600;color:#085041">Complejidad más frecuente</div>
                <div style="font-size:12px;color:#0F6E56;margin-top:4px">
                    {tipo_frecuente[0]} · {tipo_frecuente[1]} caso(s)
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── PIE DE PÁGINA ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#adb5bd;font-size:12px;padding:8px 0;">
    FISULAB · IA Clínica · Proyecto académico — Especialización en Datos e IA · 2026<br>
    <span style="color:#dc3545">Este sistema es experimental. No usar como único criterio diagnóstico.</span>
</div>
""", unsafe_allow_html=True)

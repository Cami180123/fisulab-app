import streamlit as st
import google.generativeai as genai
import os
from pathlib import Path
from fpdf import FPDF
from datetime import datetime

# ── CONFIGURACIÓN ──────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY", "PEGA_TU_API_KEY_AQUI")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ── PROMPT MÉDICO ──────────────────────────────────────────────
PROMPT_MEDICO = """
Eres un asistente de apoyo diagnóstico especializado en cirugía plástica y reconstructiva
pediátrica, con énfasis en labio y paladar hendido (fisuras labiopalatinas).

Analiza la imagen proporcionada y genera un informe clínico estructurado con el siguiente formato:

Paciente pediátrico o adulto (si la edad no se proporciona, indícalo como la edad no se proporciona).
Evaluación basada únicamente en imágenes; no hay historia clínica completa.
La información generada es para orientación y debe ser validada por un equipo médico multidisciplinar

## ANÁLISIS INICIAL
Describe primero lo que OBSERVAS objetivamente en la(s) imagen(es):
   - Continuidad del labio superior (unilateral/bilateral, completo/incompleto).
   - Afectación del reborde alveolar.
   - Afectación del paladar duro y/o blando.
   - Simetría nasal y deformidad asociada.
   - Calidad y limitaciones de la imagen (ángulo, resolución, iluminación).

## 1. CLASIFICACIÓN CLÍNICA PROBABLE DEL CASO
Identifica cuál de estas categorías corresponde:
- Labio Normal (sin hendidura)
- Labio Leporino (LL) Unilateral Incompleto: hendidura parcial que no llega a la nariz
- Labio Leporino (LL) Unilateral Completo: hendidura total hasta la nariz, un solo lado
- Labio Leporino (LL) Bilateral: hendidura en ambos lados del labio
- Labio y Paladar Hendido: compromiso de labio y paladar
- No determinable (imagen insuficiente)

## 2. CARACTERÍSTICAS CLÍNICAS OBSERVADAS
Describe brevemente los hallazgos visuales que justifican la clasificación.

## 3. PRESUNTO DIAGNÓSTICO
Nombre técnico del diagnóstico según clasificación de Veau o Kernahan.

## 4. PRÓNOSTICO QUIRÚRGICO/PLAN DE TRATAMIENTO ORIENTATIVO
Estima el número aproximado total típico de intervenciones a lo largo del crecimiento y
lista las intervenciones quirúrgicas recomendadas en orden cronológico:
Tabla con:
| Nombre del procedimiento | Número estimado de intervenciones de ese tipo | Objetivo |

## 5. CRONOGRAMA POR RANGO DE EDAD
Tabla con:
| Intervención | Rango de edad recomendado | Justificación |

## 6. NIVEL DE COMPLEJIDAD
Califica:
si el número de intervenciones es menor a dos intervenciones, el nivel de complejidad es baja
si el número de intervenciones es entre tres intervenciones y cinco intervenciones, es complejidad media
si es mayor a cinco intervenciones es de complejidad muy Alta

Justifica brevemente el nivel de complejidad del tratamiento según
- Extensión de la hendidura.
- Unilateral vs bilateral.
- Compromiso alveolar y nasal.
- Necesidad de ortodoncia prolongada o cirugía ortognática.
- Riesgo funcional (habla, alimentación, audición).

## 7. CONSIDERACIONES ADICIONALES
Menciona si se requiere: ortopedia prequirúrgica, fonoaudiología, ortodoncia, psicología u otro.

## 8. OTROS FACTORES Y ADVERTENCIAS
Señala qué datos faltan (edad, antecedentes, exploración funcional).
Explica cómo esos datos podrían cambiar el pronóstico.

---
IMPORTANTE: este análisis se basa exclusivamente en la(s) imagen(es) proporcionada(s)
y es una guía de apoyo para el médico tratante. No constituye un diagnóstico médico definitivo.
Es fundamental una evaluación clínica completa y multidisciplinar por parte del equipo de FISULAB.
No reemplaza el juicio clínico profesional ni el examen físico directo del paciente.
"""

# ── FUNCIÓN: cargar imagen ─────────────────────────────────────
def cargar_imagen(archivo_subido):
    extension = Path(archivo_subido.name).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime_type = mime_map.get(extension, "image/jpeg")
    datos = archivo_subido.read()
    return {"mime_type": mime_type, "data": datos}

# ── FUNCIÓN: generar PDF ───────────────────────────────────────
def generar_pdf(resultados):
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    for r in resultados:
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "FISULAB - Informe de Apoyo Diagnostico", ln=True, align="C")
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Paciente: {r['nombre_paciente']}  |  Edad: {r['edad_paciente']}  |  Fecha: {datetime.today().strftime('%d/%m/%Y')}", ln=True)
        pdf.cell(0, 8, f"Archivo: {r['nombre']}", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "I", 9)
        pdf.multi_cell(0, 5, "AVISO: Este informe es un apoyo de orientacion para el medico tratante. No constituye un diagnostico medico definitivo.")
        pdf.ln(6)
        pdf.set_font("Arial", size=11)
        if r["error"]:
            pdf.multi_cell(0, 6, f"ERROR: {r['error']}")
        else:
            pdf.multi_cell(0, 6, r["diagnostico"])
    return bytes(pdf.output())

# ── CONFIGURACIÓN DE PÁGINA ────────────────────────────────────
st.set_page_config(page_title="Fisulab - Apoyo Diagnóstico", page_icon="🏥")

# ── SESSION STATE: guarda el estado entre interacciones ────────
if "reiniciar" not in st.session_state:
    st.session_state.reiniciar = False

# Si se pidió reiniciar, limpia el contador para forzar nuevos widgets
if st.session_state.reiniciar:
    st.session_state.reiniciar = False
    st.session_state.paciente_id = st.session_state.get("paciente_id", 0) + 1

if "paciente_id" not in st.session_state:
    st.session_state.paciente_id = 0

# ── ENCABEZADO + BOTÓN NUEVO PACIENTE ─────────────────────────
col_titulo, col_boton = st.columns([3, 1])
with col_titulo:
    st.title("🏥 Fisulab — Apoyo de Diagnóstico con IA")
    st.caption("Herramienta de orientación clínica. No reemplaza el criterio médico profesional.")
with col_boton:
    st.write("")
    st.write("")
    if st.button("🆕 Nuevo paciente", use_container_width=True):
        st.session_state.reiniciar = True
        st.rerun()

st.divider()

# ── FORMULARIO (usa paciente_id como key para resetear) ───────
pid = st.session_state.paciente_id

col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre del paciente", placeholder="Ej: Juan Pérez", key=f"nombre_{pid}")
with col2:
    edad = st.text_input("Edad del paciente", placeholder="Ej: 3 meses", key=f"edad_{pid}")

fotos = st.file_uploader(
    "Sube las fotografías del paciente",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    help="Puedes seleccionar varias fotos a la vez",
    key=f"fotos_{pid}"
)

if fotos:
    st.write(f"📁 {len(fotos)} imagen(es) cargada(s):")
    cols = st.columns(min(len(fotos), 4))
    for i, foto in enumerate(fotos):
        with cols[i % 4]:
            st.image(foto, caption=foto.name, use_container_width=True)

st.divider()

# ── BOTÓN GENERAR ──────────────────────────────────────────────
if fotos and st.button("🔍 Generar informes", type="primary", use_container_width=True):

    resultados = []
    progreso = st.progress(0, text="Iniciando análisis...")

    for i, foto in enumerate(fotos):
        progreso.progress(i / len(fotos), text=f"Analizando {foto.name}...")
        with st.expander(f"📷 {foto.name}", expanded=True):
            try:
                imagen = cargar_imagen(foto)
                response = model.generate_content([PROMPT_MEDICO, imagen])
                diagnostico = response.text
                st.markdown(diagnostico)
                resultados.append({
                    "nombre": foto.name,
                    "nombre_paciente": nombre or "No especificado",
                    "edad_paciente": edad or "No especificada",
                    "diagnostico": diagnostico,
                    "error": None
                })
                st.success("✅ Informe generado")
            except Exception as e:
                msg = str(e)
                st.error(f"❌ Error: {msg}")
                resultados.append({
                    "nombre": foto.name,
                    "nombre_paciente": nombre or "No especificado",
                    "edad_paciente": edad or "No especificada",
                    "diagnostico": None,
                    "error": msg
                })

    progreso.progress(1.0, text="¡Análisis completado!")
    exitosas = sum(1 for r in resultados if not r["error"])
    st.divider()
    st.write(f"**Resumen:** {exitosas} de {len(resultados)} imágenes procesadas correctamente.")

    if exitosas > 0:
        pdf_bytes = generar_pdf(resultados)
        st.download_button(
            label="📄 Descargar todos los informes en PDF",
            data=pdf_bytes,
            file_name=f"informes_fisulab_{nombre or 'paciente'}_{datetime.today().strftime('%d%m%Y')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

elif not fotos:
    st.info("👆 Sube una o varias fotografías para comenzar el análisis.")

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

# ── PROMPT MÉDICO (exactamente igual que en tu Colab) ──────────
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

## 4. PRÓNOSTICO QURÚRGICO/PLAN DE TRATAMIENTO ORIENTATIVO
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
y demás aspectos que consideres relevantes.

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

# ── FUNCIÓN: cargar imagen (igual que en tu Colab) ─────────────
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

# ── FUNCIÓN: generar PDF ────────────────────────────────────────
def generar_pdf(nombre, edad, diagnostico):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "FISULAB - Informe de Apoyo Diagnostico", ln=True, align="C")
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Paciente: {nombre}  |  Edad: {edad}  |  Fecha: {datetime.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, "AVISO: Este informe es un apoyo de orientacion para el medico tratante. No constituye un diagnostico medico definitivo. Es fundamental una evaluacion clinica completa y multidisciplinar.")
    pdf.ln(6)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, diagnostico)

    return bytes(pdf.output())

# ── INTERFAZ STREAMLIT ──────────────────────────────────────────
st.set_page_config(page_title="Fisulab - Apoyo Diagnóstico", page_icon="🏥")

st.title("🏥 Fisulab — Apoyo de Diagnóstico con IA")
st.caption("Herramienta de orientación clínica. No reemplaza el criterio médico profesional.")
st.divider()

col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre del paciente", placeholder="Ej: Juan Pérez")
with col2:
    edad = st.text_input("Edad del paciente", placeholder="Ej: 3 meses")

foto = st.file_uploader(
    "Sube la fotografía del paciente",
    type=["jpg", "jpeg", "png", "webp"],
    help="Formatos aceptados: JPG, PNG, WEBP"
)

if foto:
    st.image(foto, caption="Imagen cargada", width=300)

st.divider()

if foto and st.button("🔍 Generar informe", type="primary", use_container_width=True):
    with st.spinner("Analizando imagen con IA... esto puede tomar unos segundos."):
        try:
            imagen = cargar_imagen(foto)
            response = model.generate_content([PROMPT_MEDICO, imagen])
            diagnostico = response.text

            st.success("✅ Informe generado correctamente")
            st.divider()
            st.markdown(diagnostico)
            st.divider()

            # Botón de descarga PDF
            pdf_bytes = generar_pdf(nombre or "No especificado", edad or "No especificada", diagnostico)
            nombre_archivo = f"informe_fisulab_{nombre.replace(' ', '_') if nombre else 'paciente'}.pdf"
            st.download_button(
                label="📄 Descargar informe en PDF",
                data=pdf_bytes,
                file_name=nombre_archivo,
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Error al procesar la imagen: {str(e)}")
            st.info("Verifica que la API key de Gemini esté configurada correctamente.")

elif not foto:
    st.info("👆 Sube una fotografía para comenzar el análisis.")

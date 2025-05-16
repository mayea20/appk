import streamlit as st
from PIL import Image
import pytesseract
import re
import pandas as pd

st.set_page_config(page_title="App de Finanzas - Análisis de Facturas", layout="centered")
st.title("🧾 App de Finanzas - Análisis de Facturas")

MAX_SIZE_MB = 5
MAX_SIZE = MAX_SIZE_MB * 1024 * 1024
MAX_IMG_WIDTH = 1200

with st.expander("ℹ️ Consejos para obtener buenos resultados", expanded=False):
    st.markdown("""
- Sube fotos claras, centradas y bien iluminadas de tu factura.
- Si la foto pesa mucho, recórtala o haz captura de pantalla antes de subirla.
- Si el resultado no es bueno, prueba con otra foto o ajusta el enfoque.
""")

uploaded_file = st.file_uploader(
    f"Sube una imagen de factura (máx. {MAX_SIZE_MB}MB)", 
    type=["png", "jpg", "jpeg"]
)

def clasificar_producto(nombre):
    nombre = nombre.lower()
    if "kg" in nombre or "g" in nombre:
        return "por gramo"
    elif "unidad" in nombre or "u" in nombre:
        return "por unidad"
    else:
        return "desconocido"

if uploaded_file:
    if uploaded_file.size > MAX_SIZE:
        st.error(f"La imagen es muy grande. Sube una de menos de {MAX_SIZE_MB} MB.")
    else:
        image = Image.open(uploaded_file)
        if image.width > MAX_IMG_WIDTH:
            ratio = MAX_IMG_WIDTH / image.width
            new_size = (MAX_IMG_WIDTH, int(image.height * ratio))
            image = image.resize(new_size)
        
        st.image(image, caption='Factura cargada', use_container_width=True)

        with st.spinner("Extrayendo texto con OCR..."):
            try:
                text = pytesseract.image_to_string(image, lang='spa')
            except Exception as e:
                st.error("Error de OCR: " + str(e))
                st.stop()

        st.subheader("Texto detectado:")
        st.text(text)

        fecha = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text)
        st.write("📅 Fecha:", fecha.group() if fecha else "No encontrada")

        lineas = [l.strip() for l in text.split('\n') if l.strip()]
        lugar = lineas[0] if lineas else "No encontrado"
        st.write("📍 Lugar:", lugar)

        st.subheader("🛒 Productos detectados:")

        productos = []
        for linea in lineas:
            match = re.search(r"([A-Za-zÁÉÍÓÚáéíóúñÑ\s\(\)\-\.]+?)\s+(\d{1,4}[.,]\d{2})\s*€?", linea)
            if match:
                nombre = match.group(1).strip()
                precio_str = match.group(2).replace(",", ".")
                try:
                    precio = float(precio_str)
                except Exception:
                    continue
                if 0.05 < precio < 1000 and re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]", nombre):
                    tipo = clasificar_producto(nombre)
                    productos.append({
                        "Producto": nombre,
                        "Precio (€)": precio,
                        "Tipo": tipo
                    })

        if productos:
            df = pd.DataFrame(productos)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.warning("Ningún producto encontrado con un precio válido. Revisa el texto detectado arriba y prueba con otra imagen si es posible.")

        st.download_button(
            label="Descargar texto detectado",
            data=text,
            file_name="factura_ocr.txt",
            mime="text/plain"
        )

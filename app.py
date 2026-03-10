import streamlit as st
import requests
import os

# Configuración de la página
st.set_page_config(page_title="Mi Generador Seedream", layout="centered")

# --- SEGURIDAD ---
# Esto crea un login simple para que solo tú entres
password_correct = st.sidebar.text_input("Contraseña de acceso", type="password")
if password_correct != "2525Nicolas.": # Cambia esto por la tuya
    st.error("Por favor, introduce la contraseña correcta en el menú lateral.")
    st.stop()

st.title("🎨 Mi Estudio Privado: Seedream 5.0 Lite")
st.markdown("Genera imágenes exclusivas sin que nadie más las vea.")

# --- INTERFAZ ---
prompt = st.text_area("Describe tu imagen:", placeholder="Un gato cyberpunk en las calles de Medellín...")
col1, col2 = st.columns(2)
with col1:
    aspect_ratio = st.selectbox("Formato", ["1:1", "16:9", "9:16", "4:3"])
with col2:
    quality = st.select_slider("Calidad/Pasos", options=["Baja", "Media", "Alta"])

# --- GENERACIÓN ---
if st.button("🚀 Generar Imagen Ahora"):
    if not prompt:
        st.warning("Escribe algo primero.")
    else:
        with st.spinner("Seedream está soñando tu imagen..."):
            try:
                # Aquí conectamos con el proveedor de la API (ejemplo: Wavespeed o Segmind)
                payload = {
                    "model": "seedream-5-lite",
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "private": True  # IMPORTANTE: Indica que no sea pública
                }
                
                headers = {
                    "Authorization": f"Bearer {st.secrets['SEEDREAM_API_KEY']}",
                    "Content-Type": "application/json"
                }

                # Llamada real a la API
                response = requests.post("https://api.wavespeed.ai/v1/generate", json=payload, headers=headers)
                data = response.json()
                
                # Mostrar resultado
                image_url = data['output_url']
                st.image(image_url, caption="Generado con Seedream 5.0 Lite", use_column_width=True)
                
                # Botón de descarga directa
                st.download_button("Descargar Imagen", requests.get(image_url).content, "imagen_generada.png")

            except Exception as e:
                st.error(f"Hubo un error: {e}")

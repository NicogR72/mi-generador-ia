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

import streamlit as st
import requests

st.set_page_config(page_title="Mi Estudio Privado", layout="centered")

# --- SEGURIDAD ---
password_correct = st.sidebar.text_input("Contraseña de acceso", type="password")
if password_correct != "TU_CONTRASEÑA_AQUI": # <--- CAMBIA ESTO
    st.error("Introduce la contraseña.")
    st.stop()

st.title("🎨 Editor de Medias: Seedream 5.0 Lite")

# --- INTERFAZ DE SUBIDA ---
st.markdown("### 1. Sube la foto original")
foto_original = st.file_uploader("Sube la imagen de tus medias (Adidas, etc.)", type=["jpg", "png", "jpeg"])

if foto_original:
    st.image(foto_original, caption="Foto cargada", width=300)

st.markdown("### 2. Describe el cambio")
prompt = st.text_area("Ejemplo: 'Change the background to a minimalist studio and enhance textures'", 
                     placeholder="Escribe aquí tus instrucciones...")

# --- GENERACIÓN ---
if st.button("🚀 Iniciar Edición Mágica"):
    if not foto_original or not prompt:
        st.warning("Necesitas subir una foto y escribir un prompt.")
    else:
        with st.spinner("Subiendo imagen y editando..."):
            try:
                # PASO A: Subir tu foto a los servidores de Fal para obtener un link
                headers_upload = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}"}
                files = {"file": foto_original.getvalue()}
                upload_res = requests.post("https://fal.run/fal-ai/upload/image", headers=headers_upload, files=files)
                url_de_tu_foto = upload_res.json()["url"]

                # PASO B: Enviar la instrucción de edición
                api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                payload = {
                    "prompt": prompt,
                    "image_urls": [url_de_tu_foto] # <--- ¡Aquí enviamos tu foto!
                }
                
                headers = {
                    "Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}",
                    "Content-Type": "application/json"
                }

                response = requests.post(api_url, json=payload, headers=headers)
                data = response.json()
                
                if "images" in data:
                    image_url = data['images'][0]['url']
                    st.image(image_url, caption="¡Resultado final!", use_column_width=True)
                    st.download_button("📥 Guardar Foto Editada", requests.get(image_url).content, "edicion_ia.png")
                else:
                    st.error(f"Error: {data}")

            except Exception as e:
                st.error(f"Error técnico: {e}")

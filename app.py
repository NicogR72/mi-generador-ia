import streamlit as st
import requests

# Configuración inicial
st.set_page_config(page_title="Mi Estudio Privado", layout="centered")

# --- 1. SEGURIDAD (Solo una vez) ---
st.sidebar.title("Configuración")
password_correct = st.sidebar.text_input("Contraseña de acceso", type="password", key="pass_input")

if password_correct != "TU_CONTRASEÑA_AQUI": # <--- CAMBIA ESTO POR TU CLAVE
    st.error("Por favor, introduce la contraseña en el menú lateral.")
    st.stop()

# --- 2. INTERFAZ ---
st.title("🎨 Editor Pro: Seedream 5.0 Lite")
st.markdown("Sube una foto de tus medias y descríbele a la IA qué quieres cambiar.")

foto_original = st.file_uploader("Sube tu imagen (Adidas, etc.)", type=["jpg", "png", "jpeg"], key="uploader")

if foto_original:
    st.image(foto_original, caption="Foto cargada con éxito", width=300)

prompt = st.text_area("Instrucciones para la IA:", 
                     placeholder="Ej: 'Make the socks look more premium, change background to a clean white studio'",
                     key="prompt_input")

# --- 3. PROCESAMIENTO ---
if st.button("🚀 Iniciar Edición", key="btn_generar"):
    if not foto_original or not prompt:
        st.warning("Asegúrate de haber subido una foto y escrito un prompt.")
    else:
        with st.spinner("Procesando imagen con Seedream..."):
            try:
                # A. Subir la imagen a Fal para tener un link
                headers_api = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}"}
                files = {"file": foto_original.getvalue()}
                upload_res = requests.post("https://fal.run/fal-ai/upload/image", headers=headers_api, files=files)
                url_de_tu_foto = upload_res.json()["url"]

                # B. Llamar al modelo de edición
                api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                payload = {
                    "prompt": prompt,
                    "image_urls": [url_de_tu_foto]
                }
                
                response = requests.post(api_url, json=payload, headers=headers_api)
                data = response.json()
                
                if "images" in data:
                    image_url = data['images'][0]['url']
                    st.image(image_url, caption="¡Resultado final!", use_column_width=True)
                    st.download_button("📥 Descargar Resultado", requests.get(image_url).content, "editada.png")
                else:
                    st.error(f"Error de la API: {data}")

            except Exception as e:
                st.error(f"Error técnico: {e}")

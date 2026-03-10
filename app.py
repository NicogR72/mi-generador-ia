import streamlit as st
import requests

st.set_page_config(page_title="Mi Estudio Privado", layout="centered")

# --- 1. SEGURIDAD ---
st.sidebar.title("Configuración")
password_correct = st.sidebar.text_input("Contraseña de acceso", type="password", key="pass_input")

if password_correct != "TU_CONTRASEÑA_AQUI": # <--- CAMBIA ESTO
    st.error("Por favor, introduce la contraseña.")
    st.stop()

# --- 2. INTERFAZ ---
st.title("🎨 Editor Pro: Seedream 5.0 Lite")

foto_original = st.file_uploader("Sube tu imagen de las medias", type=["jpg", "png", "jpeg"], key="uploader")

if foto_original:
    st.image(foto_original, caption="Imagen para editar", width=300)

prompt = st.text_area("¿Qué quieres que haga la IA?", 
                     placeholder="Ej: 'Make it look professional, clean white background'",
                     key="prompt_input")

# --- 3. PROCESAMIENTO ---
if st.button("🚀 Iniciar Edición", key="btn_generar"):
    if not foto_original or not prompt:
        st.warning("Falta la foto o el prompt.")
    else:
        with st.spinner("Paso 1: Subiendo imagen..."):
            try:
                # A. SUBIDA DE IMAGEN
                headers_api = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}"}
                files = {"file": foto_original.getvalue()}
                
                # Usamos el endpoint oficial de subida de Fal
                upload_res = requests.post("https://fal.run/fal-ai/upload/image", headers=headers_api, files=files)
                
                if upload_res.status_code != 200:
                    st.error(f"Error al subir la imagen (Código {upload_res.status_code})")
                    st.write(upload_res.json()) # Esto nos dirá el error real
                    st.stop()
                
                url_de_tu_foto = upload_res.json().get("url")
                if not url_de_tu_foto:
                    st.error("No se pudo obtener la URL de la imagen. Respuesta:")
                    st.write(upload_res.json())
                    st.stop()

                # B. EDICIÓN CON SEEDREAM
                st.info("Imagen subida. Paso 2: Editando con Seedream...")
                api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                payload = {
                    "prompt": prompt,
                    "image_urls": [url_de_tu_foto]
                }
                
                response = requests.post(api_url, json=payload, headers=headers_api)
                data = response.json()
                
                if "images" in data:
                    image_url = data['images'][0]['url']
                    st.image(image_url, caption="¡Edición completada!", use_column_width=True)
                else:
                    st.error("La IA no pudo procesar la imagen:")
                    st.write(data)

            except Exception as e:
                st.error(f"Error inesperado: {str(e)}")

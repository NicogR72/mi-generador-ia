import streamlit as st
import requests
import base64

st.set_page_config(page_title="Mi Estudio Privado", layout="centered")

# --- 1. SEGURIDAD ---
st.sidebar.title("Configuración")
password_correct = st.sidebar.text_input("Contraseña de acceso", type="password", key="pass_input")

if password_correct != "2525Nico.": # <--- CAMBIA ESTO POR TU CLAVE
    st.error("Por favor, introduce la contraseña.")
    st.stop()

# --- 2. INTERFAZ ---
st.title("🎨 Editor Pro: Seedream 5.0 Lite")
st.markdown("Edición profesional de producto sin intermediarios.")

foto_original = st.file_uploader("Sube tu imagen de las medias", type=["jpg", "png", "jpeg"], key="uploader")

if foto_original:
    st.image(foto_original, caption="Imagen original", width=300)

prompt = st.text_area("¿Qué debe hacer la IA?", 
                     placeholder="Ej: 'Clean professional studio background, enhance cotton texture'",
                     key="prompt_input")

# --- 3. PROCESAMIENTO ---
if st.button("🚀 Iniciar Edición", key="btn_generar"):
    if not foto_original or not prompt:
        st.warning("Falta la foto o el prompt.")
    else:
        with st.spinner("Transformando tu imagen..."):
            try:
                # PASO A: Convertir la imagen a Base64 (Texto)
                # Esto evita el error 404 de subida
                img_bytes = foto_original.getvalue()
                encoded_string = base64.b64encode(img_bytes).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{encoded_string}"

                # PASO B: Llamar a Seedream directamente
                api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                
                headers = {
                    "Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "prompt": prompt,
                    "image_urls": [data_uri] # Enviamos la imagen como datos puros
                }

                response = requests.post(api_url, json=payload, headers=headers)
                data = response.json()
                
                if "images" in data:
                    image_url = data['images'][0]['url']
                    st.image(image_url, caption="¡Resultado final!", use_column_width=True)
                    st.download_button("📥 Descargar", requests.get(image_url).content, "medias_editadas.png")
                else:
                    st.error("La IA respondió con un error:")
                    st.write(data)

            except Exception as e:
                st.error(f"Error técnico inesperado: {str(e)}")

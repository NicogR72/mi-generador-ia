import streamlit as st
import requests
import base64
import cloudinary
import cloudinary.uploader

# --- CONFIGURACIÓN BÁSICA ---
st.set_page_config(page_title="SockEdit Pro Max", layout="wide", page_icon="🧦")

# Configuración Cloudinary
if "CLOUDINARY_CLOUD_NAME" in st.secrets:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"]
    )

if "history" not in st.session_state:
    st.session_state.history = []

# --- 1. SEGURIDAD ---
st.sidebar.title("🔐 Acceso")
password = st.sidebar.text_input("Contraseña", type="password")
if password != "2525Nico.": # <--- CAMBIA ESTO POR TU CLAVE
    st.error("Introduce la clave.")
    st.stop()

st.title("🧦 SockEdit Enterprise")
st.caption("ByteDance Seedream 5.0 Lite + Cloudinary")

tab1, tab2 = st.tabs(["🖌️ Editor Pro", "📂 Archivo Histórico"])

with tab1:
    col_in, col_out = st.columns([1, 1])
    with col_in:
        st.subheader("Configuración")
        foto = st.file_uploader("Subir foto base", type=["jpg", "png", "jpeg"])
        estilo = st.selectbox("Modo de Trabajo", ["Manual", "Fondo Blanco", "Urbano", "Lujo"])
        prompt_usuario = st.text_area("Instrucciones", placeholder="Describe el cambio...")

    with col_out:
        st.subheader("Resultado")
        if st.button("🚀 Renderizar", use_container_width=True):
            if foto and prompt_usuario:
                with st.spinner("Procesando..."):
                    try:
                        # A. Convertir imagen a Base64
                        img_bytes = foto.getvalue()
                        encoded_string = base64.b64encode(img_bytes).decode("utf-8")
                        data_uri = f"data:image/jpeg;base64,{encoded_string}"

                        # B. Construir el Prompt
                        if estilo == "Fondo Blanco":
                            final_prompt = f"Pure white background, e-commerce style, studio lighting. {prompt_usuario}"
                        elif estilo == "Urbano":
                            final_prompt = f"Urban streetwear setting, concrete background, natural light. {prompt_usuario}"
                        elif estilo == "Lujo":
                            final_prompt = f"Luxury cinematic shot, bokeh, high-end lighting. {prompt_usuario}"
                        else:
                            final_prompt = prompt_usuario

                        # C. Llamada a la API de Fal.ai
                        api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                        headers = {
                            "Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "prompt": final_prompt,
                            "image_urls": [data_uri]
                        }

                        response = requests.post(api_url, json=payload, headers=headers)
                        data = response.json()

                        if "images" in data:
                            res_url = data['images'][0]['url']
                            # Guardar en Cloudinary
                            try:
                                upload = cloudinary.uploader.upload(res_url, folder="productos_ia")
                                res_url = upload["secure_url"]
                            except:
                                pass

                            # Mostrar imágenes lado a lado
                            c1, c2 = st.columns(2)
                            with c1: st.image(foto, caption="Original")
                            with c2: st.image(res_url, caption="Editada")
                            
                            st.session_state.history.append({"url": res_url, "txt": final_prompt})
                            st.success("¡Imagen generada con éxito!")
                        else:
                            st.error(f"Error de la IA: {data}")

                    except Exception as e:
                        st.error(f"Error técnico: {e}")
            else:
                st.warning("Sube una foto y escribe una instrucción.")

with tab2:
    if st.session_state.history:
        grid = st.columns(3)
        for idx, item in enumerate(reversed(st.session_state.history)):
            with grid[idx % 3]:
                st.image(item["url"], use_column_width=True)
                st.caption(f"Prompt: {item['txt'][:30]}...")

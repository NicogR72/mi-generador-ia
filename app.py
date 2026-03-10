import streamlit as st
import requests
import base64
import cloudinary
import cloudinary.uploader

# --- CONFIGURACIÓN ---
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

# --- SEGURIDAD ---
st.sidebar.title("🔐 Acceso")
password = st.sidebar.text_input("Contraseña", type="password")
if password != "2525Nico.": # <--- CAMBIA ESTO
    st.error("Introduce la clave.")
    st.stop()

st.title("🧦 SockEdit Enterprise")

tab1, tab2 = st.tabs(["🖌️ Editor Pro", "📂 Archivo Histórico"])

with tab1:
    col_in, col_out = st.columns([1, 1])
    
    with col_in:
        st.subheader("Configuración")
        foto = st.file_uploader("Subir foto base", type=["jpg", "png", "jpeg"])
        estilo = st.selectbox("Estilo", ["Fondo Blanco E-commerce", "Urbano Streetwear", "Lujo Cinematográfico"])
        prompt_extra = st.text_area("Notas", "High quality, professional product shot.")

    with col_out:
        st.subheader("Resultado")
        if st.button("🚀 Renderizar", use_container_width=True):
            if foto:
                with st.spinner("Procesando..."):
                    try:
                        # Base64
                        encoded = base64.b64encode(foto.getvalue()).decode("utf-8")
                        data_uri = f"data:image/jpeg;base64,{encoded}"

                        # API
                        api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                        headers = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}"}
                        payload = {"prompt": f"{estilo} {prompt_extra}", "image_urls": [data_uri]}
                        
                        response = requests.post(api_url, json=payload, headers=headers)
                        res_data = response.json()

                        if "images" in res_data:
                            p_url = res_data['images'][0]['url']
                            
                            # Intentar guardar en Cloudinary si está configurado
                            try:
                                up = cloudinary.uploader.upload(p_url, folder="productos_ia")
                                p_url = up["secure_url"]
                            except:
                                pass # Si Cloudinary falla, usamos el link temporal de Fal

                            # MOSTRAR LADO A LADO (Sin librerías extra)
                            c1, c2 = st.columns(2)
                            with c1: st.image(foto, caption="Antes")
                            with c2: st.image(p_url, caption="Después (IA)")
                            
                            st.session_state.history.append({"final": p_url, "style": estilo})
                        else:
                            st.error(f"Error: {res_data}")
                    except Exception as e:
                        st.error(f"Error: {e}")

with tab2:
    if st.session_state.history:
        grid = st.columns(3)
        for idx, item in enumerate(reversed(st.session_state.history)):
            with grid[idx % 3]:
                st.image(item["final"], use_column_width=True)

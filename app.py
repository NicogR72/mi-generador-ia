import streamlit as st
import requests
import base64
import cloudinary
import cloudinary.uploader

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SockEdit Pro Max", layout="wide", page_icon="🧦")

# Configuración Cloudinary (Baúl Permanente)
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
if password != "2525Nico.": # <--- CAMBIA ESTO
    st.error("Introduce la clave.")
    st.stop()

st.title("🧦 SockEdit Enterprise")
st.caption("Control Total: Presets + Prompt Manual")

tab1, tab2 = st.tabs(["🖌️ Editor Pro", "📂 Archivo Histórico"])

with tab1:
    col_in, col_out = st.columns([1, 1])
    with col_in:
        st.subheader("Configuración")
        foto = st.file_uploader("Subir foto base", type=["jpg", "png", "jpeg"])
        estilo = st.selectbox("Modo de Trabajo", [
            "Manual (Usar solo mi prompt)", 
            "Fondo Blanco E-commerce", 
            "Urbano Streetwear", 
            "Lujo Cinematográfico"
        ])
        prompt_usuario = st.text_area("Tu Prompt / Instrucciones", placeholder="Describe el cambio...")

    with col_out:
        st.subheader("Resultado")
        if st.button("🚀 Renderizar", use_container_width=True):
            if foto and prompt_usuario:
                with st.spinner("Procesando con Seedream 5.0..."):
                    try:
                        # A. Imagen a Base64
                        img_bytes = foto.getvalue()
                        encoded_string = base64.b64encode(img_bytes).decode("utf-8")
                        data_uri = f"data:image/jpeg;base64,{encoded_string}"

                        # B. Lógica de Prompts
                        if estilo == "Manual (Usar solo mi prompt)":
                            final_prompt = prompt_usuario
                        else:
                            estilos_dict = {
                                "Fondo Blanco E-commerce": "Pure white background, e-commerce style, studio lighting.",
                                "Urbano Streetwear": "Concrete background, natural outdoor light, urban style.",
                                "Lujo Cinematográfico": "Dramatic lighting, luxury bokeh background, 8k."
                            }
                            final_prompt = f"{estilos_dict[estilo]} {prompt_usuario}"

                        # C. Petición a la API (Aquí estaba el error de la llave)
                        api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                        headers

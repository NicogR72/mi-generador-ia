import streamlit as st
import requests
import base64
import cloudinary
import cloudinary.uploader
from streamlit_image_comparison import image_comparison

# --- CONFIGURACIÓN PRO ---
st.set_page_config(page_title="SockEdit Pro Max", layout="wide", page_icon="🎨")

# Conectar con tu baúl de Cloudinary
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
if password != "2525Nico.": # <--- PON TU CLAVE AQUÍ
    st.error("Introduce la clave para editar.")
    st.stop()

st.title("🧦 SockEdit Enterprise: Seedream 5.0 Lite")

tab1, tab2 = st.tabs(["🖌️ Editor de Precisión", "📂 Archivo Histórico"])

with tab1:
    col_in, col_out = st.columns([1, 1.2])
    
    with col_in:
        st.subheader("Configuración de Producto")
        foto = st.file_uploader("Subir foto base", type=["jpg", "png", "jpeg"])
        estilo = st.selectbox("Estilo de Renderizado", [
            "Fondo Blanco E-commerce", "Urbano Streetwear", "Lujo Cinematográfico"
        ])
        prompt_extra = st.text_area("Notas de edición", "Mejorar texturas y suavizar sombras.")

    with col_out:
        if st.button("🚀 Renderizar y Guardar", use_container_width=True):
            if foto and prompt_extra:
                with st.spinner("Editando y asegurando en la nube..."):
                    try:
                        # A. Convertir a Base64
                        encoded = base64.b64encode(foto.getvalue()).decode("utf-8")
                        data_uri = f"data:image/jpeg;base64,{encoded}"

                        # B. API Seedream
                        api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                        headers = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}"}
                        
                        estilos = {
                            "Fondo Blanco E-commerce": "Pure white background, e-commerce style, studio lighting.",
                            "Urbano Streetwear": "Concrete background, natural outdoor light, urban style.",
                            "Lujo Cinematográfico": "Dramatic lighting, luxury bokeh background, 8k."
                        }
                        
                        payload = {"prompt": f"{estilos[estilo]} {prompt_extra}", "image_urls": [data_uri]}
                        response = requests.post(api_url, json=payload, headers=headers)
                        res_data = response.json()

                        if "images" in res_data:
                            temp_url = res_data['images'][0]['url']
                            
                            # C. Guardar Permanente en Cloudinary
                            up = cloudinary.uploader.upload(temp_url, folder="productos_ia")
                            p_url = up["secure_url"]

                            # D. Comparador Visual
                            image_comparison(img1=foto, img2=p_url, label1="Original", label2="IA Pro")
                            
                            st.session_state.history.append({"final": p_url, "style": estilo})
                            st.success("✨ Imagen guardada permanentemente.")
                        else:
                            st.error(f"Error IA: {res_data}")
                    except Exception as e:
                        st.error(f"Error: {e}")

with tab2:
    st.subheader("🗄️ Historial Permanente")
    if not st.session_state.history:
        st.info("No hay imágenes en el archivo todavía.")
    else:
        grid = st.columns(3)
        for idx, item in enumerate(reversed(st.session_state.history)):
            with grid[idx % 3]:
                st.image(item["final"], use_column_width=True)
                st.caption(f"Estilo: {item['style']}")

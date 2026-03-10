import streamlit as st
import requests
import base64
import cloudinary
import cloudinary.uploader
from streamlit_image_comparison import image_comparison

# --- CONFIGURACIÓN PRO ---
st.set_page_config(page_title="SockEdit Pro Max", layout="wide", page_icon="🎨")

# Configurar Cloudinary (Tu Baúl Permanente)
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# --- SEGURIDAD ---
if "history" not in st.session_state:
    st.session_state.history = []

password = st.sidebar.text_input("🔑 Acceso Profesional", type="password")
if password != "TU_CONTRASEÑA_AQUI": # <--- CAMBIA ESTO
    st.warning("Panel bloqueado. Introduce tu clave.")
    st.stop()

# --- INTERFAZ ---
st.title("🧦 SockEdit Pro Max: Enterprise Edition")
st.info("Modelo activo: Seedream 5.0 Lite + Almacenamiento Permanente Cloudinary")

tab1, tab2 = st.tabs(["🖌️ Editor de Precisión", "📂 Archivo Histórico"])

with tab1:
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.subheader("Configuración")
        foto = st.file_uploader("Imagen base", type=["jpg", "png", "jpeg"])
        
        estilo = st.selectbox("Estilo de Renderizado", [
            "Pure White E-commerce", 
            "Lifestyle Street", 
            "High-End Luxury",
            "Studio Softbox"
        ])
        
        prompt_extra = st.text_area("Instrucciones de retoque", "Enhance textures and fix shadows.")
        
    with col_output:
        st.subheader("Resultado")
        if st.button("🚀 Ejecutar Renderizado Pro", use_container_width=True):
            if foto:
                with st.spinner("Procesando píxeles..."):
                    try:
                        # 1. Preparar Base64
                        encoded = base64.b64encode(foto.getvalue()).decode("utf-8")
                        data_uri = f"data:image/jpeg;base64,{encoded}"

                        # 2. Llamar a Seedream
                        api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                        headers = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}"}
                        
                        # Prompt dinámico según estilo
                        prompts = {
                            "Pure White E-commerce": "Professional product photography, pure white background, soft shadows, 8k high resolution.",
                            "Lifestyle Street": "Streetwear aesthetic, concrete background, urban lighting, high detail.",
                            "High-End Luxury": "Luxury product shot, silk textures, dramatic lighting, bokeh background.",
                            "Studio Softbox": "Studio lighting, clean setup, minimalist, hyper-realistic."
                        }
                        
                        full_prompt = f"{prompts[estilo]} {prompt_extra}"
                        
                        response = requests.post(api_url, json={"prompt": full_prompt, "image_urls": [data_uri]}, headers=headers)
                        res_data = response.json()

                        if "images" in res_data:
                            temp_url = res_data['images'][0]['url']
                            
                            # 3. GUARDAR PARA SIEMPRE EN CLOUDINARY
                            upload_res = cloudinary.uploader.upload(temp_url, folder="mis_medias")
                            permanent_url = upload_res["secure_url"]

                            # 4. COMPARADOR ANTES/DESPUÉS
                            st.write("### Comparativa (Desliza para ver el cambio)")
                            image_comparison(
                                img1=foto,
                                img2=permanent_url,
                                label1="Original",
                                label2="Editada por IA"
                            )
                            
                            # Guardar en historial
                            st.session_state.history.append({
                                "original": foto,
                                "final": permanent_url,
                                "prompt": full_prompt
                            })
                            
                            st.success("✅ Imagen guardada permanentemente en tu nube.")
                        else:
                            st.error(f"Error IA: {res_data}")
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
            else:
                st.warning("Sube una foto primero.")

with tab2:
    st.header("🗄️ Tu Archivo de Producto")
    if not st.session_state.history:
        st.write("Tu baúl está vacío.")
    else:
        for item in reversed(st.session_state.history):
            with st.expander(f"Edición: {item['prompt'][:50]}..."):
                st.image(item['final'], use_column_width=True)
                st.write(f"**Link permanente:** {item['final']}")

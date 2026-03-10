import streamlit as st
import requests
import base64
from datetime import datetime

# Configuración de página con icono profesional
st.set_page_config(page_title="SockEdit Pro | Seedream 5.0", layout="wide", page_icon="🧦")

# --- 1. SEGURIDAD Y CONFIGURACIÓN ---
if "gallery" not in st.session_state:
    st.session_state.gallery = []

password_correct = st.sidebar.text_input("🔑 Contraseña", type="password")
if password_correct != "2525Nico.": # <--- CAMBIA ESTO
    st.info("Introduce la contraseña para desbloquear el panel profesional.")
    st.stop()

st.sidebar.success("Conectado a Seedream 5.0 Lite")
st.sidebar.markdown("---")
st.sidebar.write(f"📅 Sesión: {datetime.now().strftime('%d/%m/%Y')}")

# --- 2. TABS PROFESIONALES ---
tab1, tab2 = st.tabs(["🚀 Editor de Producto", "🖼️ Galería de Sesión"])

with tab1:
    st.title("🧦 SockEdit Pro")
    st.caption("Impulsado por ByteDance Seedream 5.0 Lite")
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Cargar Producto")
        foto_original = st.file_uploader("Sube la foto base", type=["jpg", "png", "jpeg"])
        if foto_original:
            st.image(foto_original, caption="Original", use_column_width=True)

    with col2:
        st.subheader("2. Ajustes de Edición")
        
        # Selector de color rápido
        color_deseado = st.color_picker("Color de énfasis (Opcional)", "#ffffff")
        
        # Presets profesionales
        preset = st.selectbox("Elegir Estilo (Preset)", [
            "Manual (Usar mi prompt)",
            "Fondo Blanco E-commerce (Amazon/Shopify Style)",
            "Estilo Urbano / Streetwear",
            "Fotografía de Lujo / Cinematic",
            "Cambio de Color / Texture Boost"
        ])
        
        prompt_usuario = st.text_area("Instrucciones adicionales:", placeholder="Ej: Añadir sombras suaves debajo...")

    # --- LÓGICA DE PROMPTS ---
    final_prompt = prompt_usuario
    if preset == "Fondo Blanco E-commerce (Amazon/Shopify Style)":
        final_prompt = f"Product photography of the socks on a pure white minimalist background, studio lighting, high contrast, 8k, {prompt_usuario}"
    elif preset == "Estilo Urbano / Streetwear":
        final_prompt = f"Socks worn in a street style setting, concrete background, natural sunlight, urban vibe, {prompt_usuario}"
    elif preset == "Fotografía de Lujo / Cinematic":
        final_prompt = f"Luxury advertising photography, soft bokeh background, dramatic lighting, high weave detail, {prompt_usuario}"

    # --- BOTÓN DE ACCIÓN ---
    if st.button("✨ Procesar con IA", use_container_width=True):
        if not foto_original:
            st.warning("Primero sube una foto.")
        else:
            with st.spinner("La IA está reinterpretando tu producto..."):
                try:
                    # Preparar imagen
                    img_bytes = foto_original.getvalue()
                    encoded_string = base64.b64encode(img_bytes).decode("utf-8")
                    data_uri = f"data:image/jpeg;base64,{encoded_string}"

                    # Llamada API
                    api_url = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
                    headers = {"Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}", "Content-Type": "application/json"}
                    payload = {"prompt": final_prompt, "image_urls": [data_uri]}

                    response = requests.post(api_url, json=payload, headers=headers)
                    data = response.json()

                    if "images" in data:
                        res_url = data['images'][0]['url']
                        st.image(res_url, caption="Resultado Pro", use_column_width=True)
                        
                        # Guardar en galería de sesión
                        st.session_state.gallery.append({"img": res_url, "prompt": final_prompt, "time": datetime.now()})
                        
                        st.download_button("📥 Descargar Alta Calidad", requests.get(res_url).content, "editada_pro.png")
                    else:
                        st.error(f"Error: {data}")
                except Exception as e:
                    st.error(f"Error técnico: {e}")

with tab2:
    st.header("🖼️ Historial de la Sesión")
    if not st.session_state.gallery:
        st.info("Aún no has generado imágenes en esta sesión.")
    else:
        # Mostrar galería en cuadrícula de 3 columnas
        cols = st.columns(3)
        for i, item in enumerate(reversed(st.session_state.gallery)):
            with cols[i % 3]:
                st.image(item["img"], use_column_width=True)
                st.caption(f"Hace un momento")

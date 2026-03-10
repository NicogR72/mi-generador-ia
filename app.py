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

st.title("🎨 Mi Estudio Privado: Seedream 5.0 Lite")
st.markdown("Genera imágenes exclusivas sin que nadie más las vea.")

# --- INTERFAZ ---
prompt = st.text_area("Describe tu imagen:", placeholder="Un gato cyberpunk en las calles de Medellín...")
col1, col2 = st.columns(2)
with col1:
    aspect_ratio = st.selectbox("Formato", ["1:1", "16:9", "9:16", "4:3"])
with col2:
    quality = st.select_slider("Calidad/Pasos", options=["Baja", "Media", "Alta"])

# --- GENERACIÓN ---
if st.button("🚀 Generar Imagen Ahora"):
    if not prompt:
        st.warning("Escribe algo primero.")
    else:
        with st.spinner("Seedream está trabajando en tus medias..."):
            try:
                # 1. Configuración de lo que le pedimos a la IA
                payload = {
                    "prompt": prompt,
                    "image_size": "square_hd" if aspect_ratio == "1:1" else "landscape_hd"
                }
                
                # 2. Tus credenciales (Sacadas de la pestaña Secrets de Streamlit)
                headers = {
                    "Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}",
                    "Content-Type": "application/json"
                }

                # 3. La dirección de la "puerta" de Seedream en Fal.ai
                api_url = "https://fal.run/fal-ai/bytedance/seedream-5-lite"
                
                # 4. Enviamos la petición
                response = requests.post(api_url, json=payload, headers=headers)
                data = response.json()
                
                # 5. REVISIÓN DE RESULTADOS (Aquí es donde evitamos el error 'images')
                if "images" in data:
                    # Si todo salió bien, mostramos la imagen
                    image_url = data['images'][0]['url']
                    st.image(image_url, caption="¡Tus medias listas!", use_column_width=True)
                    
                    # Botón para que la bajes a tu PC
                    img_data = requests.get(image_url).content
                    st.download_button("📥 Descargar Imagen", img_data, "mis_medias.png")
                
                elif "detail" in data:
                    # Si la API nos rechaza por algo (ej: falta de saldo)
                    st.error(f"La API dice: {data['detail']}")
                
                else:
                    # Si pasa algo raro, vemos el mensaje completo para investigar
                    st.warning("Respuesta inesperada del servidor:")
                    st.write(data)

            except Exception as e:
                st.error(f"Hubo un error local: {e}")
                
                headers = {
                    "Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}", # Nota que Fal usa 'Key' no 'Bearer'
                    "Content-Type": "application/json"
                }

                # URL específica para Seedream en Fal.ai
                api_url = "https://fal.run/fal-ai/seedream-v5-lite"
                
                response = requests.post(api_url, json=payload, headers=headers)
                data = response.json()
                
                # En Fal.ai la imagen suele venir en una lista llamada 'images'
                image_url = data['images'][0]['url']
                st.image(image_url, caption="¡Tus medias listas!", use_column_width=True)
                
                # Botón de descarga directa
                st.download_button("Descargar Imagen", requests.get(image_url).content, "imagen_generada.png")

            except Exception as e:
                st.error(f"Hubo un error: {e}")

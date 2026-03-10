import streamlit as st
import requests
import base64
import json
import os
import zipfile
import io
import time
from datetime import datetime
from PIL import Image
from deep_translator import GoogleTranslator
import cloudinary
import cloudinary.uploader

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_OK = True
except ImportError:
    CANVAS_OK = False

try:
    from streamlit_image_comparison import image_comparison
    COMPARISON_OK = True
except ImportError:
    COMPARISON_OK = False

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="SockEdit Pro Max", layout="wide", page_icon="🧦")

if "CLOUDINARY_CLOUD_NAME" in st.secrets:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"],
    )

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_FILE  = f"{DATA_DIR}/history.json"
PROMPTS_FILE  = f"{DATA_DIR}/prompts.json"
CREDITS_FILE  = f"{DATA_DIR}/credits.json"

# ═══════════════════════════════════════════════════════════
#  DATA HELPERS
# ═══════════════════════════════════════════════════════════
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_history():  return load_json(HISTORY_FILE, [])
def save_history(h): save_json(HISTORY_FILE, h)
def load_prompts():  return load_json(PROMPTS_FILE, [])
def save_prompts(p): save_json(PROMPTS_FILE, p)

def load_credits():
    return load_json(CREDITS_FILE, {"credits": 100, "used": 0})

def save_credits(d): save_json(CREDITS_FILE, d)

def deduct_credits(n=1):
    d = load_credits()
    if d["credits"] >= n:
        d["credits"] -= n
        d["used"]    += n
        save_credits(d)
        return True
    return False

# ═══════════════════════════════════════════════════════════
#  PROMPT LIBRARY  (medias / calcetines, sin marcas)
# ═══════════════════════════════════════════════════════════
PRESETS = {
    "📸 E-commerce": [
        "Pure white seamless background, professional product photography, soft studio lighting, sharp focus, no shadows",
        "Clean white background, flat lay perspective, even diffused lighting, e-commerce style",
        "Ghost mannequin effect, white background, high detail, commercial product shot",
    ],
    "🏙️ Urbano": [
        "Urban streetwear setting, grey concrete wall background, natural daylight, lifestyle shot",
        "Street style on asphalt texture, casual urban environment, authentic documentary feel",
        "City lifestyle, exposed brick wall, golden hour natural light, editorial look",
    ],
    "🌿 Natural": [
        "Flat lay on rustic wooden surface, soft window light, minimal shadows, organic aesthetic",
        "On fresh green grass outdoors, natural daylight, clean and fresh mood",
        "On smooth river stones, natural outdoor environment, soft diffused light",
    ],
    "✨ Lujo": [
        "Luxury product photography, deep black background, dramatic Rembrandt lighting, cinematic feel",
        "High-end fashion editorial, bokeh background, premium quality, studio lighting",
        "Minimalist luxury shot on white marble, subtle shadows, refined aesthetic",
    ],
    "🎨 Creativos": [
        "Pastel gradient background in soft pink and lavender tones, beauty product shot",
        "Bold flat lay with bright colorful background, graphic modern design, overhead view",
        "Flat lay with complementary lifestyle props (coffee mug, book, plant), warm mood",
    ],
    "👟 Lifestyle": [
        "Worn on feet on cozy wooden floor, warm home atmosphere, lifestyle photo",
        "On feet walking outdoors on cobblestone, motion, authentic everyday lifestyle",
        "Relaxed home setting, warm natural light, comfortable and authentic feel",
    ],
    "🔄 Cambio de color": [
        "Same product, change color to navy blue, keep all other details identical",
        "Same product, change color to deep burgundy red, photorealistic, identical composition",
        "Same product, change color to forest green, maintain fabric texture and lighting",
    ],
    "❄️ Temporada": [
        "Winter holiday setting, pine branches and snowflakes around product, cozy mood",
        "Summer lifestyle shot, bright sunlight, colorful beach towel background",
        "Autumn flat lay with dry leaves and warm tones, seasonal mood",
    ],
}

NEGATIVE_PRESETS = [
    "blurry, low quality, distorted, deformed, pixelated",
    "mannequin, plastic look, artificial, overexposed, harsh shadows",
    "watermark, text overlay, logo, signature, branding",
    "wrinkled, dirty, damaged, worn out, stained",
    "extra objects, clutter, busy background, distracting elements",
]

# ═══════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════
def translate_to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        st.warning(f"Traducción fallida: {e}")
        return text

def file_to_b64(file_obj):
    raw = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()

def pil_to_b64(img, fmt="JPEG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()

def smart_crop(img, ratio_label):
    ratios = {
        "1:1 — Instagram / TikTok": (1, 1),
        "4:3 — Amazon / Marketplace": (4, 3),
        "3:4 — Portrait": (3, 4),
        "16:9 — Banner / Web": (16, 9),
        "9:16 — Stories / Reels": (9, 16),
        "2:3 — Pinterest": (2, 3),
    }
    wr, hr = ratios[ratio_label]
    w, h = img.size
    target = wr / hr
    current = w / h
    if current > target:
        nw = int(h * target)
        offset = (w - nw) // 2
        img = img.crop((offset, 0, offset + nw, h))
    else:
        nh = int(w / target)
        offset = (h - nh) // 2
        img = img.crop((0, offset, w, offset + nh))
    return img

def post_process(pil_img, crop=False, crop_ratio=None, compress=False, quality=85, fmt="JPEG"):
    if crop and crop_ratio:
        pil_img = smart_crop(pil_img, crop_ratio)
    buf = io.BytesIO()
    save_fmt = fmt if fmt != "WEBP" else "WEBP"
    if compress:
        pil_img.save(buf, format=save_fmt, quality=quality, optimize=True)
    else:
        pil_img.save(buf, format=save_fmt)
    return buf.getvalue(), pil_img

def upload_cloudinary(source):
    try:
        if "CLOUDINARY_CLOUD_NAME" in st.secrets:
            r = cloudinary.uploader.upload(source, folder="sockedit")
            return r["secure_url"]
    except Exception:
        pass
    return source

def fetch_pil(url):
    r = requests.get(url, timeout=30)
    return Image.open(io.BytesIO(r.content)).convert("RGB")

# ═══════════════════════════════════════════════════════════
#  API
# ═══════════════════════════════════════════════════════════
FAL_EDIT_URL    = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
FAL_INPAINT_URL = "https://fal.run/fal-ai/flux/dev/image-to-image"  # ajusta si hay endpoint específico

def fal_headers():
    return {
        "Authorization": f"Key {st.secrets['SEEDREAM_API_KEY']}",
        "Content-Type": "application/json",
    }

def call_edit(prompt, img_b64, neg="", seed=None, guidance=7.5, num=1, size="square_hd"):
    payload = {
        "prompt": prompt,
        "image_urls": [img_b64],
        "num_images": num,
        "guidance_scale": guidance,
        "image_size": size,
    }
    if neg:     payload["negative_prompt"] = neg
    if seed:    payload["seed"] = seed
    r = requests.post(FAL_EDIT_URL, json=payload, headers=fal_headers(), timeout=180)
    return r.json()

def call_inpaint(prompt, img_b64, mask_b64, neg="", seed=None, guidance=7.5):
    payload = {
        "prompt": prompt,
        "image_url": img_b64,
        "mask_url": mask_b64,
        "guidance_scale": guidance,
        "num_inference_steps": 30,
    }
    if neg:  payload["negative_prompt"] = neg
    if seed: payload["seed"] = seed
    r = requests.post(FAL_INPAINT_URL, json=payload, headers=fal_headers(), timeout=180)
    return r.json()

# ═══════════════════════════════════════════════════════════
#  AUTH + SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🧦 SockEdit Pro Max")
    password = st.text_input("🔐 Contraseña", type="password")
    VALID_PWD = st.secrets.get("APP_PASSWORD", "TU_CONTRASEÑA_AQUI")
    if password != VALID_PWD:
        st.info("Introduce tu contraseña para acceder.")
        st.stop()

    st.markdown("---")
    cred = load_credits()
    st.metric("💳 Créditos disponibles", cred["credits"])
    st.metric("📊 Total usados", cred["used"])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("➕ +50"):
            cred["credits"] += 50
            save_credits(cred)
            st.rerun()
    with col_s2:
        if st.button("➕ +100"):
            cred["credits"] += 100
            save_credits(cred)
            st.rerun()

    manual_credits = st.number_input("Establecer créditos", 0, 99999, cred["credits"], key="set_cred")
    if st.button("✅ Aplicar"):
        cred["credits"] = manual_credits
        save_credits(cred)
        st.rerun()

    st.markdown("---")
    st.caption("1 imagen generada = 1 crédito")
    st.caption(f"Librerías:\n- canvas: {'✅' if CANVAS_OK else '❌ pip install streamlit-drawable-canvas'}\n- comparador: {'✅' if COMPARISON_OK else '❌ pip install streamlit-image-comparison'}")

st.title("🧦 SockEdit Pro Max")

# ═══════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════
tab_editor, tab_inpaint, tab_batch, tab_prompts, tab_history, tab_tools = st.tabs([
    "🖌️ Editor",
    "🎭 Inpainting",
    "📦 Batch",
    "📚 Prompts",
    "📂 Historial",
    "🔧 Herramientas",
])

# ══════════════════════════════════════════
#  TAB 1 — EDITOR PRINCIPAL
# ══════════════════════════════════════════
with tab_editor:
    L, R = st.columns([1, 1])

    with L:
        st.subheader("⚙️ Configuración")
        foto = st.file_uploader("📁 Imagen base", type=["jpg","png","jpeg"], key="ed_foto")

        # — Prompt con presets —
        cat = st.selectbox("Categoría preset", list(PRESETS.keys()), key="ed_cat")
        preset_sel = st.selectbox("Preset", ["(personalizado)"] + PRESETS[cat], key="ed_preset")
        default_prompt = preset_sel if preset_sel != "(personalizado)" else ""

        prompt = st.text_area("✍️ Prompt (español o inglés)", value=default_prompt, height=100, key="ed_prompt")

        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("🌐 Traducir al inglés", key="ed_tr"):
                if prompt:
                    st.session_state["ed_prompt"] = translate_to_english(prompt)
                    st.rerun()
        with c2:
            auto_tr = st.checkbox("Auto-traducir siempre", value=True, key="ed_auto_tr")

        # — Prompt negativo —
        with st.expander("🚫 Prompt Negativo"):
            neg_preset = st.selectbox("Preset negativo", ["(personalizado)"] + NEGATIVE_PRESETS, key="ed_neg_pre")
            neg = st.text_area("Qué evitar", value=neg_preset if neg_preset != "(personalizado)" else "", height=70, key="ed_neg")

        # — Parámetros avanzados —
        with st.expander("🎛️ Parámetros avanzados"):
            c1, c2 = st.columns(2)
            with c1:
                guidance   = st.slider("Intensidad (guidance scale)", 1.0, 20.0, 7.5, 0.5, key="ed_guid")
                num_imgs   = st.slider("Nº variaciones", 1, 4, 1, key="ed_num")
            with c2:
                seed       = st.number_input("Seed (0 = aleatorio)", 0, 999999, 0, key="ed_seed")
                img_size   = st.selectbox("Resolución", [
                    "square_hd","square","portrait_4_3","portrait_16_9","landscape_4_3","landscape_16_9"
                ], key="ed_size")

        # — Post-proceso —
        with st.expander("🔧 Post-proceso"):
            do_crop = st.checkbox("Recorte inteligente", key="ed_crop")
            crop_ratio = st.selectbox("Formato de recorte", [
                "1:1 — Instagram / TikTok","4:3 — Amazon / Marketplace",
                "3:4 — Portrait","16:9 — Banner / Web","9:16 — Stories / Reels","2:3 — Pinterest"
            ], key="ed_ratio") if do_crop else None
            do_compress  = st.checkbox("Comprimir imagen", key="ed_compress")
            comp_quality = st.slider("Calidad JPEG", 50, 100, 85, key="ed_q") if do_compress else 85
            out_fmt      = st.selectbox("Formato de salida", ["JPEG","PNG","WEBP"], key="ed_fmt")

        cred = load_credits()
        gen_btn = st.button("🚀 Renderizar", type="primary", use_container_width=True, key="ed_gen")

    with R:
        st.subheader("📸 Resultado")

        if gen_btn:
            if not foto:         st.warning("Sube una imagen base."); st.stop()
            if not prompt:       st.warning("Escribe un prompt."); st.stop()
            if cred["credits"] < num_imgs:
                st.error(f"Créditos insuficientes ({cred['credits']} disponibles, {num_imgs} necesarios)"); st.stop()

            final_prompt = translate_to_english(prompt) if auto_tr else prompt

            with st.spinner(f"🎨 Generando {num_imgs} variación(es)…"):
                try:
                    img_b64 = file_to_b64(foto)
                    data = call_edit(
                        prompt=final_prompt, img_b64=img_b64, neg=neg,
                        seed=seed if seed > 0 else None,
                        guidance=guidance, num=num_imgs, size=img_size,
                    )

                    if "images" not in data:
                        st.error(f"Error API: {data}")
                    else:
                        deduct_credits(len(data["images"]))
                        history = load_history()
                        st.success(f"✅ {len(data['images'])} imagen(es) generadas")

                        for idx, img_info in enumerate(data["images"]):
                            url = upload_cloudinary(img_info["url"])
                            pil_res = fetch_pil(url)
                            raw_bytes, pil_pp = post_process(
                                pil_res,
                                crop=do_crop, crop_ratio=crop_ratio,
                                compress=do_compress, quality=comp_quality,
                                fmt=out_fmt,
                            )

                            st.markdown(f"**— Variación {idx+1} —**")

                            if COMPARISON_OK:
                                orig_pil = Image.open(foto).convert("RGB")
                                image_comparison(img1=orig_pil, img2=pil_pp,
                                                 label1="Original", label2="Editada",
                                                 width=700)
                            else:
                                ca, cb = st.columns(2)
                                with ca: st.image(foto,   caption="Original",  use_column_width=True)
                                with cb: st.image(pil_pp, caption="Editada",   use_column_width=True)

                            st.download_button(
                                f"⬇️ Descargar variación {idx+1} ({out_fmt})",
                                data=raw_bytes,
                                file_name=f"sockedit_v{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{out_fmt.lower()}",
                                mime=f"image/{out_fmt.lower()}",
                                key=f"ed_dl_{idx}_{time.time_ns()}",
                            )
                            st.markdown("---")

                            history.append({
                                "url": url, "mode": "editor",
                                "prompt_es": prompt, "final_prompt": final_prompt,
                                "negative": neg, "guidance": guidance,
                                "seed": seed, "size": img_size,
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                        save_history(history)

                except Exception as e:
                    st.error(f"Error técnico: {e}")

# ══════════════════════════════════════════
#  TAB 2 — INPAINTING
# ══════════════════════════════════════════
with tab_inpaint:
    st.subheader("🎭 Inpainting — Edición por Zonas")

    if not CANVAS_OK:
        st.error("Instala `streamlit-drawable-canvas` para usar esta función.")
        st.code("pip install streamlit-drawable-canvas", language="bash")
    else:
        L2, R2 = st.columns([1, 1])
        with L2:
            foto_inp = st.file_uploader("Imagen base", type=["jpg","png","jpeg"], key="inp_foto")

            if foto_inp:
                pil_inp = Image.open(foto_inp).convert("RGB")
                # Redimensionar para canvas (max 600px)
                mw = 600
                w, h = pil_inp.size
                if w > mw:
                    pil_inp = pil_inp.resize((mw, int(h * mw / w)))

                st.markdown("**🖌️ Pinta la zona a editar (blanco = editar):**")
                canvas_result = st_canvas(
                    fill_color="rgba(255,255,255,1)",
                    stroke_width=30,
                    stroke_color="#ffffff",
                    background_image=pil_inp,
                    update_streamlit=True,
                    height=pil_inp.height,
                    width=pil_inp.width,
                    drawing_mode="freedraw",
                    key="inp_canvas",
                )

            prompt_inp = st.text_area("Qué debe aparecer en la zona pintada", key="inp_prompt")
            neg_inp    = st.text_area("Prompt negativo (opcional)", height=70, key="inp_neg")

            c1, c2 = st.columns(2)
            with c1:
                guid_inp = st.slider("Intensidad", 1.0, 20.0, 7.5, key="inp_guid")
                seed_inp = st.number_input("Seed", 0, 999999, 0, key="inp_seed")
            with c2:
                auto_tr_inp = st.checkbox("Auto-traducir", True, key="inp_tr")

            cred = load_credits()
            inp_btn = st.button("🎨 Aplicar Inpainting", type="primary", use_container_width=True, key="inp_btn")

        with R2:
            st.subheader("Resultado")
            st.info("⚠️ El inpainting usa el endpoint de flux/dev. Si tienes acceso al endpoint específico de Seedream inpainting en fal.ai, actualiza `FAL_INPAINT_URL` en el código.")

            if inp_btn:
                if not foto_inp:
                    st.warning("Sube una imagen.")
                elif canvas_result is None or canvas_result.image_data is None:
                    st.warning("Pinta primero las zonas a editar.")
                elif not prompt_inp:
                    st.warning("Escribe qué poner en la zona pintada.")
                elif cred["credits"] < 1:
                    st.error("Sin créditos disponibles.")
                else:
                    fp = translate_to_english(prompt_inp) if auto_tr_inp else prompt_inp
                    with st.spinner("🎭 Procesando inpainting…"):
                        try:
                            import numpy as np
                            # Máscara
                            mask_arr = canvas_result.image_data[:, :, 3]  # canal alpha
                            mask_pil = Image.fromarray(mask_arr.astype("uint8"))
                            mask_buf = io.BytesIO()
                            mask_pil.save(mask_buf, format="PNG")
                            mask_b64 = "data:image/png;base64," + base64.b64encode(mask_buf.getvalue()).decode()

                            # Imagen
                            img_buf = io.BytesIO()
                            pil_inp.save(img_buf, format="JPEG")
                            img_b64 = "data:image/jpeg;base64," + base64.b64encode(img_buf.getvalue()).decode()

                            data = call_inpaint(fp, img_b64, mask_b64,
                                               neg=neg_inp,
                                               seed=seed_inp if seed_inp > 0 else None,
                                               guidance=guid_inp)

                            if "images" in data:
                                deduct_credits(1)
                                url = upload_cloudinary(data["images"][0]["url"])
                                pil_r = fetch_pil(url)

                                if COMPARISON_OK:
                                    image_comparison(img1=pil_inp, img2=pil_r, label1="Original", label2="Editada", width=600)
                                else:
                                    st.image(pil_r, caption="Resultado", use_column_width=True)

                                buf = io.BytesIO()
                                pil_r.save(buf, format="JPEG")
                                st.download_button("⬇️ Descargar resultado", data=buf.getvalue(),
                                                   file_name=f"inpaint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                                                   mime="image/jpeg", key="inp_dl")

                                history = load_history()
                                history.append({"url": url, "mode": "inpainting",
                                                "final_prompt": fp, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                                save_history(history)
                            else:
                                st.error(f"Error: {data}")
                        except Exception as e:
                            st.error(f"Error: {e}")

# ══════════════════════════════════════════
#  TAB 3 — BATCH
# ══════════════════════════════════════════
with tab_batch:
    st.subheader("📦 Procesamiento Masivo")
    L3, R3 = st.columns([1, 1])

    with L3:
        fotos_b = st.file_uploader("Subir varias imágenes", type=["jpg","png","jpeg"],
                                   accept_multiple_files=True, key="batch_fotos")
        if fotos_b:
            st.success(f"📁 {len(fotos_b)} imagen(es) cargadas")

        cat_b    = st.selectbox("Categoría preset", list(PRESETS.keys()), key="b_cat")
        preset_b = st.selectbox("Preset", ["(personalizado)"] + PRESETS[cat_b], key="b_preset")
        prompt_b = st.text_area("Prompt para TODAS las imágenes",
                                value=preset_b if preset_b != "(personalizado)" else "",
                                key="b_prompt")
        neg_b    = st.text_area("Prompt negativo", height=60, key="b_neg")

        c1, c2 = st.columns(2)
        with c1:
            guid_b   = st.slider("Intensidad", 1.0, 20.0, 7.5, key="b_guid")
            seed_b   = st.number_input("Seed", 0, 999999, 0, key="b_seed")
        with c2:
            size_b   = st.selectbox("Resolución", ["square_hd","square","portrait_4_3","landscape_4_3"], key="b_size")
            auto_b   = st.checkbox("Auto-traducir", True, key="b_tr")

        with st.expander("🔧 Post-proceso batch"):
            b_crop = st.checkbox("Recorte automático", key="b_crop")
            b_ratio = st.selectbox("Formato", ["1:1 — Instagram / TikTok","4:3 — Amazon / Marketplace",
                                               "3:4 — Portrait","16:9 — Banner / Web"], key="b_ratio") if b_crop else None
            b_comp  = st.checkbox("Comprimir", key="b_comp")
            b_q     = st.slider("Calidad", 50, 100, 85, key="b_q") if b_comp else 85
            b_fmt   = st.selectbox("Formato salida", ["JPEG","PNG","WEBP"], key="b_fmt")

        cred = load_credits()
        n_needed = len(fotos_b) if fotos_b else 0
        if n_needed:
            color = "🟢" if cred["credits"] >= n_needed else "🔴"
            st.info(f"{color} Usará **{n_needed}** crédito(s) — Disponibles: **{cred['credits']}**")

        batch_btn = st.button("🚀 Procesar todo", type="primary", use_container_width=True, key="batch_go")

    with R3:
        st.subheader("Resultados")

        if batch_btn:
            if not fotos_b:         st.warning("Sube imágenes."); st.stop()
            if not prompt_b:        st.warning("Escribe un prompt."); st.stop()
            if cred["credits"] < n_needed:
                st.error(f"Créditos insuficientes ({cred['credits']} disponibles, {n_needed} necesarios)"); st.stop()

            fp_b = translate_to_english(prompt_b) if auto_b else prompt_b
            progress = st.progress(0, text="Iniciando cola de trabajos…")
            results, errors = [], []
            history = load_history()

            for i, foto in enumerate(fotos_b):
                progress.progress(i / len(fotos_b), text=f"⚙️ Procesando {i+1}/{len(fotos_b)}: {foto.name}")
                try:
                    data = call_edit(prompt=fp_b, img_b64=file_to_b64(foto),
                                     neg=neg_b, seed=seed_b if seed_b > 0 else None,
                                     guidance=guid_b, num=1, size=size_b)
                    if "images" in data:
                        deduct_credits(1)
                        url  = upload_cloudinary(data["images"][0]["url"])
                        pil  = fetch_pil(url)
                        raw, pil_pp = post_process(pil, crop=b_crop, crop_ratio=b_ratio,
                                                   compress=b_comp, quality=b_q, fmt=b_fmt)
                        results.append({"name": foto.name, "bytes": raw, "pil": pil_pp, "url": url})
                        history.append({"url": url, "mode": "batch", "final_prompt": fp_b,
                                        "filename": foto.name, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    else:
                        errors.append(f"{foto.name}: {data}")
                except Exception as e:
                    errors.append(f"{foto.name}: {str(e)}")

            progress.progress(1.0, text=f"✅ Completado: {len(results)}/{len(fotos_b)}")
            save_history(history)

            if results:
                # ZIP
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for res in results:
                        fname = f"edited_{os.path.splitext(res['name'])[0]}.{b_fmt.lower()}"
                        zf.writestr(fname, res["bytes"])

                st.download_button(
                    f"📦 Descargar todo en ZIP ({len(results)} imágenes)",
                    data=zip_buf.getvalue(),
                    file_name=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip", type="primary", key="batch_zip",
                )
                st.markdown("---")

                cols = st.columns(min(3, len(results)))
                for idx, res in enumerate(results):
                    with cols[idx % 3]:
                        st.image(res["pil"], caption=res["name"], use_column_width=True)
                        st.download_button(f"⬇️ {res['name']}", data=res["bytes"],
                                           file_name=f"edited_{os.path.splitext(res['name'])[0]}.{b_fmt.lower()}",
                                           mime=f"image/{b_fmt.lower()}", key=f"b_dl_{idx}")

            if errors:
                with st.expander(f"⚠️ {len(errors)} error(es)"):
                    for e in errors: st.error(e)

# ══════════════════════════════════════════
#  TAB 4 — PROMPTS
# ══════════════════════════════════════════
with tab_prompts:
    st.subheader("📚 Biblioteca de Prompts")
    L4, R4 = st.columns([1, 1])

    with L4:
        st.markdown("#### 🗂️ Presets predefinidos (Medias & Calcetines)")
        for cat_name, prompts in PRESETS.items():
            with st.expander(cat_name):
                for p in prompts:
                    st.code(p, language=None)

        st.markdown("---")
        st.markdown("#### ➕ Guardar prompt personalizado")
        pname = st.text_input("Nombre", key="p_name")
        ptext = st.text_area("Texto del prompt", height=80, key="p_text")
        pcat  = st.text_input("Categoría", value="Mis Prompts", key="p_cat")
        if st.button("💾 Guardar", key="p_save"):
            if pname and ptext:
                sp = load_prompts()
                sp.append({"name": pname, "text": ptext, "cat": pcat,
                            "date": datetime.now().strftime("%Y-%m-%d")})
                save_prompts(sp)
                st.success(f"✅ Guardado: {pname}")
                st.rerun()

    with R4:
        st.markdown("#### 📌 Mis prompts guardados")
        sp = load_prompts()
        if sp:
            for i, item in enumerate(reversed(sp)):
                ri = len(sp) - 1 - i
                with st.expander(f"**{item['name']}** — {item.get('cat','')} ({item.get('date','')})"):
                    st.code(item["text"], language=None)
                    if st.button("🗑️ Eliminar", key=f"del_p_{ri}"):
                        sp.pop(ri); save_prompts(sp); st.rerun()
        else:
            st.info("No tienes prompts guardados todavía.")

        st.markdown("---")
        st.markdown("#### 📜 Historial de prompts usados")
        hist = load_history()
        seen, unique = set(), []
        for item in reversed(hist):
            fp = item.get("final_prompt", "")
            if fp and fp not in seen:
                seen.add(fp); unique.append(item)

        if unique:
            for item in unique[:25]:
                fp = item.get("final_prompt", "")
                with st.expander(f"📝 {fp[:55]}…"):
                    st.caption(f"Fecha: {item.get('date','')} | Modo: {item.get('mode','')}")
                    st.code(fp, language=None)
                    orig = item.get("prompt_es", "")
                    if orig and orig != fp:
                        st.caption(f"🇪🇸 Original: {orig}")
        else:
            st.info("Sin historial todavía.")

# ══════════════════════════════════════════
#  TAB 5 — HISTORIAL
# ══════════════════════════════════════════
with tab_history:
    st.subheader("📂 Archivo de Imágenes Generadas")
    hist = load_history()

    if not hist:
        st.info("Todavía no hay imágenes generadas.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1: filter_mode = st.selectbox("Filtrar modo", ["Todos","editor","batch","inpainting"], key="hf_mode")
        with c2: search = st.text_input("Buscar en prompt", key="hf_search")
        with c3: st.metric("Total imágenes", len(hist))
        with c4:
            if st.button("🗑️ Limpiar historial", key="h_clear"):
                save_history([]); st.rerun()

        filtered = hist
        if filter_mode != "Todos": filtered = [h for h in filtered if h.get("mode") == filter_mode]
        if search: filtered = [h for h in filtered if search.lower() in h.get("final_prompt","").lower()]

        items = list(reversed(filtered))[:60]
        st.caption(f"Mostrando {len(items)} de {len(hist)} imágenes")

        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                try:
                    st.image(item["url"], use_column_width=True)
                    st.caption(f"🗓️ {item.get('date','')} | {item.get('mode','')}")
                    prompt_preview = item.get("final_prompt","")[:55]
                    st.caption(f"📝 {prompt_preview}…")
                    r = requests.get(item["url"], timeout=10)
                    if r.status_code == 200:
                        st.download_button("⬇️ Descargar", data=r.content,
                                           file_name=f"sock_{idx}_{item.get('date','').replace(':','-').replace(' ','_')}.jpg",
                                           mime="image/jpeg", key=f"h_dl_{idx}_{item.get('date','')}")
                except Exception:
                    st.warning("No se pudo cargar esta imagen.")

# ══════════════════════════════════════════
#  TAB 6 — HERRAMIENTAS (sin IA)
# ══════════════════════════════════════════
with tab_tools:
    st.subheader("🔧 Herramientas de Imagen (sin IA)")
    st.caption("Recortar, comprimir y convertir imágenes localmente sin gastar créditos.")

    foto_t = st.file_uploader("📁 Subir imagen", type=["jpg","png","jpeg","webp"], key="t_foto")

    if foto_t:
        pil_t = Image.open(foto_t).convert("RGB")
        st.image(pil_t, caption=f"Original — {pil_t.size[0]}×{pil_t.size[1]}px", use_column_width=False, width=300)

        st.markdown("---")
        col_t1, col_t2, col_t3 = st.columns(3)

        with col_t1:
            st.markdown("**✂️ Recorte inteligente**")
            t_ratio = st.selectbox("Formato", [
                "1:1 — Instagram / TikTok","4:3 — Amazon / Marketplace",
                "3:4 — Portrait","16:9 — Banner / Web","9:16 — Stories / Reels","2:3 — Pinterest"
            ], key="t_ratio")
            t_resize = st.number_input("Redimensionar al ancho (px, 0=no cambiar)", 0, 4096, 0, key="t_resize")

            if st.button("✂️ Aplicar recorte", key="t_crop_btn"):
                result_t = smart_crop(pil_t, t_ratio)
                if t_resize > 0:
                    ar = result_t.height / result_t.width
                    result_t = result_t.resize((t_resize, int(t_resize * ar)), Image.LANCZOS)
                st.image(result_t, caption=f"Recortada — {result_t.size[0]}×{result_t.size[1]}px", use_column_width=False, width=300)
                buf = io.BytesIO(); result_t.save(buf, format="JPEG", quality=90)
                st.download_button("⬇️ Descargar recortada", buf.getvalue(),
                                   file_name=f"crop_{foto_t.name}", mime="image/jpeg", key="t_dl_crop")

        with col_t2:
            st.markdown("**🗜️ Compresión**")
            t_q = st.slider("Calidad JPEG", 10, 100, 85, key="t_q")

            if st.button("🗜️ Comprimir", key="t_comp_btn"):
                buf = io.BytesIO(); pil_t.save(buf, format="JPEG", quality=t_q, optimize=True)
                compressed = buf.getvalue()
                original_size = len(foto_t.getvalue())
                saved_pct = 100 - (len(compressed) / original_size * 100)
                st.success(f"Original: {original_size//1024}KB → Comprimida: {len(compressed)//1024}KB (−{saved_pct:.0f}%)")
                st.download_button("⬇️ Descargar comprimida", compressed,
                                   file_name=f"compressed_{foto_t.name}", mime="image/jpeg", key="t_dl_comp")

        with col_t3:
            st.markdown("**🔄 Conversión de formato**")
            t_fmt_out = st.selectbox("Convertir a", ["JPEG","PNG","WEBP"], key="t_fmt_out")
            t_fmt_q   = st.slider("Calidad", 50, 100, 90, key="t_fmt_q")

            if st.button("🔄 Convertir", key="t_conv_btn"):
                buf = io.BytesIO()
                if t_fmt_out == "PNG":
                    pil_t.save(buf, format="PNG")
                elif t_fmt_out == "WEBP":
                    pil_t.save(buf, format="WEBP", quality=t_fmt_q)
                else:
                    pil_t.save(buf, format="JPEG", quality=t_fmt_q)
                ext = t_fmt_out.lower()
                st.success(f"Convertida a {t_fmt_out} — {len(buf.getvalue())//1024}KB")
                st.download_button(f"⬇️ Descargar .{ext}", buf.getvalue(),
                                   file_name=f"{os.path.splitext(foto_t.name)[0]}.{ext}",
                                   mime=f"image/{ext}", key="t_dl_conv")

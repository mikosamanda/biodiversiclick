import contextlib
from io import BytesIO
import cv2 as cv
import numpy as np
import streamlit as st

def _reset():
    keys_defaults = {
        "rotate": 0,
        "scale": 100,
        "shear_x": 0,
        "shear_y": 0,
        "brightness": 100,
        "contrast": 100,
        "log_transform": False,
        "gamma": 1.0,
        "negative": False
    }
    for k, v in keys_defaults.items():
        st.session_state[k] = v

def adjust_brightness_contrast(img, brightness=100, contrast=100):
    beta = np.clip(brightness, -100, 100)
    alpha = np.clip(contrast, 0.5, 1.5)
    return cv.convertScaleAbs(img, alpha=alpha, beta=beta)

def apply_rotation(img, angle):
    (h, w) = img.shape[:2]
    center = (w / 2, h / 2)
    M = cv.getRotationMatrix2D(center, angle, 1.0)
    return cv.warpAffine(img, M, (w, h))

def apply_scaling(img, scale_percent):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    return cv.resize(img, (width, height), interpolation=cv.INTER_CUBIC)

def apply_shear(img, shear_x, shear_y):
    rows, cols = img.shape[:2]
    M = np.float32([[1, shear_x / 100, 0], [shear_y / 100, 1, 0]])
    return cv.warpAffine(img, M, (cols, rows))

def apply_negative(img):
    return 255 - img

def apply_log_transform(img):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    h, s, v = cv.split(hsv)
    v_log = np.log1p(v.astype(np.float32))
    cv.normalize(v_log, v_log, 0, 255, cv.NORM_MINMAX)
    v_log = v_log.astype(np.uint8)
    final_hsv = cv.merge((h, s, v_log))
    return cv.cvtColor(final_hsv, cv.COLOR_HSV2BGR)

def apply_gamma_transform(img, gamma):
    gamma = max(0.3, min(gamma, 2.5))
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    h, s, v = cv.split(hsv)
    lookup_table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype("uint8")
    v_gamma = cv.LUT(v, lookup_table)
    final_hsv = cv.merge((h, s, v_gamma))
    return cv.cvtColor(final_hsv, cv.COLOR_HSV2BGR)

# ---------- INTERFACE STREAMLIT ----------

st.set_page_config("BiodiversiClick", layout="wide")
st.title("📸 BiodiversiClick - OpenCV Edition")

with st.sidebar:
    st.markdown("### Ajustes Geométricos")
    st.slider("Rotação (graus)", 0, 360, 0, key="rotate")
    st.slider("Escala (%)", 10, 300, 100, key="scale")
    st.slider("Cisalhamento Horizontal", -100, 100, 0, key="shear_x",)
    st.slider("Cisalhamento Vertical", -100, 100, 0, key="shear_y")

    st.markdown("### Ajustes de Intensidade")
    st.slider("Brilho", 0, 200, key="brightness")
    st.slider("Contraste", 0, 200, key="contrast")
    st.checkbox("Transformação Logarítmica", key="log_transform")
    st.slider("Gama (potência)", 0.1, 3.0, 1.0, 0.1, key="gamma")
    st.checkbox("Filtro Negativo", key="negative")

    if st.button("Resetar Tudo"):
        _reset()
        st.experimental_rerun()

option = st.radio("Entrada de imagem:", ("Carregar imagem", "Tirar foto"), horizontal=True)
if option == "Tirar foto":
    upload_img = st.camera_input("Capturar imagem")
else:
    upload_img = st.file_uploader("Carregar imagem", type=["jpg", "jpeg", "png", "bmp"])

if upload_img is not None:
    file_bytes = np.asarray(bytearray(upload_img.read()), dtype=np.uint8)
    img_original = cv.imdecode(file_bytes, cv.IMREAD_COLOR)
    img_processada = img_original.copy()

    img_processada = apply_rotation(img_processada, st.session_state.rotate)
    

    img_processada = apply_scaling(img_processada, st.session_state.scale)
   

    img_processada = apply_shear(img_processada, st.session_state.shear_x, st.session_state.shear_y)
 

    img_processada = adjust_brightness_contrast(img_processada, st.session_state.brightness, st.session_state.contrast)


    if st.session_state.log_transform:
        img_processada = apply_log_transform(img_processada)
        img_processada = apply_gamma_transform(img_processada, st.session_state.gamma)

    if st.session_state.negative:
        img_processada = apply_negative(img_processada)

    img_display_original = cv.cvtColor(img_original, cv.COLOR_BGR2RGB)
    img_display_processada = cv.cvtColor(img_processada, cv.COLOR_BGR2RGB)

    def resize_to_fit(image, max_width=800):
        h, w = image.shape[:2]
        if w > max_width:
            ratio = max_width / w
            new_h = int(h * ratio)
            return cv.resize(image, (max_width, new_h), interpolation=cv.INTER_AREA)
        return image

    col1, col2 = st.columns(2)
   # col1.image(img_display_original, caption="Original", use_container_width=True, width=img_original.shape[1])
   # col2.image(img_display_processada, caption="Processada", use_container_width=True, width=img_processada.shape[1])
    with col1:
        st.image(resize_to_fit(img_display_original), caption="Original", use_container_width=False)
    with col2:
        st.image(resize_to_fit(img_display_processada), caption="Processada", use_container_width=False)    
    
    _, buffer = cv.imencode(".png", img_processada)
    st.download_button("💾 Baixar imagem", data=buffer.tobytes(), file_name="imagem_editada.png", mime="image/png")

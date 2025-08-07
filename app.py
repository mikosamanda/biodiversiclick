import contextlib
from io import BytesIO
import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
from rembg import remove
from streamlit_image_comparison import image_comparison

VERSION = "1.0.2" 

# ---------- FUNÇÕES AUXILIARES ----------

# Reinicia os controles deslizantes e checkboxes para valores padrão
def _reset(key: str) -> None:
    if key == "all":
        st.session_state["rotate_slider"] = 0
        st.session_state["brightness_slider"] = st.session_state[
            "saturation_slider"] = st.session_state["contrast_slider"] = st.session_state["sharpness_slider"] = 100
        st.session_state["scale_slider"] = 100
        st.session_state["shear_x_slider"] = st.session_state["shear_y_slider"] = 0
        st.session_state["bg"] = st.session_state["mirror"] = st.session_state["gray_bw"] = st.session_state["negative"] = 0
    elif key == "rotate_slider":
        st.session_state["rotate_slider"] = 0
    elif key == "checkboxes":
        st.session_state["mirror"] = st.session_state["gray_bw"] = st.session_state["negative"] = 0
    else:
        st.session_state[key] = 100

# Aplica todas as transformações na imagem
def apply_transformations(image, degrees, brightness_factor, saturation_factor, contrast_factor, sharpness_factor, flag):
    rotated_img = image.rotate(360 - degrees)
    if flag:
        brightness_img = ImageEnhance.Brightness(rotated_img).enhance(brightness_factor / 100)
        saturation_img = ImageEnhance.Color(brightness_img).enhance(saturation_factor / 100)
        contrast_img = ImageEnhance.Contrast(saturation_img).enhance(contrast_factor / 100)
        sharpness_img = ImageEnhance.Sharpness(contrast_img).enhance(sharpness_factor / 100)
        return sharpness_img
    else:
        return rotated_img

# ---------- FUNÇÕES ADICIONADAS ----------
def apply_scale(image, scale_factor):
    """Redimensiona a imagem mantendo a proporção"""
    width, height = image.size
    new_width = int(width * scale_factor / 100)
    new_height = int(height * scale_factor / 100)
    return image.resize((new_width, new_height), Image.LANCZOS)

def apply_shear(image, shear_x, shear_y):
    """Aplica cisalhamento à imagem"""
    width, height = image.size
    shear_factor_x = shear_x / 100
    shear_factor_y = shear_y / 100
    
    # Matriz de transformação para cisalhamento
    transform_matrix = (1, shear_factor_x, -width * shear_factor_x / 2,
                       shear_factor_y, 1, -height * shear_factor_y / 2)
    
    return image.transform(image.size, Image.AFFINE, transform_matrix, Image.BICUBIC)

def apply_negative(image):
    """Inverte as cores da imagem (efeito negativo)"""
    return ImageOps.invert(image)

# Define o título e layout da página web
st.set_page_config(
    page_title="BiodiversiClick",
    layout="wide",
)

# ---------- CHECA RESET ----------
if st.session_state.get("reset_trigger", False):
    st.session_state["reset_trigger"] = False
    _reset("all")

# ---------- ESTILO PERSONALIZADO ----------

# Personaliza cores e aparência da interface
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
    }
    [data-testid="stSidebar"] {
        background-color: #1f4430;
        color: white;
    }
    .stSlider > div[data-testid="stSlider"] > div {
        background-color: #456a45;
    }
    .stDownloadButton button {
        background-color: #d4af3d;
        color: black;
    }
    .stButton>button {
        background-color: #5685a8;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cria o título principal
st.title("📸 BiodiversiClick")

# ---------- BARRA LATERAL ----------
# Cria todos os checkboxes e controles deslizantes da barra lateral
with st.sidebar:
    st.checkbox("Remover fundo?", key="bg")
    st.checkbox("Espelhar imagem?", key="mirror")
    st.checkbox("Converter para tons de cinza ou P&B", key="gray_bw")
    st.checkbox("Efeito negativo", key="negative")  # Novo checkbox adicionado

    st.markdown("### 🎛️ Ajustes")

    st.session_state.setdefault("rotate_slider", 0)
    st.slider("🔁 Rotação (graus)", 0, 360, key="rotate_slider")

    # Novo controle de escala adicionado
    st.session_state.setdefault("scale_slider", 100)
    st.slider("📏 Escala (%)", 10, 200, key="scale_slider")

    # Novos controles de cisalhamento adicionados
    st.session_state.setdefault("shear_x_slider", 0)
    st.slider("↔️ Cisalhamento Horizontal", -50, 50, key="shear_x_slider")
    
    st.session_state.setdefault("shear_y_slider", 0)
    st.slider("↕️ Cisalhamento Vertical", -50, 50, key="shear_y_slider")

    st.session_state.setdefault("brightness_slider", 100)
    st.slider("💡 Brilho", 0, 1000, key="brightness_slider")

    st.session_state.setdefault("saturation_slider", 100)
    st.slider("🎨 Saturação", 0, 1000, key="saturation_slider")

    st.session_state.setdefault("contrast_slider", 100)
    st.slider("🔳 Contraste", 0, 1000, key="contrast_slider")

    st.session_state.setdefault("sharpness_slider", 100)
    st.slider("✨ Nitidez", 0, 1000, key="sharpness_slider")

# ---------- UPLOAD DE IMAGEM ----------
option = st.radio(
    label="Selecione o método de entrada da imagem:",
    options=("Carregar imagem ⬆️", "Tirar foto 📷"),
    horizontal=True
)

if option == "Tirar foto 📷":
    upload_img = st.camera_input("Capturar imagem")
    mode = "camera"
elif option == "Carregar imagem ⬆️":
    upload_img = st.file_uploader("Carregar imagem", type=["jpg", "jpeg", "png", "bmp"])
    mode = "upload"

# ---------- PROCESSAMENTO DA IMAGEM ----------
# Cria um contexto que suprime (ignora) erros do tipo NameError
with contextlib.suppress(NameError):
    # Só executa o bloco se realmente houver uma imagem carregada
    if upload_img is not None:
        # Abre a imagem e converte em RGB
        pil_img = Image.open(upload_img).convert("RGB")
        # Converte em array Numpay (para fins de processmaneot) e cria uma cópia para trabalhar com segurança
        img_arr = np.asarray(pil_img)
        image = pil_img

        # Verifica se o checkbox "Remover fundo?" está marcado
        if st.session_state["bg"]:
            # Função do pacote rembg que remove o fundo automaticamente
            image = remove(image)

        # Verifica se o checkbox de espelhamento está marcado
        if st.session_state["mirror"]:
            # Espelha a imagem horizontalmente (como um reflexo no espelho)
            image = ImageOps.mirror(image)

        # NOVO: Aplica efeito negativo se selecionado
        if st.session_state["negative"]:
            image = apply_negative(image)

         # Controla se as transformações de cores (brilho, saturação etc.) devem ser aplicadas
        flag = True
        if st.session_state["gray_bw"]:
            # Modo grayscale (tons de cinza)
            mode = "L"
            choice = st.radio("Escolha o modo de tons:", ("Tons de cinza", "Preto e Branco"))
            if choice == "Tons de cinza":
                image = image.convert(mode)
            else:
                flag = False
                # Calcula um limiar (thresh) como a média de brilho da imagem
                thresh = np.array(image).mean()
                # Aplica uma função que converte cada pixel: Acima do limiar → branco (255) e Abaixo do limiar → preto (0)
                image = image.convert(mode).point(lambda x: 255 if x > thresh else 0, mode="1")
        else:
            # Modo colorido normal
            mode = "RGB"

        # Aplica as transformações básicas
        transformed_image = apply_transformations(
            image,
            st.session_state["rotate_slider"],
            st.session_state["brightness_slider"],
            st.session_state["saturation_slider"],
            st.session_state["contrast_slider"],
            st.session_state["sharpness_slider"],
            flag
        )

        # NOVO: Aplica escala
        scaled_image = apply_scale(transformed_image, st.session_state["scale_slider"])

        # NOVO: Aplica cisalhamento
        final_image = apply_shear(scaled_image, st.session_state["shear_x_slider"], st.session_state["shear_y_slider"])

        # ---------- PREVIEW LADO A LADO ----------
        col1, col2 = st.columns(2)
        col1.image(pil_img, caption="Imagem original", use_container_width=True)
        col2.image(final_image, caption="Imagem editada", use_container_width=True)
        
        # ---------- DOWNLOAD E AÇÕES ----------
        if isinstance(final_image, np.ndarray):
            Image.fromarray(final_image).save("final_image.png")
        else:
            final_image.save("final_image.png")

        st.download_button("💾 Baixar imagem final", data=open("final_image.png", "rb"), file_name="imagem_editada.png", mime="image/png")

# Botão para resetar
        if st.button("↩️ Resetar Tudo"):
            st.session_state["reset_trigger"] = True
            st.experimental_rerun()
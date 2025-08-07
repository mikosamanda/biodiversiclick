# BiodiversiClick - Editor de Imagens com OpenCV e Streamlit

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.0-orange)
![OpenCV](https://img.shields.io/badge/opencv-4.0-green)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Descrição

**BiodiversiClick** é uma aplicação web interativa para edição de imagens, construída com Python, OpenCV e Streamlit. Ela permite que usuários façam ajustes geométricos (rotação, escala, cisalhamento) e de intensidade (brilho, contraste, transformação logarítmica, correção gama e filtro negativo) em imagens carregadas ou capturadas pela webcam, tudo em tempo real e com interface simples e amigável.

O projeto foi desenvolvido para fins educacionais e demonstra como integrar processamento de imagens com interfaces web modernas para manipulação visual rápida e prática.

## Funcionalidades principais

- Upload de imagens (JPG, JPEG, PNG, BMP) ou captura pela webcam
- Ajustes geométricos:
  - Rotação (0° a 360°)
  - Escala (10% a 300%)
  - Cisalhamento horizontal e vertical (-100% a 100%)
- Ajustes de intensidade:
  - Brilho e contraste ajustáveis
  - Transformação logarítmica
  - Correção gama
  - Filtro negativo (inversão das cores)
- Visualização lado a lado da imagem original e editada
- Download da imagem editada em PNG
- Reset de todos os parâmetros para valores padrão

## Tecnologias utilizadas

- Python 3.8+
- OpenCV
- Streamlit
- NumPy

## Como usar

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/biodiversiclick.git
   cd biodiversiclick

Instale as dependências:

    pip install -r requirements.txt

Execute o aplicativo:

    streamlit run app.py

Abra o navegador na URL mostrada (normalmente http://localhost:8501), carregue uma imagem ou capture pela webcam, ajuste os parâmetros e veja os resultados.

Contribuições

Contribuições são bem-vindas! Abra issues ou pull requests para sugerir melhorias, corrigir bugs ou adicionar recursos.

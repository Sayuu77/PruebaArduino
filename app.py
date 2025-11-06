import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import cv2
import numpy as np

# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

# Function to capture image from camera
def capture_image():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        st.error("No se pudo acceder a la cámara")
        return None
    
    st.info("Presiona 'Capturar' para tomar una foto")
    capture_button = st.button("Capturar Foto")
    
    frame_placeholder = st.empty()
    captured_image = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Error al capturar el frame")
            break
            
        # Convert BGR to RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
        
        if capture_button:
            captured_image = frame
            break
    
    cap.release()
    frame_placeholder.empty()
    
    return captured_image

# Function to convert OpenCV image to PIL format
def cv2_to_pil(cv2_image):
    cv2_image_rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(cv2_image_rgb)

# Function to save OpenCV image to bytes for upload
def cv2_to_bytes(cv2_image):
    success, encoded_image = cv2.imencode('.jpg', cv2_image)
    if success:
        return encoded_image.tobytes()
    return None

st.set_page_config(page_title="Analizador de Colores", layout="centered", initial_sidebar_state="collapsed")

# Streamlit page setup
st.title("Analizador de Colores por Cámara:🎨📷")
image = Image.open('OIG4.jpg')
st.image(image, width=350)

with st.sidebar:
    st.subheader("Este Agente analiza los colores de imágenes capturadas por cámara.")
    st.markdown("""
    **Funcionalidades:**
    - Captura imágenes en tiempo real
    - Analiza paleta de colores
    - Identifica colores dominantes
    - Proporciona códigos HEX y RGB
    - Sugiere combinaciones armónicas
    """)

ke = st.text_input('Ingresa tu Clave de OpenAI', type="password")
os.environ['OPENAI_API_KEY'] = ke

# Initialize the OpenAI client with the API key
api_key = os.environ.get('OPENAI_API_KEY')

# Image source selection
image_source = st.radio("Selecciona la fuente de la imagen:", 
                        ["Cámara Web", "Subir Archivo"], 
                        horizontal=True)

uploaded_file = None
captured_image = None

if image_source == "Cámara Web":
    st.subheader("Captura desde Cámara")
    if st.button("Iniciar Cámara"):
        captured_image = capture_image()
        if captured_image is not None:
            # Display the captured image
            pil_image = cv2_to_pil(captured_image)
            st.image(pil_image, caption="Imagen Capturada", use_container_width=True)
            
            # Save to uploaded_file format for processing
            image_bytes = cv2_to_bytes(captured_image)
            if image_bytes:
                uploaded_file = type('obj', (object,), {
                    'getvalue': lambda: image_bytes,
                    'name': 'captured_image.jpg'
                })

else:
    st.subheader("Subir Imagen")
    uploaded_file = st.file_uploader("Sube una imagen", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Display the uploaded/captured image
    with st.expander("Vista Previa de la Imagen", expanded=True):
        if image_source == "Subir Archivo":
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        else:
            # For captured images, we already displayed it above
            pass

# Toggle for showing additional details input
show_details = st.toggle("Adiciona detalles específicos sobre el análisis de color", value=False)

if show_details:
    # Text input for additional details about color analysis
    additional_details = st.text_area(
        "Especifica qué aspectos del color quieres analizar:",
        placeholder="Ej: Analizar colores dominantes, sugerir paletas armónicas, identificar colores complementarios...",
        disabled=not show_details
    )

# Button to trigger the analysis
analyze_button = st.button("Analizar Colores", type="primary")

# Check if an image has been uploaded/captured, if the API key is available, and if the button has been pressed
if (uploaded_file is not None or captured_image is not None) and api_key and analyze_button:

    with st.spinner("Analizando colores..."):
        # Encode the image
        base64_image = encode_image(uploaded_file)
    
        # Optimized prompt for color analysis
        prompt_text = (
            "Eres un experto en análisis de color y teoría del color. "
            "Analiza la imagen proporcionada y responde en español con un análisis completo de los colores presentes. "
            "Incluye:\n"
            "1. Colores dominantes y sus porcentajes aproximados\n"
            "2. Códigos HEX y RGB de los colores principales\n"
            "3. Análisis de la paleta de colores\n"
            "4. Sugerencias de combinaciones armónicas\n"
            "5. Estado de ánimo o sensaciones que transmiten los colores\n"
            "6. Recomendaciones de uso (diseño, decoración, etc.)\n\n"
            "Formatea la respuesta en markdown con secciones claras."
        )
    
        if show_details and additional_details:
            prompt_text += (
                f"\n\nContexto Adicional del Usuario:\n{additional_details}"
            )
    
        # Create the payload for the completion request
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ]
    
        # Make the request to the OpenAI API
        try:
            full_response = ""
            message_placeholder = st.empty()
            response = openai.chat.completions.create(
              model="gpt-4o",
              messages=[
                {
                   "role": "user",
                   "content": [
                     {"type": "text", "text": prompt_text},
                     {
                       "type": "image_url",
                       "image_url": {
                         "url": f"data:image/jpeg;base64,{base64_image}",
                       },
                     },
                   ],
                  }
                ],
              max_tokens=500,
            )
            
            if response.choices[0].message.content is not None:
                full_response += response.choices[0].message.content
                message_placeholder.markdown(full_response + "▌")
            
            # Final update to placeholder after the stream ends
            message_placeholder.markdown(full_response)
    
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
            
else:
    # Warnings for user action required
    if not uploaded_file and not captured_image and analyze_button:
        st.warning("Por favor captura o sube una imagen primero.")
    if not api_key:
        st.warning("Por favor ingresa tu API key de OpenAI.")

# Additional color analysis tips
with st.expander("💡 Consejos para un mejor análisis de color"):
    st.markdown("""
    - **Iluminación**: Asegúrate de tener buena iluminación al capturar imágenes
    - **Enfoque**: Mantén la cámara estable para imágenes nítidas
    - **Colores neutros**: Evita reflejos y sombras fuertes
    - **Composición**: Enfoca el área con los colores que quieres analizar
    - **Contexto**: Usa el campo de detalles para especificar tus necesidades
    """)

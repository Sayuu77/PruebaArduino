import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image, ImageDraw
import io

# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

# Function to crop image to the guide area
def crop_to_guide_area(image):
    """Crop image to only include the guide rectangle area"""
    width, height = image.size
    
    # Calculate crop area (60% of image size, centered)
    crop_width = int(width * 0.6)
    crop_height = int(height * 0.6)
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    right = left + crop_width
    bottom = top + crop_height
    
    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))
    
    return cropped_image

# Function to add guide rectangle to image (for display only)
def add_guide_rectangle(image):
    """Add a guide rectangle to show where to place the object"""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    
    # Calculate rectangle dimensions (60% of image size, centered)
    width, height = img.size
    rect_width = int(width * 0.6)
    rect_height = int(height * 0.6)
    x1 = (width - rect_width) // 2
    y1 = (height - rect_height) // 2
    x2 = x1 + rect_width
    y2 = y1 + rect_height
    
    # Draw rectangle
    draw.rectangle([x1, y1, x2, y2], outline="red", width=4)
    
    # Add corner markers for better visibility
    corner_size = 15
    # Top-left
    draw.line([x1, y1, x1 + corner_size, y1], fill="red", width=3)
    draw.line([x1, y1, x1, y1 + corner_size], fill="red", width=3)
    # Top-right
    draw.line([x2, y1, x2 - corner_size, y1], fill="red", width=3)
    draw.line([x2, y1, x2, y1 + corner_size], fill="red", width=3)
    # Bottom-left
    draw.line([x1, y2, x1 + corner_size, y2], fill="red", width=3)
    draw.line([x1, y2, x1, y2 - corner_size], fill="red", width=3)
    # Bottom-right
    draw.line([x2, y2, x2 - corner_size, y2], fill="red", width=3)
    draw.line([x2, y2, x2, y2 - corner_size], fill="red", width=3)
    
    # Add text
    draw.text((x1 + 10, y1 - 30), "COLOCA EL OBJETO AQUÍ", fill="red", stroke_width=2, stroke_fill="white")
    draw.text((width//2 - 80, y2 + 10), "Zona de detección", fill="red", stroke_width=2, stroke_fill="white")
    
    return img

# Function to convert PIL image to bytes for upload
def pil_to_bytes(pil_image):
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

st.set_page_config(page_title="Detector de Colores Básicos", layout="centered", initial_sidebar_state="collapsed")

# Streamlit page setup
st.title("🔍 Detector de Colores: Rojo, Azul, Verde")

with st.sidebar:
    st.subheader("Detector Simple de Colores")
    st.markdown("""
    **🎯 Colores que detecta:**
    - 🔴 ROJO
    - 🔵 AZUL  
    - 🟢 VERDE
    
    **📸 Instrucciones:**
    1. Coloca el objeto dentro del **cuadro rojo**
    2. Asegúrate que esté bien centrado
    3. Haz clic en **"Detectar Colores"**
    4. Solo el área dentro del cuadro se analiza
    """)

ke = st.text_input('Ingresa tu Clave de OpenAI', type="password")
if ke:
    os.environ['OPENAI_API_KEY'] = ke

api_key = os.environ.get('OPENAI_API_KEY')

# Image source selection
image_source = st.radio("Selecciona la fuente de la imagen:", 
                        ["Cámara Web", "Subir Archivo"], 
                        horizontal=True)

uploaded_file = None
cropped_image = None

if image_source == "Cámara Web":
    st.subheader("📸 Captura desde Cámara")
    
    # Instructions with visual guide
    st.info("🎯 **Coloca el objeto dentro del cuadro rojo que verás en la cámara**")
    
    # Create a custom camera input with guide overlay
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📷 Cámara con Guía")
        captured_image = st.camera_input(
            "Toma una foto del objeto", 
            key="camera_with_guide",
            help="El cuadro rojo te muestra dónde colocar el objeto para mejor detección"
        )
    
    with col2:
        st.markdown("### 💡 Guía Visual")
        # Create a sample guide image
        guide_sample = Image.new('RGB', (200, 150), color='lightgray')
        guide_with_overlay = add_guide_rectangle(guide_sample)
        st.image(guide_with_overlay, caption="Así verás la guía en la cámara", use_container_width=True)
        st.markdown("""
        **Asegúrate de:**
        - Objeto dentro del rojo ✅
        - Buena iluminación 💡
        - Enfoque claro 👁️
        """)
    
    if captured_image is not None:
        original_image = Image.open(captured_image)
        
        # Show what was captured with the guide overlay
        st.markdown("---")
        st.subheader("📷 Foto Capturada")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("**👀 Con guía de posición:**")
            guide_image = add_guide_rectangle(original_image)
            st.image(guide_image, caption="Así capturaste la imagen", use_container_width=True)
        
        with col4:
            st.markdown("**✂️ Área que se analiza:**")
            cropped_image = crop_to_guide_area(original_image)
            st.image(cropped_image, caption="Esta parte se enviará para análisis", use_container_width=True)
        
        # Convert cropped image for upload
        image_bytes = pil_to_bytes(cropped_image)
        uploaded_file = type('obj', (object,), {
            'getvalue': lambda: image_bytes.getvalue(),
            'name': 'objeto_analizado.jpg'
        })
        
        st.success("✅ ¡Imagen lista! Ahora haz clic en 'Detectar Colores'")

else:
    st.subheader("📁 Subir Imagen")
    
    uploaded_original = st.file_uploader("Sube una imagen del objeto", type=["jpg", "png", "jpeg"])
    
    if uploaded_original is not None:
        original_image = Image.open(uploaded_original)
        
        # Show the image with guide overlay
        st.subheader("📷 Vista Previa con Guía")
        
        col5, col6 = st.columns(2)
        
        with col5:
            st.markdown("**👀 Imagen original con guía:**")
            guide_image = add_guide_rectangle(original_image)
            st.image(guide_image, caption="Área de detección marcada", use_container_width=True)
        
        with col6:
            st.markdown("**✂️ Área que se analiza:**")
            cropped_image = crop_to_guide_area(original_image)
            st.image(cropped_image, caption="Esta parte se analizará", use_container_width=True)
        
        # Convert cropped image for upload
        image_bytes = pil_to_bytes(cropped_image)
        uploaded_file = type('obj', (object,), {
            'getvalue': lambda: image_bytes.getvalue(),
            'name': 'objeto_analizado.jpg'
        })

# Button to trigger the analysis
analyze_button = st.button("🎨 Detectar Colores", type="primary", use_container_width=True)

# Check if an image has been uploaded and API key is available
if uploaded_file is not None and api_key and analyze_button:

    with st.spinner("🔍 Analizando colores..."):
        # Encode the cropped image
        base64_image = encode_image(uploaded_file)
    
        # Simple prompt for basic color detection
        prompt_text = """
        Analiza esta imagen y responde SOLO con un JSON que contenga:
        
        {
            "rojo": true/false,
            "azul": true/false, 
            "verde": true/false
        }
        
        Reglas:
        - "true" si el color está presente en el objeto
        - "false" si el color NO está presente
        - Analiza solo el objeto principal dentro del área visible
        - Ignora fondos y elementos secundarios
        - Responde EXCLUSIVAMENTE con el JSON, nada más
        """
    
        # Make the request to the OpenAI API
        try:
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
                max_tokens=150,
            )
            
            # Display the response
            if response.choices[0].message.content:
                st.markdown("---")
                st.subheader("🎯 Resultados de Detección")
                
                # Parse the JSON response
                try:
                    import json
                    result_text = response.choices[0].message.content.strip()
                    # Limpiar el texto en caso de que haya markdown
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                    color_data = json.loads(result_text)
                    
                    # Mostrar resultados con emojis y colores
                    st.markdown("### 📊 Detección de Colores")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if color_data.get("rojo", False):
                            st.success("🔴 **ROJO: SÍ**")
                            st.markdown("✅ Color rojo detectado")
                        else:
                            st.error("🔴 **ROJO: NO**")
                            st.markdown("❌ No se detectó rojo")
                    
                    with col2:
                        if color_data.get("azul", False):
                            st.success("🔵 **AZUL: SÍ**")
                            st.markdown("✅ Color azul detectado")
                        else:
                            st.error("🔵 **AZUL: NO**")
                            st.markdown("❌ No se detectó azul")
                    
                    with col3:
                        if color_data.get("verde", False):
                            st.success("🟢 **VERDE: SÍ**")
                            st.markdown("✅ Color verde detectado")
                        else:
                            st.error("🟢 **VERDE: NO**")
                            st.markdown("❌ No se detectó verde")
                            
                    # Resumen
                    st.markdown("---")
                    colors_found = []
                    if color_data.get("rojo"): colors_found.append("🔴 Rojo")
                    if color_data.get("azul"): colors_found.append("🔵 Azul")
                    if color_data.get("verde"): colors_found.append("🟢 Verde")
                    
                    if colors_found:
                        st.success(f"🎨 **Colores detectados:** {', '.join(colors_found)}")
                    else:
                        st.warning("❌ **No se detectaron** los colores rojo, azul o verde")
                        
                except json.JSONDecodeError:
                    st.error("Error al procesar la respuesta. Respuesta recibida:")
                    st.code(response.choices[0].message.content)
    
        except Exception as e:
            st.error(f"❌ Ocurrió un error: {e}")
            st.info("Por favor verifica tu API key e intenta nuevamente")
            
else:
    # Warnings for user action required
    if not uploaded_file and analyze_button:
        st.warning("⚠️ Por favor captura o sube una imagen del objeto primero.")
    if not api_key and analyze_button:
        st.warning("🔑 Por favor ingresa tu API key de OpenAI.")

# Simple instructions
with st.expander("📋 Guía Rápida"):
    st.markdown("""
    ### 🎯 Cómo usar la cámara:
    1. **Verás un cuadro rojo** en la vista de la cámara
    2. **Coloca tu objeto** completamente dentro del cuadro
    3. **Asegúrate** de que esté bien iluminado
    4. **Toma la foto** cuando esté bien posicionado
    
    ### 🔍 Qué hace la app:
    - Analiza **solo el área dentro del cuadro rojo**
    - Detecta si hay colores **rojo, azul o verde**
    - Muestra resultados **SÍ/NO** para cada color
    - **Ignora** todo fuera del cuadro rojo
    
    ### 💡 Consejos:
    - Usa **fondo simple** para mejor detección
    - **Buena luz** natural o artificial
    - Objeto **bien centrado** en el cuadro
    - **Múltiples intentos** si es necesario
    """)

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

# Function to convert PIL image to bytes for upload
def pil_to_bytes(pil_image):
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

st.set_page_config(page_title="Detector de Colores Básicos", layout="centered", initial_sidebar_state="collapsed")

# Streamlit page setup
st.title("🔍 Detector de Colores: Rojo, Azul, Verde")

# Custom CSS para superponer el cuadro guía en la cámara
st.markdown("""
<style>
    .camera-overlay {
        position: relative;
        display: inline-block;
    }
    .camera-guide {
        position: absolute;
        top: 20%;
        left: 20%;
        width: 60%;
        height: 60%;
        border: 3px solid #ff0000;
        background: transparent;
        pointer-events: none;
        z-index: 1000;
    }
    .camera-guide::before {
        content: "COLOCA EL OBJETO AQUÍ";
        position: absolute;
        top: -35px;
        left: 10px;
        color: #ff0000;
        font-weight: bold;
        font-size: 14px;
        background: white;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .guide-corners {
        position: absolute;
        width: 100%;
        height: 100%;
        pointer-events: none;
    }
    .corner {
        position: absolute;
        width: 20px;
        height: 20px;
        border: 2px solid #ff0000;
        background: transparent;
    }
    .corner-tl {
        top: -2px;
        left: -2px;
        border-right: none;
        border-bottom: none;
    }
    .corner-tr {
        top: -2px;
        right: -2px;
        border-left: none;
        border-bottom: none;
    }
    .corner-bl {
        bottom: -2px;
        left: -2px;
        border-right: none;
        border-top: none;
    }
    .corner-br {
        bottom: -2px;
        right: -2px;
        border-left: none;
        border-top: none;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Detector Simple de Colores")
    st.markdown("""
    **🎯 Colores que detecta:**
    - 🔴 ROJO
    - 🔵 AZUL  
    - 🟢 VERDE
    
    **📸 Instrucciones:**
    1. **Coloca el objeto dentro del cuadro rojo** en la cámara
    2. El cuadro te guiará en tiempo real
    3. Solo esa área se analizará
    4. Haz clic en **"Detectar Colores"**
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
    
    # Instructions
    st.info("🎯 **Coloca el objeto dentro del cuadro rojo que verás en la cámara**")
    
    # Container for camera with overlay
    st.markdown("""
    <div class="camera-overlay">
        <div class="camera-guide">
            <div class="guide-corners">
                <div class="corner corner-tl"></div>
                <div class="corner corner-tr"></div>
                <div class="corner corner-bl"></div>
                <div class="corner corner-br"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Camera input - this will appear below the overlay
    captured_image = st.camera_input(
        "Toma una foto del objeto - Asegúrate que esté dentro del cuadro rojo", 
        key="camera_with_overlay"
    )
    
    if captured_image is not None:
        original_image = Image.open(captured_image)
        
        # Show preview of what will be analyzed
        st.markdown("---")
        st.subheader("📷 Vista Previa del Análisis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📸 Foto completa capturada:**")
            st.image(original_image, caption="Así se vio en la cámara", use_container_width=True)
        
        with col2:
            st.markdown("**✂️ Área que se analizará:**")
            cropped_image = crop_to_guide_area(original_image)
            st.image(cropped_image, caption="Solo esta parte se analiza (60% central)", use_container_width=True)
        
        # Convert cropped image for upload
        image_bytes = pil_to_bytes(cropped_image)
        uploaded_file = type('obj', (object,), {
            'getvalue': lambda: image_bytes.getvalue(),
            'name': 'objeto_analizado.jpg'
        })
        
        st.success("✅ ¡Imagen preparada! Ahora haz clic en 'Detectar Colores'")

else:
    st.subheader("📁 Subir Imagen")
    
    uploaded_original = st.file_uploader("Sube una imagen del objeto", type=["jpg", "png", "jpeg"])
    
    if uploaded_original is not None:
        original_image = Image.open(uploaded_original)
        
        # Show the image with guide overlay using PIL
        st.subheader("📷 Vista Previa con Guía")
        
        # Create guide overlay for uploaded image
        img_with_guide = original_image.copy()
        draw = ImageDraw.Draw(img_with_guide)
        
        width, height = img_with_guide.size
        rect_width = int(width * 0.6)
        rect_height = int(height * 0.6)
        x1 = (width - rect_width) // 2
        y1 = (height - rect_height) // 2
        x2 = x1 + rect_width
        y2 = y1 + rect_height
        
        # Draw red rectangle
        draw.rectangle([x1, y1, x2, y2], outline="red", width=4)
        
        # Draw corners
        corner_size = 15
        draw.line([x1, y1, x1 + corner_size, y1], fill="red", width=3)
        draw.line([x1, y1, x1, y1 + corner_size], fill="red", width=3)
        draw.line([x2, y1, x2 - corner_size, y1], fill="red", width=3)
        draw.line([x2, y1, x2, y1 + corner_size], fill="red", width=3)
        draw.line([x1, y2, x1 + corner_size, y2], fill="red", width=3)
        draw.line([x1, y2, x1, y2 - corner_size], fill="red", width=3)
        draw.line([x2, y2, x2 - corner_size, y2], fill="red", width=3)
        draw.line([x2, y2, x2, y2 - corner_size], fill="red", width=3)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("**👀 Imagen con guía:**")
            st.image(img_with_guide, caption="Área de detección marcada", use_container_width=True)
        
        with col4:
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

# Additional styling for better mobile experience
st.markdown("""
<style>
    @media (max-width: 768px) {
        .camera-guide::before {
            font-size: 12px;
            top: -30px;
        }
    }
</style>
""", unsafe_allow_html=True)

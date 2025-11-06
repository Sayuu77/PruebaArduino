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
    draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
    
    # Add text
    draw.text((x1 + 10, y1 - 25), "COLOCA EL OBJETO AQUÍ", fill="red")
    
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
    **Colores que detecta:**
    - 🔴 ROJO
    - 🔵 AZUL  
    - 🟢 VERDE
    
    **Instrucciones:**
    1. Coloca el objeto en el cuadro rojo
    2. Solo el área dentro del cuadro se analiza
    3. Obtendrás SI/NO para cada color
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
    
    # Mostrar imagen de guía
    st.info("🔴 Coloca el objeto dentro del área roja")
    
    # Usar la cámara nativa de Streamlit
    captured_image = st.camera_input("Toma una foto del objeto")
    
    if captured_image is not None:
        original_image = Image.open(captured_image)
        
        # Mostrar la imagen original con guía
        st.subheader("📷 Vista previa")
        guide_image = add_guide_rectangle(original_image)
        st.image(guide_image, caption="Área de análisis", use_container_width=True)
        
        # Crear y mostrar la imagen recortada
        cropped_image = crop_to_guide_area(original_image)
        
        # Convertir imagen recortada a formato para upload
        image_bytes = pil_to_bytes(cropped_image)
        uploaded_file = type('obj', (object,), {
            'getvalue': lambda: image_bytes.getvalue(),
            'name': 'objeto_analizado.jpg'
        })
        
        st.success("✅ ¡Imagen lista para análisis!")

else:
    st.subheader("📁 Subir Imagen")
    
    uploaded_original = st.file_uploader("Sube una imagen del objeto", type=["jpg", "png", "jpeg"])
    
    if uploaded_original is not None:
        original_image = Image.open(uploaded_original)
        
        # Mostrar la imagen original con guía
        st.subheader("📷 Vista previa")
        guide_image = add_guide_rectangle(original_image)
        st.image(guide_image, caption="Área de análisis", use_container_width=True)
        
        # Crear y mostrar la imagen recortada
        cropped_image = crop_to_guide_area(original_image)
        
        # Convertir imagen recortada a formato para upload
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
        - Analiza solo el objeto principal
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
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if color_data.get("rojo", False):
                            st.success("🔴 ROJO: SÍ")
                        else:
                            st.error("🔴 ROJO: NO")
                    
                    with col2:
                        if color_data.get("azul", False):
                            st.success("🔵 AZUL: SÍ")
                        else:
                            st.error("🔵 AZUL: NO")
                    
                    with col3:
                        if color_data.get("verde", False):
                            st.success("🟢 VERDE: SÍ")
                        else:
                            st.error("🟢 VERDE: NO")
                            
                    # Resumen
                    st.markdown("---")
                    colors_found = []
                    if color_data.get("rojo"): colors_found.append("Rojo")
                    if color_data.get("azul"): colors_found.append("Azul")
                    if color_data.get("verde"): colors_found.append("Verde")
                    
                    if colors_found:
                        st.success(f"🎨 Colores detectados: {', '.join(colors_found)}")
                    else:
                        st.warning("❌ No se detectaron los colores rojo, azul o verde")
                        
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
with st.expander("💡 Cómo usar"):
    st.markdown("""
    ### 🎯 Instrucciones simples:
    1. **Coloca el objeto** en el área central
    2. **Haz clic en "Detectar Colores"**
    3. **Obtén resultados** SI/NO para cada color
    
    ### 🔍 Qué detecta:
    - **ROJO**: Tonos rojos en el objeto
    - **AZUL**: Tonos azules en el objeto  
    - **VERDE**: Tonos verdes en el objeto
    
    ### 💡 Consejo:
    - Usa buena iluminación
    - Enfoca bien el objeto
    - Colócalo en el centro
    """)

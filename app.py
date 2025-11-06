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
    draw.text((x1 + 10, y1 - 25), "ZONA DE ANÁLISIS", fill="red")
    draw.text((x1 + 10, y2 + 5), "Solo esta área será analizada", fill="red")
    
    return img

# Function to convert PIL image to bytes for upload
def pil_to_bytes(pil_image):
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

st.set_page_config(page_title="Analizador de Colores de Objetos", layout="centered", initial_sidebar_state="collapsed")

# Streamlit page setup
st.title("Analizador de Colores de Objetos:🎨📦")

try:
    image = Image.open('OIG4.jpg')
    st.image(image, width=350)
except:
    st.markdown("### 🎨 Analizador de Colores de Objetos")

with st.sidebar:
    st.subheader("Analiza exclusivamente colores de objetos")
    st.markdown("""
    **Instrucciones:**
    1. Coloca el objeto en el cuadro rojo
    2. Solo el área dentro del cuadro será analizada
    3. El fondo exterior se eliminará
    4. Buena iluminación sin sombras
    
    **Zona de análisis:**
    - 60% central de la imagen
    - Fondo exterior ignorado
    - Enfoque solo en el objeto
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
original_image = None

if image_source == "Cámara Web":
    st.subheader("📸 Captura desde Cámara")
    
    # Mostrar imagen de guía
    st.info("🔴 Coloca el objeto completamente dentro del área roja")
    
    # Crear imagen de guía temporal
    guide_img = Image.new('RGB', (400, 300), color='white')
    guide_img_with_rect = add_guide_rectangle(guide_img)
    st.image(guide_img_with_rect, caption="Guía de posicionamiento - Solo el área roja se analizará", 
             use_container_width=False)
    
    # Usar la cámara nativa de Streamlit
    captured_image = st.camera_input("Toma una foto del objeto")
    
    if captured_image is not None:
        original_image = Image.open(captured_image)
        
        # Mostrar la imagen original con guía
        st.subheader("📷 Vista previa con área de análisis")
        guide_image = add_guide_rectangle(original_image)
        st.image(guide_image, caption="Área que será analizada (dentro del recuadro rojo)", 
                use_container_width=True)
        
        # Crear y mostrar la imagen recortada
        cropped_image = crop_to_guide_area(original_image)
        st.subheader("✂️ Imagen que se analizará")
        st.image(cropped_image, caption="Esta es la imagen que se enviará para análisis (recortada)", 
                use_container_width=True)
        
        # Convertir imagen recortada a formato para upload
        image_bytes = pil_to_bytes(cropped_image)
        uploaded_file = type('obj', (object,), {
            'getvalue': lambda: image_bytes.getvalue(),
            'name': 'objeto_analizado.jpg'
        })
        
        st.success("✅ ¡Imagen preparada! Haz clic en 'Analizar Colores del Objeto'")

else:
    st.subheader("📁 Subir Imagen")
    st.info("🔴 El objeto debe estar en el área central - solo esa parte se analizará")
    
    uploaded_original = st.file_uploader("Sube una imagen del objeto", type=["jpg", "png", "jpeg"], 
                                       help="El objeto debe estar en el centro de la imagen")
    
    if uploaded_original is not None:
        original_image = Image.open(uploaded_original)
        
        # Mostrar la imagen original con guía
        st.subheader("📷 Vista previa con área de análisis")
        guide_image = add_guide_rectangle(original_image)
        st.image(guide_image, caption="Área que será analizada (dentro del recuadro rojo)", 
                use_container_width=True)
        
        # Crear y mostrar la imagen recortada
        cropped_image = crop_to_guide_area(original_image)
        st.subheader("✂️ Imagen que se analizará")
        st.image(cropped_image, caption="Esta es la imagen que se enviará para análisis (recortada)", 
                use_container_width=True)
        
        # Convertir imagen recortada a formato para upload
        image_bytes = pil_to_bytes(cropped_image)
        uploaded_file = type('obj', (object,), {
            'getvalue': lambda: image_bytes.getvalue(),
            'name': 'objeto_analizado.jpg'
        })

# Tipo de análisis específico para objetos
analysis_type = st.selectbox(
    "🔍 Tipo de análisis:",
    ["Análisis Completo del Objeto", "Paleta de Colores Principal", "Colores Exactos", "Análisis para Diseño"]
)

# Toggle for showing additional details input
show_details = st.toggle("🎯 Especificar tipo de objeto", value=False)

if show_details:
    additional_details = st.text_area(
        "Describe el objeto y qué colores te interesan:",
        placeholder="Ej: 'Una botella de plástico azul', 'Una manzana roja', 'Un tejido con patrones multicolor'...",
        help="Describe el objeto para un análisis más preciso"
    )

# Button to trigger the analysis
analyze_button = st.button("🎨 Analizar Colores del Objeto", type="primary", use_container_width=True)

# Check if an image has been uploaded and API key is available
if uploaded_file is not None and api_key and analyze_button:

    with st.spinner("🔍 Analizando colores del objeto... Esto puede tomar unos segundos"):
        # Encode the cropped image
        base64_image = encode_image(uploaded_file)
    
        # Base prompt for object color analysis
        base_prompt = """Eres un experto en análisis de color de objetos. 
        Analiza EXCLUSIVAMENTE los colores del OBJETO en la imagen. 
        Esta imagen ya ha sido recortada para mostrar solo el objeto de interés.
        
        Responde EXCLUSIVAMENTE en español enfocándote solo en los colores visibles."""
        
        # Customize prompt based on analysis type
        if analysis_type == "Análisis Completo del Objeto":
            prompt_text = base_prompt + """
            Proporciona un análisis completo de los colores del objeto:

            ## 🎨 COLORES PRINCIPALES DEL OBJETO
            - 3-5 colores dominantes con porcentajes
            - Códigos HEX y RGB exactos de cada color
            - Nombres descriptivos de los colores

            ## 🔍 CARACTERÍSTICAS TÉCNICAS
            - Temperatura de color (cálido/frío/neutral)
            - Saturación y brillo predominantes
            - Textura y acabado sugeridos por los colores

            ## 📊 COMPOSICIÓN CROMÁTICA
            - Distribución de colores en el objeto
            - Patrones o gradientes identificados
            - Acabados (mate, brillo, transparente, etc.)

            Formato: Usa markdown con organización clara y profesional.
            """
            
        elif analysis_type == "Paleta de Colores Principal":
            prompt_text = base_prompt + """
            Enfócate específicamente en la paleta de colores del objeto:

            ## 🎨 PALETA PRINCIPAL DEL OBJETO
            - 4-6 colores principales con códigos HEX exactos
            - Porcentaje de cada color en el objeto
            - Colores base y acentos

            ## 🔄 VARIACIONES Y MATICES
            - Diferentes tonalidades presentes
            - Gradientes o transiciones de color

            Incluye TODOS los códigos HEX para cada color del objeto.
            """
            
        elif analysis_type == "Colores Exactos":
            prompt_text = base_prompt + """
            Identifica específicamente los colores exactos del objeto:

            ## 🎯 COLORES EXACTOS IDENTIFICADOS
            - Lista ordenada de colores por predominancia
            - Códigos HEX, RGB exactos
            - Porcentaje estimado de cada color

            ## 🏷️ ESPECIFICACIONES TÉCNICAS
            - Nombres descriptivos de los colores
            - Familia cromática de cada color

            Formato: Lista detallada con todos los códigos técnicos.
            """
            
        else:  # Análisis para Diseño
            prompt_text = base_prompt + """
            Enfócate en aplicaciones de diseño con los colores del objeto:

            ## 🎨 APLICACIONES EN DISEÑO
            - Usos en diseño de producto
            - Aplicaciones en branding
            - Compatibilidad con tendencias

            ## 💼 RECOMENDACIONES COMERCIALES
            - Públicos que atraerían estos colores
            - Contextos de uso recomendados

            Incluye recomendaciones prácticas basadas en los colores del objeto.
            """
    
        # Add object description if provided
        if show_details and additional_details:
            prompt_text += f"\n\nDESCRIPCIÓN DEL OBJETO:\n{additional_details}"
    
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
                max_tokens=1500,
            )
            
            # Display the response
            if response.choices[0].message.content:
                st.markdown("---")
                st.subheader("📊 Resultados del Análisis del Objeto")
                st.markdown(response.choices[0].message.content)
                
                # Mostrar recordatorio de que se usó imagen recortada
                st.info("💡 *Análisis basado únicamente en el área recortada del objeto*")
    
        except Exception as e:
            st.error(f"❌ Ocurrió un error: {e}")
            st.info("Por favor verifica tu API key e intenta nuevamente")
            
else:
    # Warnings for user action required
    if not uploaded_file and analyze_button:
        st.warning("⚠️ Por favor captura o sube una imagen del objeto primero.")
    if not api_key and analyze_button:
        st.warning("🔑 Por favor ingresa tu API key de OpenAI.")

# Additional tips section for object analysis
with st.expander("💡 Cómo usar el área de análisis"):
    st.markdown("""
    ### 🎯 Zona de análisis:
    - **Solo el área dentro del recuadro rojo** se analiza
    - **El 60% central** de la imagen es lo que importa
    - **Fondo exterior eliminado** automáticamente
    - **Enfoque exclusivo** en el objeto

    ### 📸 Para mejores resultados:
    - **Centra el objeto** completamente dentro del área roja
    - **Ajusta la distancia** para que el objeto ocupe la mayor parte del área
    - **Fondo simple** ayuda al recorte
    - **Buena iluminación** para colores precisos

    ### ✅ Ventajas del recorte automático:
    - Elimina distracciones del fondo
    - Enfoca solo en el objeto de interés
    - Mejora la precisión del análisis
    - Elimina elementos no deseados
    """)

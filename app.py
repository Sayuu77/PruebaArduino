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

# Function to add guide rectangle to image
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
    2. Evita incluir personas en la foto
    3. Usa fondo neutro para mejor resultado
    4. Buena iluminación sin sombras
    
    **Funcionalidades:**
    - Detecta colores de objetos
    - Proporciona códigos HEX y RGB
    - Sugiere combinaciones armónicas
    - Análisis técnico de colores
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
guide_image = None

if image_source == "Cámara Web":
    st.subheader("📸 Captura desde Cámara")
    
    # Mostrar imagen de guía primero
    st.info("🔴 Coloca el objeto en el área central de la cámara")
    
    # Crear imagen de guía temporal
    guide_img = Image.new('RGB', (400, 300), color='white')
    guide_img_with_rect = add_guide_rectangle(guide_img)
    st.image(guide_img_with_rect, caption="Guía de posicionamiento", use_container_width=False)
    
    # Usar la cámara nativa de Streamlit
    captured_image = st.camera_input("Toma una foto del objeto")
    
    if captured_image is not None:
        uploaded_file = captured_image
        # Mostrar la imagen capturada con el cuadro guía
        pil_image = Image.open(captured_image)
        guide_image = add_guide_rectangle(pil_image)
        st.image(guide_image, caption="Tu objeto - Área de análisis marcada", use_container_width=True)
        st.success("¡Foto capturada! Haz clic en 'Analizar Colores del Objeto'")

else:
    st.subheader("📁 Subir Imagen")
    st.info("🔴 La imagen debe mostrar principalmente el objeto, sin personas")
    
    uploaded_file = st.file_uploader("Sube una imagen del objeto", type=["jpg", "png", "jpeg"], 
                                   help="Imágenes de objetos, productos, materiales, etc.")
    
    if uploaded_file is not None:
        # Mostrar imagen con cuadro guía
        pil_image = Image.open(uploaded_file)
        guide_image = add_guide_rectangle(pil_image)
        st.image(guide_image, caption="Tu objeto - Área de análisis marcada", use_container_width=True)

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
        # Encode the image
        base64_image = encode_image(uploaded_file)
    
        # Base prompt for object color analysis
        base_prompt = """Eres un experto en análisis de color de objetos. 
        Analiza EXCLUSIVAMENTE los colores del OBJETO en la imagen, ignorando completamente:
        - Personas, caras o figuras humanas
        - Fondos y entorno
        - Elementos secundarios
        
        Responde EXCLUSIVAMENTE en español enfocándote solo en los colores del objeto principal."""
        
        # Customize prompt based on analysis type
        if analysis_type == "Análisis Completo del Objeto":
            prompt_text = base_prompt + """
            Proporciona un análisis completo de los colores del objeto:

            ## 🎨 COLORES PRINCIPALES DEL OBJETO
            - 3-5 colores dominantes del objeto con porcentajes
            - Códigos HEX y RGB exactos de cada color
            - Nombres descriptivos de los colores

            ## 🔍 CARACTERÍSTICAS TÉCNICAS
            - Temperatura de color del objeto (cálido/frío/neutral)
            - Saturación y brillo predominantes
            - Textura y acabado sugeridos por los colores

            ## 📊 COMPOSICIÓN CROMÁTICA
            - Distribución de colores en el objeto
            - Patrones o gradientes identificados
            - Acabados (mate, brillo, transparente, etc.)

            ## 💡 APLICACIONES PRÁCTICAS
            - Usos recomendados basados en los colores
            - Combinaciones armónicas sugeridas
            - Compatibilidad con otros materiales

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
            - Efectos visuales (metalizado, perlado, etc.)

            ## ✨ COMBINACIONES RECOMENDADAS
            - 3 combinaciones armónicas con los colores del objeto
            - Esquemas de color que complementan el objeto

            Incluye TODOS los códigos HEX para cada color del objeto.
            """
            
        elif analysis_type == "Colores Exactos":
            prompt_text = base_prompt + """
            Identifica específicamente los colores exactos del objeto:

            ## 🎯 COLORES EXACTOS IDENTIFICADOS
            - Lista ordenada de colores por predominancia
            - Códigos HEX, RGB y CMYK exactos
            - Porcentaje estimado de cada color en el objeto

            ## 🏷️ ESPECIFICACIONES TÉCNICAS
            - Nombres comerciales/industriales de los colores
            - Familia cromática de cada color
            - Valores HSL detallados

            ## 📐 PRECISIÓN DE COLOR
            - Nivel de uniformidad del color
            - Variaciones detectadas
            - Consistencia cromática

            Formato: Lista detallada con todos los códigos técnicos.
            """
            
        else:  # Análisis para Diseño
            prompt_text = base_prompt + """
            Enfócate en aplicaciones de diseño con los colores del objeto:

            ## 🎨 APLICACIONES EN DISEÑO
            - Usos en diseño de producto
            - Aplicaciones en branding y packaging
            - Compatibilidad con tendencias actuales

            ## 🏭 USOS INDUSTRIALES
            - Aplicaciones en manufactura
            - Materiales sugeridos por los colores
            - Mercados objetivo apropiados

            ## 💼 RECOMENDACIONES COMERCIALES
            - Públicos que atraerían estos colores
            - Contextos de uso recomendados
            - Valor percibido del objeto por sus colores

            Incluye recomendaciones prácticas basadas en los colores del objeto.
            """
    
        # Add object description if provided
        if show_details and additional_details:
            prompt_text += f"\n\nDESCRIPCIÓN DEL OBJETO:\n{additional_details}"
        else:
            prompt_text += "\n\nSi no se proporciona descripción, analiza los colores del objeto principal visible."
    
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
with st.expander("💡 Consejos para análisis de objetos"):
    st.markdown("""
    ### 📸 Para mejores resultados con objetos:
    - **Posicionamiento**: Coloca el objeto en el centro del cuadro rojo
    - **Fondo**: Usa fondos neutros (blanco, gris, negro)
    - **Iluminación**: Luz uniforme sin sombras fuertes
    - **Enfoque**: Imagen nítida del objeto
    - **Ángulo**: Muestra la superficie principal del objeto

    ### 🚫 Qué evitar:
    - Personas en la imagen
    - Múltiples objetos mezclados
    - Fondos con patrones complejos
    - Reflexiones y brillos excesivos
    - Sombras que distorsionen los colores

    ### ✅ Objetos ideales para análisis:
    - Productos y packaging
    - Materiales y textiles
    - Objetos de diseño
    - Elementos naturales (frutas, flores, minerales)
    - Artículos de decoración
    """)

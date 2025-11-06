import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import io

# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

st.set_page_config(page_title="Analizador de Colores", layout="centered", initial_sidebar_state="collapsed")

# Streamlit page setup
st.title("Analizador de Colores por Cámara:🎨📷")

# Logo de la aplicación (opcional - si no tienes la imagen, comenta esta línea)
try:
    image = Image.open('OIG4.jpg')
    st.image(image, width=350)
except:
    st.markdown("### 🎨 Analizador de Colores Profesional")

with st.sidebar:
    st.subheader("Este Agente analiza los colores de imágenes capturadas por cámara.")
    st.markdown("""
    **Funcionalidades:**
    - Captura imágenes con la cámara
    - Analiza paleta de colores
    - Identifica colores dominantes
    - Proporciona códigos HEX y RGB
    - Sugiere combinaciones armónicas
    """)

ke = st.text_input('Ingresa tu Clave de OpenAI', type="password")
if ke:
    os.environ['OPENAI_API_KEY'] = ke

# Initialize the OpenAI client with the API key
api_key = os.environ.get('OPENAI_API_KEY')

# Image source selection
image_source = st.radio("Selecciona la fuente de la imagen:", 
                        ["Cámara Web", "Subir Archivo"], 
                        horizontal=True)

uploaded_file = None

if image_source == "Cámara Web":
    st.subheader("📸 Captura desde Cámara")
    st.info("Usa la cámara integrada para tomar una foto")
    
    # Usar la cámara nativa de Streamlit
    captured_image = st.camera_input("Toma una foto para analizar los colores")
    
    if captured_image is not None:
        uploaded_file = captured_image
        st.success("¡Foto capturada exitosamente! Ahora haz clic en 'Analizar Colores'")

else:
    st.subheader("📁 Subir Imagen")
    uploaded_file = st.file_uploader("Sube una imagen", type=["jpg", "png", "jpeg"], 
                                   help="Formatos soportados: JPG, PNG, JPEG")

if uploaded_file:
    # Display the image
    with st.expander("👀 Vista Previa de la Imagen", expanded=True):
        st.image(uploaded_file, caption="Imagen para analizar", use_container_width=True)
        
        # Mostrar información básica de la imagen
        try:
            image = Image.open(uploaded_file)
            st.write(f"**Dimensiones:** {image.size[0]} x {image.size[1]} píxeles")
            st.write(f"**Formato:** {image.format}")
        except:
            pass

# Tipo de análisis
analysis_type = st.selectbox(
    "🔍 Tipo de análisis:",
    ["Análisis Completo", "Paleta de Colores", "Colores Dominantes", "Análisis Emocional"]
)

# Toggle for showing additional details input
show_details = st.toggle("🎯 Personalizar análisis", value=False)

if show_details:
    additional_details = st.text_area(
        "Especifica qué aspectos del color quieres analizar:",
        placeholder="Ej: Analizar colores dominantes, sugerir paletas armónicas, identificar colores complementarios, análisis psicológico del color...",
        help="Cuanto más específico seas, mejor será el análisis"
    )

# Button to trigger the analysis
analyze_button = st.button("🎨 Analizar Colores", type="primary", use_container_width=True)

# Check if an image has been uploaded and API key is available
if uploaded_file is not None and api_key and analyze_button:

    with st.spinner("🔍 Analizando colores... Esto puede tomar unos segundos"):
        # Encode the image
        base64_image = encode_image(uploaded_file)
    
        # Base prompt for color analysis
        base_prompt = """Eres un experto en análisis de color, teoría del color y diseño. 
        Analiza la imagen proporcionada y responde EXCLUSIVAMENTE en español con un análisis profesional."""
        
        # Customize prompt based on analysis type
        if analysis_type == "Análisis Completo":
            prompt_text = base_prompt + """
            Proporciona un análisis completo que incluya:

            ## 🎨 PALETA DE COLORES
            - Colores dominantes con porcentajes aproximados
            - Códigos HEX, RGB y nombres de cada color principal
            - Paleta completa identificada

            ## 🔍 ANÁLISIS TÉCNICO
            - Temperatura de color (cálido/frío/neutral)
            - Saturación y brillo general
            - Nivel de contraste

            ## 💫 ANÁLISIS EMOCIONAL
            - Estados de ánimo que transmite
            - Sensaciones y emociones asociadas
            - Contextos apropiados para esta paleta

            ## 💡 RECOMENDACIONES PRÁCTICAS
            - Uso en diseño gráfico
            - Aplicación en decoración
            - Combinaciones armónicas sugeridas

            Formato: Usa markdown con encabezados claros y organización profesional.
            """
            
        elif analysis_type == "Paleta de Colores":
            prompt_text = base_prompt + """
            Enfócate específicamente en la paleta de colores:

            ## 🎨 PALETA PRINCIPAL
            - 5-7 colores principales con códigos HEX exactos
            - Porcentaje aproximado de cada color en la imagen

            ## 🔄 VARIACIONES Y TONALIDADES
            - Tonalidades claras y oscuras presentes
            - Gradientes identificados

            ## ✨ COMBINACIONES SUGERIDAS
            - 3 combinaciones armónicas con los colores identificados
            - Esquemas de color recomendados (análogo, complementario, etc.)

            Incluye todos los códigos HEX para cada color mencionado.
            """
            
        elif analysis_type == "Colores Dominantes":
            prompt_text = base_prompt + """
            Identifica específicamente los colores dominantes:

            ## 🏆 TOP 5 COLORES DOMINANTES
            - Lista ordenada por predominancia
            - Porcentaje estimado de cada color
            - Códigos EXACTOS (HEX, RGB)

            ## 📊 DISTRIBUCIÓN CROMÁTICA
            - Cómo se distribuyen los colores en la imagen
            - Puntos focales de color

            ## 🏷️ NOMENCLATURA
            - Nombres descriptivos/comerciales de cada color
            - Familia cromática de cada color

            Formato: Lista o tabla clara con todos los códigos.
            """
            
        else:  # Análisis Emocional
            prompt_text = base_prompt + """
            Enfócate en el aspecto emocional y psicológico:

            ## 😊 IMPACTO EMOCIONAL
            - Estados de ánimo que evoca la paleta
            - Sensaciones principales transmitidas
            - Asociaciones psicológicas de los colores

            ## 🏛️ CONTEXTOS APROPIADOS
            - Usos recomendados (branding, interiorismo, etc.)
            - Industrias o sectores adecuados
            - Público objetivo ideal

            ## 💭 MENSAJE Y COMUNICACIÓN
            - Qué comunica esta combinación de colores
            - Valores y atributos asociados
            - Personalidad de la paleta

            Incluye recomendaciones específicas basadas en la psicología del color.
            """
    
        # Add user context if provided
        if show_details and additional_details:
            prompt_text += f"\n\nCONTEXTO ADICIONAL DEL USUARIO:\n{additional_details}"
    
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
                st.subheader("📊 Resultados del Análisis")
                st.markdown(response.choices[0].message.content)
    
        except Exception as e:
            st.error(f"❌ Ocurrió un error: {e}")
            st.info("Por favor verifica tu API key e intenta nuevamente")
            
else:
    # Warnings for user action required
    if not uploaded_file and analyze_button:
        st.warning("⚠️ Por favor captura o sube una imagen primero.")
    if not api_key and analyze_button:
        st.warning("🔑 Por favor ingresa tu API key de OpenAI.")

# Additional tips section
with st.expander("💡 Consejos para un mejor análisis de color"):
    st.markdown("""
    ### 📸 Para mejores resultados:
    - **Iluminación**: Buena luz natural o artificial uniforme
    - **Enfoque**: Imágenes nítidas y bien enfocadas
    - **Composición**: Enfoca el área con los colores que te interesan
    - **Fondo**: Fondos neutros ayudan a aislar los colores principales
    
    ### 🎨 Tipos de imágenes ideales:
    - Fotografías de productos o objetos
    - Imágenes de naturaleza y paisajes
    - Diseños gráficos y obras de arte
    - Interiores y espacios decorados
    
    ### 🔧 Para análisis específicos:
    - **Diseño**: Especifica si es para web, print, branding, etc.
    - **Decoración**: Menciona el espacio o estilo deseado
    - **Arte**: Indica el estilo o técnica que te interesa
    """)

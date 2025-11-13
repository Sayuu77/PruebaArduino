import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image, ImageDraw
import io
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import time
import paho.mqtt.client as paho
import json
from gtts import gTTS
from googletrans import Translator

# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

# Function to crop image to the guide area
def crop_to_guide_area(image):
    """Crop image to only include the guide rectangle area"""
    width, height = image.size
    
    # Calculate crop area (70% of image size, centered)
    crop_width = int(width * 0.7)
    crop_height = int(height * 0.7)
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    right = left + crop_width
    bottom = top + crop_height
    
    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))
    
    return cropped_image

# Function to add guide rectangle to image
def add_guide_rectangle(image):
    """Add a guide rectangle directly to the image"""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    
    # Calculate rectangle dimensions (70% of image size, centered)
    width, height = img.size
    rect_width = int(width * 0.7)
    rect_height = int(height * 0.7)
    x1 = (width - rect_width) // 2
    y1 = (height - rect_height) // 2
    x2 = x1 + rect_width
    y2 = y1 + rect_height
    
    # Draw thick red rectangle
    for i in range(4):  # Multiple lines for thicker border
        draw.rectangle([x1-i, y1-i, x2+i, y2+i], outline="red", width=1)
    
    # Add corner markers
    corner_size = 25
    # Top-left corner
    draw.line([x1, y1, x1 + corner_size, y1], fill="red", width=4)
    draw.line([x1, y1, x1, y1 + corner_size], fill="red", width=4)
    # Top-right corner
    draw.line([x2, y1, x2 - corner_size, y1], fill="red", width=4)
    draw.line([x2, y1, x2, y1 + corner_size], fill="red", width=4)
    # Bottom-left corner
    draw.line([x1, y2, x1 + corner_size, y2], fill="red", width=4)
    draw.line([x1, y2, x1, y2 - corner_size], fill="red", width=4)
    # Bottom-right corner
    draw.line([x2, y2, x2 - corner_size, y2], fill="red", width=4)
    draw.line([x2, y2, x2, y2 - corner_size], fill="red", width=4)
    
    # Add instructional text with background
    text = "COLOCA EL OBJETO DENTRO DEL CUADRO ROJO"
    text_width = draw.textlength(text)
    text_x = (width - text_width) // 2
    text_y = y1 - 40
    
    # Text background
    draw.rectangle([text_x-10, text_y-5, text_x + text_width + 10, text_y + 20], 
                   fill="white", outline="red", width=2)
    
    # Text
    draw.text((text_x, text_y), text, fill="red", stroke_width=1, stroke_fill="white")
    
    return img

# Function to convert PIL image to bytes for upload
def pil_to_bytes(pil_image):
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

# Callbacks MQTT
def on_publish(client, userdata, result):
    st.toast("Comando enviado exitosamente", icon="✅")

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.session_state.last_received = message_received

# Configuración MQTT
broker = "broker.mqttdashboard.com"
port = 1883

# Configuración de página
st.set_page_config(
    page_title="Sistema IoT: Voz + Visión",
    page_icon="🎤",
    layout="wide"
)

# Estilos CSS modernos
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        color: #7E57C2;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #7E57C2, #BA68C8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    .section-title {
        font-size: 1.5rem;
        color: #7E57C2;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #D1C4E9;
        padding-bottom: 0.5rem;
    }
    .mic-button {
        background: linear-gradient(135deg, #7E57C2, #BA68C8);
        color: white;
        border: none;
        border-radius: 50%;
        width: 100px;
        height: 100px;
        font-size: 2.5rem;
        margin: 1rem auto;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(126, 87, 194, 0.3);
    }
    .mic-button:hover {
        transform: scale(1.05);
        box-shadow: 0 12px 35px rgba(126, 87, 194, 0.4);
    }
    .result-box {
        background: white;
        border: 2px solid #7E57C2;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .status-indicator {
        display: inline-flex;
        align-items: center;
        background: #E8F5E8;
        color: #2E7D32;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        margin: 0.5rem 0;
    }
    .status-indicator-off {
        display: inline-flex;
        align-items: center;
        background: #FFEBEE;
        color: #C62828;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        margin: 0.5rem 0;
    }
    .pulse {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .command-list {
        background: #F8F9FA;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .command-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-left: 4px solid;
        background: white;
    }
    .led-amarillo { border-left-color: #FFEB3B; }
    .led-rojo { border-left-color: #F44336; }
    .led-verde { border-left-color: #4CAF50; }
    .led-todos { border-left-color: #9C27B0; }
    .luz-principal { border-left-color: #2196F3; }
    .puerta { border-left-color: #FF9800; }
    .camera-section { border-left-color: #E91E63; }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'last_command' not in st.session_state:
    st.session_state.last_command = ""
if 'last_received' not in st.session_state:
    st.session_state.last_received = ""
if 'color_results' not in st.session_state:
    st.session_state.color_results = None

# Header principal
st.markdown('<div class="main-title">🤖 Sistema IoT: Control por Voz + Visión</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Controla dispositivos con comandos de voz y detección de colores por cámara</div>', unsafe_allow_html=True)

# Sidebar con información
with st.sidebar:
    st.subheader("🎯 Comandos Disponibles")
    st.markdown("""
    <div class="command-list">
        <div class="command-item led-amarillo"><strong>💡 Enciende el amarillo</strong></div>
        <div class="command-item led-amarillo"><strong>🔌 Apaga el amarillo</strong></div>
        
        <div class="command-item led-rojo"><strong>🔴 Enciende el rojo</strong></div>
        <div class="command-item led-rojo"><strong>🔌 Apaga el rojo</strong></div>
        
        <div class="command-item led-verde"><strong>🟢 Enciende el verde</strong></div>
        <div class="command-item led-verde"><strong>🔌 Apaga el verde</strong></div>
        
        <div class="command-item led-todos"><strong>🌈 Enciende todos</strong></div>
        <div class="command-item led-todos"><strong>🔌 Apaga todos</strong></div>
        
        <div class="command-item luz-principal"><strong>💡 Enciende la luz</strong></div>
        <div class="command-item luz-principal"><strong>🔌 Apaga la luz</strong></div>
        
        <div class="command-item puerta"><strong>🚪 Abre la puerta</strong></div>
        <div class="command-item puerta"><strong>🚪 Cierra la puerta</strong></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🔧 Configuración")
    ke = st.text_input('Clave de OpenAI', type="password")
    if ke:
        os.environ['OPENAI_API_KEY'] = ke

    api_key = os.environ.get('OPENAI_API_KEY')
    
    if api_key:
        st.success("✅ API Key configurada")
    else:
        st.warning("🔑 Ingresa tu API Key")

# Crear pestañas para las diferentes funcionalidades
tab1, tab2, tab3 = st.tabs(["🎤 Control por Voz", "📷 Detección de Colores", "📊 Estado del Sistema"])

with tab1:
    st.markdown('<div class="section-title">🎤 Control por Comandos de Voz</div>', unsafe_allow_html=True)
    
    col_mic, col_commands = st.columns([1, 2])
    
    with col_mic:
        st.markdown('<div class="mic-button pulse">🎤</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #666;">Haz clic y habla</div>', unsafe_allow_html=True)
        
        # Botón de reconocimiento de voz
        stt_button = Button(label=" Iniciar Reconocimiento ", width=200, height=50, 
                           button_type="success")
        stt_button.js_on_event("button_click", CustomJS(code="""
            var recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'es-ES';

            recognition.onresult = function (e) {
                var value = e.results[0][0].transcript;
                if ( value != "") {
                    document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
                }
            }

            recognition.onerror = function(e) {
                document.dispatchEvent(new CustomEvent("RECORDING_ERROR", {detail: e.error}));
            }

            recognition.start();
        """))

        # Procesar eventos de voz
        result = streamlit_bokeh_events(
            stt_button,
            events="GET_TEXT,RECORDING_ERROR",
            key="listen",
            refresh_on_update=False,
            override_height=50,
            debounce_time=0
        )

    with col_commands:
        if result:
            if "GET_TEXT" in result:
                command = result.get("GET_TEXT").strip()
                
                # Normalizar el comando
                command = command.lower().strip(' .!?')
                st.session_state.last_command = command
                
                # Mostrar comando reconocido
                st.markdown("### 🎯 Comando Reconocido")
                st.markdown(f'<div class="result-box"><span style="font-size: 1.4rem; color: #7E57C2; font-weight: 600;">"{command}"</span></div>', unsafe_allow_html=True)
                
                # Mapeo de comandos
                command_mapping = {
                    # Comandos para ENCENDER
                    'enciende el amarillo': 'enciende amarillo',
                    'prende el amarillo': 'enciende amarillo',
                    'enciende amarillo': 'enciende amarillo',
                    'enciende el rojo': 'enciende rojo',
                    'prende el rojo': 'enciende rojo',
                    'enciende rojo': 'enciende rojo',
                    'enciende el verde': 'enciende verde',
                    'prende el verde': 'enciende verde',
                    'enciende verde': 'enciende verde',
                    'enciende todos los leds': 'enciende todos los leds',
                    
                    # Comandos para APAGAR
                    'apaga el amarillo': 'apaga amarillo',
                    'apaga amarillo': 'apaga amarillo',
                    'apaga el rojo': 'apaga rojo',
                    'apaga rojo': 'apaga rojo',
                    'apaga el verde': 'apaga verde',
                    'apaga verde': 'apaga verde',
                    'apaga todos los leds': 'apaga todos los leds',
                    
                    # Otros comandos
                    'enciende la luz': 'enciende luz',
                    'apaga la luz': 'apaga luz',
                    'abre la puerta': 'abre puerta',
                    'cierra la puerta': 'cierra puerta',
                    
                    # Comandos simples
                    'amarillo': 'enciende amarillo',
                    'rojo': 'enciende rojo',
                    'verde': 'enciende verde',
                }
                
                normalized_command = command_mapping.get(command, command)
                
                # Enviar comando por MQTT
                try:
                    client1 = paho.Client("streamlit-voice-control")
                    client1.on_publish = on_publish
                    client1.connect(broker, port)
                    message = json.dumps({"Act1": normalized_command})
                    ret = client1.publish("appcolor", message)
                    
                    if normalized_command.startswith('enciende'):
                        st.toast(f"💡 Encendiendo: {normalized_command}", icon="✅")
                    elif normalized_command.startswith('apaga'):
                        st.toast(f"🔌 Apagando: {normalized_command}", icon="🔴")
                    else:
                        st.toast(f"📡 Comando enviado: {normalized_command}", icon="✅")
                        
                    time.sleep(1)
                    client1.disconnect()
                except Exception as e:
                    st.error(f"❌ Error al enviar comando: {e}")

with tab2:
    st.markdown('<div class="section-title">📷 Detección de Colores por Cámara</div>', unsafe_allow_html=True)
    
    # Image source selection
    image_source = st.radio("Selecciona la fuente de la imagen:", 
                            ["Cámara Web", "Subir Archivo"], 
                            horizontal=True)

    uploaded_file = None
    cropped_image = None

    if image_source == "Cámara Web":
        st.info("🔴 **Coloca el objeto dentro del cuadro rojo y toma la foto**")
        
        # Cámara real
        captured_image = st.camera_input("Toma una foto del objeto", key="color_camera")
        
        if captured_image is not None:
            original_image = Image.open(captured_image)
            
            # Procesar imagen
            image_with_guide = add_guide_rectangle(original_image)
            cropped_image = crop_to_guide_area(original_image)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(image_with_guide, caption="Vista con guía", use_container_width=True)
            
            with col2:
                st.image(cropped_image, caption="Área de análisis", use_container_width=True)
            
            # Convertir para upload
            image_bytes = pil_to_bytes(cropped_image)
            uploaded_file = type('obj', (object,), {
                'getvalue': lambda: image_bytes.getvalue(),
                'name': 'objeto_analizado.jpg'
            })
            
            st.success("🎯 ¡Imagen lista para análisis!")

    else:
        uploaded_original = st.file_uploader("Sube una imagen del objeto", type=["jpg", "png", "jpeg"])
        
        if uploaded_original is not None:
            original_image = Image.open(uploaded_original)
            
            # Procesar imagen subida
            image_with_guide = add_guide_rectangle(original_image)
            cropped_image = crop_to_guide_area(original_image)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(image_with_guide, caption="Imagen con área de detección", use_container_width=True)
            
            with col2:
                st.image(cropped_image, caption="Área que se analizará", use_container_width=True)
            
            # Convertir para upload
            image_bytes = pil_to_bytes(cropped_image)
            uploaded_file = type('obj', (object,), {
                'getvalue': lambda: image_bytes.getvalue(),
                'name': 'objeto_analizado.jpg'
            })

    # Button to trigger the analysis
    analyze_button = st.button("🔍 Analizar Colores y Encender LEDs", type="primary", use_container_width=True)

    # Análisis de colores
    if uploaded_file is not None and api_key and analyze_button:
        with st.spinner("🎨 Analizando colores y controlando LEDs..."):
            # Encode the cropped image
            base64_image = encode_image(uploaded_file)
        
            # Prompt para detección de colores (amarillo, rojo, verde)
            prompt_text = """
            Analiza ESTA imagen y responde SOLO con un JSON que contenga:
            
            {
                "rojo": true/false,
                "amarillo": true/false, 
                "verde": true/false
            }
            
            Reglas:
            - "true" si el color está presente en el objeto principal
            - "false" si el color NO está presente  
            - Analiza SOLO el objeto dentro del área visible
            - IGNORA fondos y elementos secundarios
            - Responde EXCLUSIVAMENTE con el JSON, nada más
            """
        
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
                
                if response.choices[0].message.content:
                    st.markdown("---")
                    st.subheader("📊 Resultados de la Detección")
                    
                    # Parse the JSON response
                    try:
                        result_text = response.choices[0].message.content.strip()
                        result_text = result_text.replace('```json', '').replace('```', '').strip()
                        color_data = json.loads(result_text)
                        st.session_state.color_results = color_data
                        
                        # Mostrar resultados
                        st.markdown("### 🎨 Colores Detectados en el Objeto")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("#### 🔴 Rojo")
                            if color_data.get("rojo", False):
                                st.success("**✅ DETECTADO**")
                                st.markdown("LED rojo se ENCENDERÁ")
                            else:
                                st.error("**❌ NO DETECTADO**")
                                st.markdown("LED rojo permanecerá apagado")
                        
                        with col2:
                            st.markdown("#### 🟡 Amarillo")
                            if color_data.get("amarillo", False):
                                st.success("**✅ DETECTADO**")
                                st.markdown("LED amarillo se ENCENDERÁ")
                            else:
                                st.error("**❌ NO DETECTADO**")
                                st.markdown("LED amarillo permanecerá apagado")
                        
                        with col3:
                            st.markdown("#### 🟢 Verde")
                            if color_data.get("verde", False):
                                st.success("**✅ DETECTADO**")
                                st.markdown("LED verde se ENCENDERÁ")
                            else:
                                st.error("**❌ NO DETECTADO**")
                                st.markdown("LED verde permanecerá apagado")
                        
                        # Enviar comando MQTT para controlar LEDs basado en detección
                        try:
                            client2 = paho.Client("color-detection")
                            client2.on_publish = on_publish
                            client2.connect(broker, port)
                            
                            # Enviar el JSON completo de detección
                            message = json.dumps(color_data)
                            ret = client2.publish("appcolor", message)
                            
                            # Resumen final
                            colors_found = []
                            if color_data.get("rojo"): colors_found.append("🔴 Rojo")
                            if color_data.get("amarillo"): colors_found.append("🟡 Amarillo") 
                            if color_data.get("verde"): colors_found.append("🟢 Verde")
                            
                            if colors_found:
                                st.success(f"**🎯 CONTROL DE LEDs:** Encendiendo: {', '.join(colors_found)}")
                                st.toast(f"💡 LEDs activados: {', '.join(colors_found)}", icon="✅")
                            else:
                                st.warning("**📝 CONTROL DE LEDs:** No se detectaron colores - LEDs apagados")
                                st.toast("🔌 Todos los LEDs apagados", icon="🔴")
                                
                            time.sleep(1)
                            client2.disconnect()
                            
                        except Exception as e:
                            st.error(f"❌ Error controlando LEDs: {e}")
                            
                    except json.JSONDecodeError:
                        st.error("Error al procesar la respuesta del análisis.")
                        st.code(response.choices[0].message.content)
            
            except Exception as e:
                st.error(f"❌ Error en el análisis: {e}")

with tab3:
    st.markdown('<div class="section-title">📊 Estado del Sistema</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Último Comando de Voz")
        if st.session_state.last_command:
            st.info(f"**Comando:** {st.session_state.last_command}")
        else:
            st.warning("No hay comandos recientes")
    
    with col2:
        st.subheader("Última Detección de Colores")
        if st.session_state.color_results:
            color_data = st.session_state.color_results
            colors_active = []
            if color_data.get("rojo"): colors_active.append("🔴")
            if color_data.get("amarillo"): colors_active.append("🟡")
            if color_data.get("verde"): colors_active.append("🟢")
            
            if colors_active:
                st.success(f"LEDs activos: {' '.join(colors_active)}")
            else:
                st.info("Todos los LEDs apagados")
        else:
            st.warning("No hay detecciones recientes")
    
    st.markdown("---")
    st.subheader("🔌 Información de Conexión")
    st.write(f"**Broker MQTT:** `{broker}`")
    st.write(f"**Tópico:** `appcolor`")
    
    # Estado de conexión
    try:
        test_client = paho.Client("test-connection")
        test_client.connect(broker, port, 5)
        test_client.disconnect()
        st.success("✅ Conexión MQTT disponible")
    except:
        st.error("❌ No se puede conectar al broker MQTT")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Sistema IoT Integrado | Voz + Visión + Control"
    "</div>", 
    unsafe_allow_html=True
)

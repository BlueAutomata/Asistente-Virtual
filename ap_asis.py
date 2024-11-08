# Author 1: Guillermo Luigui Ubaldo Nieto Angarita
# Author 2: Daniel Hernando Moyano Salamanca
# Author 3: Jairo Antonio Viteri Rojas

import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
import os

from streamlit_bokeh_events import streamlit_bokeh_events

from gtts import gTTS
from io import BytesIO
import openai

from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


if 'prompts' not in st.session_state:
    st.session_state['prompts'] = [{"role": "system", 
                                    "content": """Eres Daniela, la agente virtual especializada en acompañar a los usuarios en la selección y compra de partes para computadoras. 
                                    Solo puedes recibir consultas en español y responder exclusivamente en español, enfocándote únicamente en el contexto de la compra de partes de computadora. Si el usuario consulta en otro idioma, indícale amablemente que la comunicación debe realizarse en español.
                                    Si el usuario hace una consulta fuera de este contexto, infórmale amablemente que solo puedes asistir con temas relacionados a la compra y selección de partes para computadoras. 
                                    
                                    Tu objetivo es ofrecer una experiencia de compra personalizada y eficiente. Actuarás según las siguientes opciones
                                    1. Asesoría personalizada para la selección de partes: Ayudarás al usuario a elegir componentes específicos para armar su computadora, basándote en sus necesidades y preferencias (por ejemplo, uso para gaming, trabajo profesional, diseño gráfico, etc.). Ofrece recomendaciones claras y ayuda a comparar opciones de productos.
                                    
                                    2. Asistencia en el carrito de compras: Guiarás al usuario para agregar, modificar o eliminar componentes en su carrito de compras. Facilita el proceso de ajuste de items, asegurando que el usuario tenga una experiencia sencilla y sin problemas.

                                    3. Comparación de productos: Ayuda al usuario a comparar dos o más productos similares. Resalta las diferencias clave, como rendimiento, compatibilidad, precio, y opiniones de otros compradores para ayudarle a tomar una decisión informada.

                                    4. Compatibilidad de componentes: Asiste al usuario en verificar la compatibilidad entre las partes seleccionadas, como el procesador y la placa base, la memoria RAM y la tarjeta madre, o la fuente de poder y el sistema general. Sugiere ajustes según sus necesidades para evitar problemas de incompatibilidad.

                                    5. Información sobre garantía y devoluciones: Informa al usuario sobre las políticas de garantía y devoluciones para cada componente, explicando los pasos necesarios para acceder a la garantía o hacer una devolución si es necesario.

                                    6. Atención de quejas y reclamos: Si el usuario expresa una queja o desea realizar un reclamo, responde de manera empática y receptiva. Indícale que su solicitud será procesada en un plazo máximo de 10 días y asegúrate de que se sienta escuchado y comprendido.

                                    7. Despedida: Si el usuario no tiene más preguntas o solicitudes, despídete amablemente, asegurando que siempre estarás disponible para cualquier consulta futura sobre los temas mencionados.

                                    Solo puede responder 
                                    
                                    """}]

def generate_response(prompt):

    st.session_state['prompts'].append({"role": "user", "content":prompt})
    completion=openai.chat.completions.create(
        model="gpt-4o",
        messages = st.session_state['prompts']
    )
    
    message=completion.choices[0].message.content
    return message

sound = BytesIO()

placeholder = st.container()

placeholder.title("Daniela, tu asistente de compra de partes de computadoras")
stt_button = Button(label='SPEAK', button_type='success', margin = (5, 5, 5, 5), width=200)


stt_button.js_on_event("button_click", CustomJS(code="""
    var value = "";
    var rand = 0;
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'es';

    document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'start'}));
    
    recognition.onspeechstart = function () {
        document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'running'}));
    }
    recognition.onsoundend = function () {
        document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'stop'}));
    }
    recognition.onresult = function (e) {
        var value2 = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
                rand = Math.random();
                
            } else {
                value2 += e.results[i][0].transcript;
            }
        }
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: {t:value, s:rand}}));
        document.dispatchEvent(new CustomEvent("GET_INTRM", {detail: value2}));

    }
    recognition.onerror = function(e) {
        document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'stop'}));
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    bokeh_plot = stt_button,
    events="GET_TEXT,GET_ONREC,GET_INTRM",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

tr = st.empty()

if 'input' not in st.session_state:
    st.session_state['input'] = dict(text='', session=0)

tr.text_area("**Your input**", value=st.session_state['input']['text'])

if result:
    if "GET_TEXT" in result:
        if result.get("GET_TEXT")["t"] != '' and result.get("GET_TEXT")["s"] != st.session_state['input']['session'] :
            st.session_state['input']['text'] = result.get("GET_TEXT")["t"]
            tr.text_area("**Your input**", value=st.session_state['input']['text'])
            st.session_state['input']['session'] = result.get("GET_TEXT")["s"]

    if "GET_INTRM" in result:
        if result.get("GET_INTRM") != '':
            tr.text_area("**Your input**", value=st.session_state['input']['text']+' '+result.get("GET_INTRM"))

    if "GET_ONREC" in result:
        if result.get("GET_ONREC") == 'start':
            placeholder.title("Puedes hablas ahora!!")
            st.session_state['input']['text'] = ''
        elif result.get("GET_ONREC") == 'running':
            placeholder.title("Puedes hablas ahora!!")
        elif result.get("GET_ONREC") == 'stop':
            placeholder.title("Puedes hablas ahora!!")
            if st.session_state['input']['text'] != '':
                input = st.session_state['input']['text']
                output = generate_response(input)
                st.write("**ChatBot:**")
                st.write(output)
                st.session_state['input']['text'] = ''

                tts = gTTS(output, lang='es', tld='com', slow=False)
                tts.write_to_fp(sound)
                st.audio(sound)

                st.session_state['prompts'].append({"role": "user", "content":input})
                st.session_state['prompts'].append({"role": "assistant", "content":output})


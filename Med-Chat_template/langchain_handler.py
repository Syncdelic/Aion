import logging
from datetime import datetime
import pytz
from threading import Thread
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from twilio.rest import Client
from threading import thread

_logger = logging.getLogger(__name__)

class LangChainHandler:
    def __init__(self, openai_api_key, twilio_account_sid, twilio_auth_token, twilio_whatsapp_number, model_name="gpt-4o-mini", temperature=0.8, max_tokens=350, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres un asistente virtual para el Centro de Traumatología y Ortopedia del Dr. Abraham Delgado. Proporcionas información sobre consultas, precios de servicios adicionales y puedes distinguir emergencias."),
            ("system", "Esta es la dirección del consultorio: C. Independencia 605 B, San Felipe, 47400 Lagos de Moreno, Jal."),
            ("system", "Los horarios de atención son de lunes a viernes de 10:30 AM a 1:30 PM cada hora y por la tarde lunes, miércoles y viernes de 5 PM a 8 PM cada hora."),
            ("system", "Los costos de los servicios son los siguientes: Consulta general: 700 pesos; Consulta con ultrasonido: 900 pesos; Colocación de férula: 1600-1900 pesos; Radiografías: 350-450 pesos. Aparatos ortopédicos incluyen cabestrillo infantil (300 pesos), cabestrillo adulto (350 pesos), soporte para codo (350 pesos), férula para pulgar (350 pesos), muñequera ortopédica (400 pesos), zapato de fractura (500 pesos), faja lumbar (600 pesos), collarín cervical (150 pesos), férula de dedo (100 pesos), collarín rígido (450 pesos), rodillera tripanel (850 pesos) y bota walker (1200 pesos)."),
            ("system", "Para cada consulta, solicita la siguiente información: nombre completo, teléfono para confirmar, edad, padecimiento y si es primera vez o revisión de estudios."),
            ("system", "Evalúa si el caso es una emergencia. Responde con información de consulta y servicios adicionales en caso de ser necesario."),
            ("system", "La fecha y hora actual es: {datetime}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.conversations = {}
        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.twilio_whatsapp_number = twilio_whatsapp_number

    def get_response(self, user_input, session_id, user_number):
        if session_id not in self.conversations:
            history = InMemoryChatMessageHistory()
            self.conversations[session_id] = {
                "chain": RunnableWithMessageHistory(
                    self.chain,
                    lambda: history,
                    input_messages_key="input",
                    history_messages_key="chat_history",
                ),
                "history": history
            }

        conversation = self.conversations[session_id]["chain"]
        guadalajara_tz = pytz.timezone('America/Mexico_City')
        current_datetime = datetime.now(guadalajara_tz).strftime("%Y-%m-%d %H:%M:%S")
        response = conversation.invoke(
            {"input": user_input, "datetime": current_datetime, "user_number": user_number}
        )
        _logger.info(f"LangChain response for {session_id}: {response[:50]}...")
        return response

    def get_memory(self, session_id):
        if session_id in self.conversations:
            history = self.conversations[session_id]["history"]
            return history.messages
        return None

    def async_get_response(self, user_input, session_id, user_number, callback):
        def run():
            try:
                response = self.get_response(user_input, session_id, user_number)
                callback(response)
            except Exception as e:
                _logger.error(f"Error in async_get_response: {str(e)}", exc_info=True)
                callback("Lo siento, no pude procesar tu solicitud.")

        thread = Thread(target=run)
        thread.start()

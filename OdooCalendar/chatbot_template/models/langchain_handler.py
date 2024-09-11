from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
import logging
from datetime import datetime
import pytz
from twilio.rest import Client
from threading import Thread
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class LangChainHandler:
    def __init__(self, env, openai_api_key, twilio_account_sid, twilio_auth_token, twilio_whatsapp_number, model_name="gpt-4-0613", temperature=0.7, max_tokens=300):
        self.env = env
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres un asistente virtual para una consulta médica. Tu trabajo es proporcionar información sobre los servicios, horarios, costos, y agendar citas."),
            ("system", "Horarios de consulta: Lunes a viernes de 10:30 a 13:30 (cada hora), y lunes, miércoles y viernes de 17:00 a 20:00 (cada hora)."),
            ("system", "Costo de consulta básica: 700 pesos. Otros servicios tienen costo adicional."),
            ("system", "Servicios y costos adicionales:\n- Consulta con ultrasonido: 900 pesos\n- Colocación de Férula: 1600 a 1900 pesos\n- Radiografías: 350 a 450 pesos"),
            ("system", "Aparatos ortopédicos:\n- Cabestrillo infantil: 300 pesos\n- Cabestrillo adulto: 350 pesos\n- Soporte para codo: 350 pesos\n- Férula para pulgar: 350 pesos\n- Muñequera ortopédica: 400 pesos\n- Zapato de fractura: 500 pesos\n- Faja Lumbar: 600 pesos\n- Collarín cervical: 150 pesos\n- Férula de dedo: 100 pesos\n- Collarín rígido: 450 pesos\n- Rodillera tripanel: 850 pesos\n- Bota walker: 1200 pesos"),
            ("system", "Para agendar una cita, solicita la siguiente información:\n1. Nombre completo\n2. Teléfono para confirmar\n3. Edad\n4. Padecimiento\n5. Si es primera vez o revisión de estudios"),
            ("system", "Evalúa si es una emergencia y recomienda atención inmediata si es necesario."),
            ("system", "La fecha y hora actual es: {datetime}"),
            ("system", "El número de WhatsApp del paciente es: {user_number}"),
            ("system", "Información del cliente: {client_info}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.conversations = {}
        self.client_info = {}

        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.twilio_whatsapp_number = twilio_whatsapp_number

        self.setup_google_calendar()

    def setup_google_calendar(self):
        creds = None
        if os.path.exists("gcalendar/token.json"):
            creds = Credentials.from_authorized_user_file("gcalendar/token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("gcalendar/credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            with open("gcalendar/token.json", "w") as token:
                token.write(creds.to_json())

        self.calendar_service = build("calendar", "v3", credentials=creds)

    def create_calendar_event(self, summary, description, start_time, end_time):
        event = {
            "summary": summary,
            "location": "Lagos de Moreno, Jalisco, Mexico",
            "description": description,
            "colorId": "2",
            "start": {
                "dateTime": start_time,
                "timeZone": "America/Mexico_City",
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "America/Mexico_City",
            },
            "recurrence": [
                "RRULE:FREQ=DAILY;COUNT=1",
            ],
            "attendees": [
                {"email": "arrc.psy@gmail.com"},
            ],
        }

        try:
            event = self.calendar_service.events().insert(calendarId="primary", body=event).execute()
            return f"Cita agendada. Enlace del evento: {event.get('htmlLink')}"
        except HttpError as error:
            _logger.error(f"An error occurred: {error}")
            return "Lo siento, hubo un problema al agendar la cita. Por favor, intenta de nuevo más tarde."

    def get_or_create_client_info(self, user_number):
        ClientInfo = self.env['chatbot.client.info'].sudo()
        client_info = ClientInfo.search([('phone', '=', user_number)], limit=1)
        if not client_info:
            client_info = ClientInfo.create({
                'phone': user_number,
                'name': 'Unknown',
                'last_interaction': fields.Datetime.now(),
            })
        return client_info

    def update_client_info(self, client_info, session_id):
        history = self.get_memory(session_id)
        if history:
            client_info.write({
                'chat_history': '\n'.join([f"{m.type}: {m.content}" for m in history]),
                'last_interaction': fields.Datetime.now(),
            })

        # Update other fields based on extracted information
        name = self.extract_info(session_id, "nombre")
        age = self.extract_info(session_id, "edad")
        condition = self.extract_info(session_id, "padecimiento")
        is_new_patient = self.extract_info(session_id, "es_nuevo_paciente")

        if name:
            client_info.name = name
        if age:
            client_info.age = int(age)
        if condition:
            client_info.condition = condition
        if is_new_patient is not None:
            client_info.is_new_patient = is_new_patient

    def get_response(self, user_input, session_id, user_number):
        client_info = self.get_or_create_client_info(user_number)
        
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
        
        client_info_str = f"Nombre: {client_info.name}, Teléfono: {client_info.phone}, Edad: {client_info.age}, Padecimiento: {client_info.condition}, Nuevo paciente: {'Sí' if client_info.is_new_patient else 'No'}"
        
        response = conversation.invoke(
            {"input": user_input, "datetime": current_datetime, "user_number": user_number, "client_info": client_info_str},
            config={"configurable": {"session_id": session_id}}
        )
        _logger.info(f"LangChain response for {session_id}: {response[:50]}...")

        self.update_client_info(client_info, session_id)

        # Check if we need to create a calendar event
        if "agendar_cita" in response.lower():
            name = client_info.name
            date = self.extract_info(session_id, "fecha")
            time = self.extract_info(session_id, "hora")
            padecimiento = client_info.condition

            if all([name, date, time, padecimiento]):
                start_time = f"{date}T{time}:00-06:00"
                end_time = f"{date}T{time[:2]}:30:00-06:00"  # Assuming 30-minute appointments
                summary = f"Consulta para {name}"
                description = f"Paciente: {name}\nPadecimiento: {padecimiento}\nTeléfono: {user_number}"
                event_response = self.create_calendar_event(summary, description, start_time, end_time)
                response += f"\n\n{event_response}"
            else:
                response += "\n\nNo se pudo agendar la cita debido a información faltante. Por favor, proporciona todos los detalles necesarios."

        return response

    def get_memory(self, session_id):
        if session_id in self.conversations:
            history = self.conversations[session_id]["history"]
            return history.messages
        return None

    def async_get_response(self, user_input, session_id, user_number, callback):
        def run():
            response = self.get_response(user_input, session_id, user_number)
            callback(response)
        
        thread = Thread(target=run)
        thread.start()

    def extract_info(self, session_id, info_type):
        history = self.get_memory(session_id)
        if not history:
            return None

        # Implement more sophisticated extraction logic here
        # This is a simple example and might need to be improved
        for message in reversed(history):
            if message.type == 'human':
                if info_type == "nombre" and "me llamo" in message.content.lower():
                    return message.content.split("me llamo")[-1].strip()
                elif info_type == "edad" and "años" in message.content.lower():
                    return message.content.split("años")[0].split()[-1]
                elif info_type == "padecimiento" and "tengo" in message.content.lower():
                    return message.content.split("tengo")[-1].strip()
                elif info_type == "es_nuevo_paciente" and "primera vez" in message.content.lower():
                    return "primera vez" in message.content.lower()
                elif info_type == "fecha" and any(month in message.content.lower() for month in ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]):
                    # This is a very simple date extraction and should be improved
                    return message.content
                elif info_type == "hora" and ":" in message.content:
                    # This is a very simple time extraction and should be improved
                    return message.content.split(":")[-2][-2:] + ":" + message.content.split(":")[-1][:2]

        return None

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

_logger = logging.getLogger(__name__)

class LangChainHandler:
    def __init__(self, openai_api_key, twilio_account_sid, twilio_auth_token, twilio_whatsapp_number, model_name="gpt-4o-mini", temperature=0.8, max_tokens=200, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
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
            ("system", "Eres un asistente virtual para ITS-BS. Tu trabajo es proporcionar información sobre los servicios de consultoría de automatización IT, validar medios de contacto y enviar cotizaciones."),
            ("system", "La fecha y hora actual es: {datetime}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.conversations = {}
        self.client_info = {}

        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.twilio_whatsapp_number = twilio_whatsapp_number

    def get_response(self, user_input, session_id):
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
            {"input": user_input, "datetime": current_datetime},
            config={"configurable": {"session_id": session_id}}
        )
        _logger.info(f"LangChain response for {session_id}: {response[:50]}...")
        return response

    def get_memory(self, session_id):
        if session_id in self.conversations:
            history = self.conversations[session_id]["history"]
            return history.messages
        return None

    def async_get_response(self, user_input, session_id, callback):
        def run():
            response = self.get_response(user_input, session_id)
            callback(response)
        
        thread = Thread(target=run)
        thread.start()
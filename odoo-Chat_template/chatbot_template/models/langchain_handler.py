from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
import logging

_logger = logging.getLogger(__name__)

class LangChainHandler:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(openai_api_key=openai_api_key)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres un asistente virtual para Coco Resort. Tu trabajo es proporcionar información sobre las opciones de alojamiento, los servicios del resort, la ubicación, el menú del restaurante y hacer reservas para los huéspedes. Sé amable y servicial."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.conversations = {}

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
        response = conversation.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        _logger.info(f"LangChain response for {session_id}: {response[:50]}...")
        return response

    def get_memory(self, session_id):
        if session_id in self.conversations:
            # Retrieve the message history object for the session
            history = self.conversations[session_id]["history"]
            return history.messages
        return None
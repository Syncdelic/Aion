from odoo import fields, models, api
import logging
from twilio.rest import Client
from odoo.exceptions import UserError
from odoo.http import request
from twilio.twiml.messaging_response import MessagingResponse
from .langchain_handler import LangChainHandler

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    openai_api_key = fields.Char(string="OpenAI API Key", required=True)
    _langchain_handler = None  # Class-level attribute

    @classmethod
    def _get_langchain_handler(cls, openai_api_key):
        if not cls._langchain_handler:
            cls._langchain_handler = LangChainHandler(openai_api_key)
        return cls._langchain_handler

    def whatsapp_reply(self, incoming_msg, user_number):
        try:
            langchain_handler = self._get_langchain_handler(self.openai_api_key)

            _logger.info(f"Incoming message from {user_number}: {incoming_msg}")
            
            response_msg = langchain_handler.get_response(incoming_msg, session_id=user_number)
            _logger.info(f"Response content: {response_msg}")

            # Log memory content for debugging
            memory = langchain_handler.get_memory(user_number)
            if memory:
                _logger.info(f"Memory content for {user_number}: {memory}")

        except Exception as e:
            response_msg = f"Lo siento, no pude procesar tu solicitud. Error: {str(e)}"
            _logger.error(f"Error in whatsapp_reply: {str(e)}", exc_info=True)

        resp = MessagingResponse()
        resp.message(response_msg)
        return str(resp)


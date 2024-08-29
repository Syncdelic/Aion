from odoo import fields, models, api
import logging
from twilio.rest import Client
from openai import OpenAI
from odoo.exceptions import UserError
from odoo.http import request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import tiktoken

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    openai_api_key = fields.Char(string="OpenAI API Key", required=True)

    def whatsapp_reply(self):
        # Explicitly search for the company "ITS-BS"
        company = self.env['res.company'].search([('name', '=', 'ITS-BS')], limit=1)
        
        if not company:
            _logger.error("Company ITS-BS not found.")
            raise UserError("Company ITS-BS not found. Please check the company configuration.")
        
        # Logging the company details
        _logger.info(f"Company ID: {company.id}, Name: {company.name}")

        # Ensure credentials are configured
        if not company.twilio_account_sid or not company.twilio_auth_token or not company.openai_api_key:
            _logger.error("Twilio or OpenAI credentials are missing in the company settings.")
            raise UserError("Please configure Twilio and OpenAI credentials in the company settings.")
        
        try:
            # Initialize Twilio and OpenAI clients
            twilio_client = Client(company.twilio_account_sid, company.twilio_auth_token)
            openai_client = OpenAI(api_key=company.openai_api_key)

            # Extracting necessary fields from the request
            incoming_msg = request.httprequest.values.get('Body', '').strip()
            user_number = request.httprequest.values.get('From', '').strip()

            _logger.info(f"Incoming message from {user_number}: {incoming_msg}")
            
            # Default response if no response from OpenAI
            response_msg = "Lo siento, no pude entender tu solicitud."

            # Retrieve conversation context
            conversation_history = request.session.get('conversation_history', [])

            # Add the incoming message to the conversation history
            conversation_history.append({"role": "user", "content": incoming_msg})

            # OpenAI API call
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""
                    Eres un asistente virtual para Coco Resort. Tu trabajo es proporcionar información sobre las opciones de alojamiento, los servicios del resort, la ubicación, el menú del restaurante y hacer reservas para los huéspedes. Sé amable y servicial. La fecha y hora actuales son {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
                    """},
                    *conversation_history
                ],
                max_tokens=250,
                temperature=0.6,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )

            # Get response content
            response_content = response.choices[0].message.content.strip()
            _logger.info(f"Response content: {response_content}")

            # Add the response to the conversation history
            conversation_history.append({"role": "assistant", "content": response_content})

            # Save the updated conversation history to the session
            request.session['conversation_history'] = conversation_history

            response_msg = response_content

        except Exception as e:
            response_msg = f"Lo siento, no pude procesar tu solicitud. Error: {str(e)}"
            _logger.error(f"Error: {e}")    

        # Send response via Twilio
        resp = MessagingResponse()
        resp.message(response_msg)
        return str(resp)


from flask import Flask, request, jsonify
from langchain_handler import LangChainHandler
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import threading

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize LangChainHandler with environment variables
langchain_handler = LangChainHandler(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    twilio_whatsapp_number=os.getenv("TWILIO_WHATSAPP_NUMBER")
)

@app.route('/whatsapp', methods=['POST'])
def handle_whatsapp():
    incoming_msg = request.form.get('Body', '').strip()
    user_number = request.form.get('From', '').strip()
    session_id = user_number

    response_event = threading.Event()
    response_msg = ""

    def callback(response):
        nonlocal response_msg
        response_msg = response
        response_event.set()

    try:
        langchain_handler.async_get_response(incoming_msg, session_id, user_number, callback)
        # Wait for the response with a timeout
        response_event.wait(timeout=15)

        if not response_event.is_set():
            response_msg = "Lo siento, el servidor está tardando en responder. Por favor, intenta de nuevo más tarde."

        resp = MessagingResponse()
        resp.message(response_msg)
        return str(resp)
    except Exception as e:
        _logger.error(f"Error in handle_whatsapp: {str(e)}", exc_info=True)
        resp = MessagingResponse()
        resp.message("Lo siento, no pude procesar tu solicitud.")
        return str(resp)

if __name__ == '__main__':
    app.run(debug=True)


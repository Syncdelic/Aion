from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from openai import OpenAI
import os
from dotenv import load_dotenv
import tiktoken

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Twilio credentials
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_client = Client(account_sid, auth_token)

# Load the tokenizer for the specific model
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()

    # Default message if no response from OpenAI
    response_msg = "Sorry, I'm having trouble understanding your request."

    try:
        # Count tokens in the incoming message
        incoming_tokens = len(encoding.encode(incoming_msg))
        print(f"Incoming message tokens: {incoming_tokens}")

        # OpenAI API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a barista at a coffee shop. Your job is to take drink orders from customers, suggest items, and answer any questions about the menu. Be polite and helpful."},
                {"role": "user", "content": incoming_msg}
            ],
            max_tokens=150
        )
        
        # Get response content and count tokens
        response_content = response.choices[0].message.content.strip()
        response_tokens = len(encoding.encode(response_content))
        print(f"Response message tokens: {response_tokens}")

        response_msg = response_content
    except Exception as e:
        response_msg = f"Sorry, I couldn't process your request. Error: {str(e)}"

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)


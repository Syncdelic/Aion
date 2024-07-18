from flask import request, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from openai import OpenAI
from dotenv import load_dotenv
from hotel_sys import *
from reservation_utils import *
from datetime import datetime
import os
import tiktoken

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")
openai_client = OpenAI(api_key=openai_api_key)

# Twilio credentials
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
if not account_sid or not auth_token:
    raise ValueError("Twilio ACCOUNT_SID or AUTH_TOKEN is not set in the environment variables")
twilio_client = Client(account_sid, auth_token)

# Load the tokenizer for the specific model
encoding = tiktoken.encoding_for_model("gpt-4o")

# Define the path to the CSV file
today_date = datetime.now().strftime("%Y-%m-%d")
csv_file_path = f'reservations_{today_date}.csv'

def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    user_number = request.values.get('From', '').strip()

    print(f"Incoming message from {user_number}: {incoming_msg}")
    
    # Default message if no response from OpenAI
    response_msg = "Lo siento, no pude entender tu solicitud."

    # Retrieve conversation context
    conversation_history = session.get('conversation_history', [])
    current_state = session.get('current_state', 'initial')

    try:
        # Add the incoming message to the conversation history
        conversation_history.append({"role": "user", "content": incoming_msg})

        # OpenAI API call
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"""
                Eres un asistente virtual para Coco Resort. Tu trabajo es proporcionar información sobre las opciones de alojamiento, los servicios del resort, la ubicación, el menú del restaurante y hacer reservas para los huéspedes. Sé amable y servicial. La fecha y hora actuales son {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
            
                Detalles de Alojamiento:
                1 Habitación, 1 Baño Apartamento
                Huéspedes: 2
                Precio: MXN 1100 por noche
                Detalles: Apartamento de una habitación con aire acondicionado, baño y mini-bar.
            
                2 Habitaciones, 2 Baños Villa
                Huéspedes: 4
                Precio: MXN 2200 por noche
                Detalles: Villa de dos habitaciones con baños, cocina y sala de estar.
            
                3 Habitaciones, 3 Baños Villa
                Huéspedes: 6
                Precio: MXN 3300 por noche
                Detalles: Villa de tres habitaciones con aire acondicionado, baños y amplia sala de estar.
            
                6 Habitaciones, 4 Baños Villa
                Huéspedes: 12
                Precio: MXN 5500 por noche
                Detalles: Villa de seis habitaciones con baños, cocinas y áreas de estar.
            
                Información de Ubicación:
                Coordenadas GPS: 21.144448, -89.278721
                Dirección: Uchi, Tablaje Catastral No. 3563, Localidad de, 97430 Yuc., México.
            
                Por Qué Elegir Coco Resort:
                Construido en 2021, ofreciendo una experiencia al estilo mexicano con apartamentos y villas.
                Las comodidades incluyen piscinas de agua dulce, bar, restaurante en la azotea, área de juegos para niños, área de barbacoa y Wi-Fi gratis.
                Ubicado en un lugar tranquilo, a poca distancia en coche de una ciudad con mercados, atracciones naturales y el mar.
            
                Información de Comodidades:
                Piscinas de agua dulce
                Bar
                Restaurante en la azotea
                Área de juegos para niños
                Área de barbacoa
                Wi-Fi gratis
                Minigolf
                Pared de escalada
                Jardines botánicos
                Senderos rodeados de hermosos jardines botánicos
                Campo de fútbol
            
                Horarios del Restaurante:
                Abierto de 9am a 9pm
            
                Menú del Restaurante:
                Coco Resort: $230
                Rib Eye Grill: $390
                Aguachile Verde: $220
                Ceviche: $220
                Filete de Atún: $240
                Espagueti a la Boloñesa: $120
                Chuletas a la Parrilla: $119
                Milanesa de Pollo Empanizada: $129
                Arroz Tipo Thai: $90
                Camarones a la Crema: $220
                Milanesa de Puerco Empanizada: $129
                Crepas: $90
                Hamburguesa con Papas: $150
                Pollo a la Parrilla: $129
            
                Ejemplo de Resumen de Reserva:
                Nombre: Aldo Rea
                Número de Personas: 6
                Fechas: 2024-07-20 al 2024-07-25
                Tipo de Habitación: Villa de 3 Habitaciones, 3 Baños
                Precio por Noche: MXN 3300
                Costo Total: MXN 16500
            
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
        print(f"Response content: {response_content}")

        # Add the response to the conversation history
        conversation_history.append({"role": "assistant", "content": response_content})

        # Save the updated conversation history to the session
        session['conversation_history'] = conversation_history

        response_msg = response_content

    except Exception as e:
        response_msg = f"Lo siento, no pude procesar tu solicitud. Error: {str(e)}"
        print(f"Error: {e}")    

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

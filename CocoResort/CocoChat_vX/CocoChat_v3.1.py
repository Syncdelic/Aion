from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from hotel_sys import Habitacion, Hotel, Reserva, Cliente, SistemaReservas
from reservation_utils import clean_text, extract_details_from_response, extract_dates, load_reservations, save_reservations, add_reservation

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")
client = OpenAI(api_key=openai_api_key)

# Twilio credentials
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
if not account_sid or not auth_token:
    raise ValueError("Twilio ACCOUNT_SID or AUTH_TOKEN is not set in the environment variables")
twilio_client = Client(account_sid, auth_token)

# Initialize hotel reservation system
sistema = SistemaReservas()
hotel = Hotel("Coco Resort", "Uchi, Tablaje Catastral No. 3563, Localidad de, 97430 Yuc., México")

# Adding rooms
habitaciones = [
    Habitacion(101, "1 Habitación, 1 Baño Apartamento", 1100),
    Habitacion(102, "2 Habitaciones, 2 Baños Villa", 2200),
    Habitacion(103, "3 Habitaciones, 3 Baños Villa", 3300),
    Habitacion(104, "6 Habitaciones, 4 Baños Villa", 5500)
]

for habitacion in habitaciones:
    hotel.añadir_habitacion(habitacion)

sistema.registrar_hotel(hotel)

@app.route('/whatsapp', methods=['POST'])
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
        response = client.chat.completions.create(
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
            temperature=0.7,
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

        if "reserva" in incoming_msg.lower() or "reservar" in incoming_msg.lower():
            response_msg = f"{response_content}\n\nPara proceder con tu reserva, por favor proporciona la siguiente información en el formato:\nNombre completo: <Tu Nombre>\nNúmero de personas: <Número>\nFechas de estancia: <Check-in> al <Check-out>\nTipo de alojamiento: <Tipo de Alojamiento>"
            session['current_state'] = 'collecting_details'
        elif current_state == 'collecting_details':
            # Extract and set reservation details if available in the response
            details = extract_details_from_response(response_content)
            print("Extracted details from response:", details)

            if details:
                # Handling the dates more robustly
                fechas = details.get("Fechas")
                start_date, end_date = extract_dates(fechas) if fechas else (None, None)

                if start_date and end_date:
                    print(f"Start Date: {start_date}, End Date: {end_date}")

                print(f"Setting details in reservation object: {details}")

                # Create reservation
                cliente = Cliente(1, details.get("Nombre"), user_number)
                sistema.registrar_cliente(cliente)
                habitaciones_disponibles = hotel.buscar_habitacion(tipo=details.get("Tipo de Habitación"))
                habitacion = habitaciones_disponibles[0] if habitaciones_disponibles else None

                if habitacion and start_date and end_date:
                    reserva = Reserva(1, habitacion, cliente, start_date, end_date)
                    cliente.realizar_reserva(reserva)

                    # Create the response message
                    response_msg = clean_text(response_content)

                    # Add reservation to CSV
                    add_reservation(
                        user_number=user_number,
                        name=cliente.nombre,
                        number_of_people=details.get("Número de Personas"),
                        start_date=start_date,
                        end_date=end_date,
                        room_type=habitacion.tipo,
                        price_per_night=habitacion.precio,
                        total_cost=details.get("Costo Total")
                    )
                    response_msg += "\n\nSu reserva ha sido añadida."
                else:
                    print("Incomplete reservation details:")
                    print(f"Cliente: {cliente.nombre}, Habitacion: {habitacion}, Start Date: {start_date}, End Date: {end_date}")
                    response_msg = "No se pudo completar la reserva. Por favor revisa los detalles proporcionados y vuelve a intentarlo."
            else:
                response_msg = "No se pudieron extraer los detalles de la reserva. Por favor proporciona los detalles nuevamente."

            session['current_state'] = 'initial'
        else:
            response_msg = response_content  # Default response message for other states

    except Exception as e:
        response_msg = f"Lo siento, no pude procesar tu solicitud. Error: {str(e)}"
        print(f"Error: {e}")

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)


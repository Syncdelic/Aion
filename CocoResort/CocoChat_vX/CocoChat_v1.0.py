from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from openai import OpenAI
import os
from dotenv import load_dotenv
import tiktoken
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Twilio credentials
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_client = Client(account_sid, auth_token)

# Load the tokenizer for the specific model
encoding = tiktoken.encoding_for_model("gpt-4o")

# Define the path to the CSV file
today_date = datetime.now().strftime("%Y-%m-%d")
csv_file_path = f'reservations_{today_date}.csv'

class Reservation:
    def __init__(self):
        self.user_number = None
        self.name = None
        self.number_of_people = None
        self.start_date = None
        self.end_date = None
        self.room_type = None
        self.price_per_night = None
        self.total_cost = None
    
    def set_details(self, user_number, name, number_of_people, start_date, end_date, room_type, price_per_night, total_cost):
        self.user_number = user_number
        self.name = name
        self.number_of_people = number_of_people
        self.start_date = start_date
        self.end_date = end_date
        self.room_type = room_type
        self.price_per_night = price_per_night
        self.total_cost = total_cost

    def get_summary(self):
        return f"Nombre: {self.name}\nNúmero de Personas: {self.number_of_people}\nFechas: {self.start_date} al {self.end_date}\nTipo de Habitación: {self.room_type}\nPrecio por Noche: {self.price_per_night}\nCosto Total: {self.total_cost}"

    def debug_print(self):
        print(f"Reservation Debug - User Number: {self.user_number}, Name: {self.name}, Number of People: {self.number_of_people}, "
              f"Start Date: {self.start_date}, End Date: {self.end_date}, Room Type: {self.room_type}, "
              f"Price per Night: {self.price_per_night}, Total Cost: {self.total_cost}")

# Functions to manage CSV file
def load_reservations():
    print(f"Loading reservations from CSV file at path: {csv_file_path}")
    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path)
        print("Loaded reservations from CSV:")
        print(df)
        return df
    else:
        print("CSV file does not exist. Creating a new dataframe.")
        return pd.DataFrame(columns=['user_number', 'name', 'num_people', 'start_date', 'end_date', 'room_type', 'price_per_night', 'total_cost'])

def save_reservations(df):
    print("Saving reservations to CSV:")
    print(df)
    df.to_csv(csv_file_path, index=False)
    print("Reservations saved successfully.")

def add_reservation(reservation):
    df = load_reservations()
    new_reservation = pd.DataFrame([{
        'user_number': reservation.user_number,
        'name': reservation.name,
        'num_people': reservation.number_of_people,
        'start_date': reservation.start_date,
        'end_date': reservation.end_date,
        'room_type': reservation.room_type,
        'price_per_night': reservation.price_per_night,
        'total_cost': reservation.total_cost
    }])
    df = pd.concat([df, new_reservation], ignore_index=True)
    save_reservations(df)
    print("Added new reservation to CSV.")

reservation = Reservation()

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    user_number = request.values.get('From', '').strip()

    print(f"Incoming message from {user_number}: {incoming_msg}")

    # Set the user number in the reservation object
    reservation.user_number = user_number

    # Get current date and time
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # Default message if no response from OpenAI
    response_msg = "Lo siento, no pude entender tu solicitud."

    # Retrieve conversation context
    conversation_history = session.get('conversation_history', [])

    try:
        # Add the incoming message to the conversation history
        conversation_history.append({"role": "user", "content": incoming_msg})

        # OpenAI API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"""
                Eres un asistente virtual para Coco Resort. Tu trabajo es proporcionar información sobre las opciones de alojamiento, los servicios del resort, la ubicación, el menú del restaurante y hacer reservas para los huéspedes. Sé amable y servicial. La fecha y hora actuales son {current_date} {current_time}.
                
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
            temperature=0.1,
            top_p=0.1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )

        # Get response content and count tokens
        response_content = response.choices[0].message.content.strip()
        response_tokens = len(encoding.encode(response_content))
        print(f"Response message tokens: {response_tokens}")

        # Add the response to the conversation history
        conversation_history.append({"role": "assistant", "content": response_content})

        # Save the updated conversation history to the session
        session['conversation_history'] = conversation_history

        # Extract and set reservation details if available in the response
        details = {}
        start_date = None
        end_date = None
        if "Nombre" in response_content and "Número de Personas" in response_content:
            lines = response_content.split('\n')
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    cleaned_key = key.strip().replace("**", "").replace("*", "").replace("-", "").strip()
                    cleaned_value = value.strip().replace("**", "").replace("*", "").strip()
                    details[cleaned_key] = cleaned_value
            
            print("Extracted details from response:", details)
            
            # Handling the dates more robustly
            fechas = details.get("Fechas")
            if fechas:
                try:
                    # Split the start and end dates
                    start_date, end_date = fechas.replace("del", "").replace("de", "").strip().split('al')
                    start_date = datetime.strptime(start_date.strip(), "%d %m %Y").strftime("%Y-%m-%d")
                    end_date = datetime.strptime(end_date.strip(), "%d %m %Y").strftime("%Y-%m-%d")
                except ValueError:
                    print(f"Error splitting dates: {fechas}")

            print(f"Setting details in reservation object: {details}")

            reservation.set_details(
                user_number=user_number,
                name=details.get("Nombre"),
                number_of_people=details.get("Número de Personas"),
                start_date=start_date,
                end_date=end_date,
                room_type=details.get("Tipo de Habitación"),
                price_per_night=details.get("Precio por Noche"),
                total_cost=details.get("Costo Total")
            )

            reservation.debug_print()

        response_msg = response_content

        # Check for reservation completion and add to CSV
        if reservation.name and reservation.number_of_people and reservation.start_date and reservation.end_date and reservation.room_type and reservation.price_per_night and reservation.total_cost:
            add_reservation(reservation)
            response_msg += "\nSu reserva ha sido añadida."
        else:
            print("Incomplete reservation details:")
            reservation.debug_print()

    except Exception as e:
        response_msg = f"Lo siento, no pude procesar tu solicitud. Error: {str(e)}"
        print(f"Error: {e}")

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)

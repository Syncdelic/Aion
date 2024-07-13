from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client  # Ensure this import is included
from openai import OpenAI
import os
from dotenv import load_dotenv
import tiktoken
from datetime import datetime

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
encoding = tiktoken.encoding_for_model("gpt-4")

# Accommodation details
accommodations = {
    "1 bedroom, 1 bathroom apartment": {
        "guests": 2,
        "price": 1100,
        "details": "One-bedroom apartment with AC, bathroom, and mini-bar."
    },
    "2 bedroom, 2 bathroom villa": {
        "guests": 4,
        "price": 2200,
        "details": "Two-bedroom villa with bathrooms, kitchen, and living area."
    },
    "3 bedroom, 3 bathroom villa": {
        "guests": 6,
        "price": 3300,
        "details": "Three-bedroom villa with AC, bathrooms, and large living area."
    },
    "6 bedroom, 4 bathroom villa": {
        "guests": 12,
        "price": 5500,
        "details": "Six-bedroom villa with bathrooms, kitchens, and living areas."
    }
}

# Store conversation context and reservation details
conversations = {}
reservations = {}

def get_accommodation_info(accommodation_name):
    info = accommodations.get(accommodation_name.lower())
    if info:
        return f"{accommodation_name.title()}:\nGuests: {info['guests']}\nPrice: MXN ${info['price']} per night\nDetails: {info['details']}"
    else:
        return "I couldn't find information about that accommodation. Please provide more details or choose from our available options."

def get_location_info():
    return (
        "GPS coordinates: 21.144448, -89.278721\n"
        "Address: Uchi, Tablaje Catastral No. 3563, Localidad de, 97430 Yuc., Mexico."
    )

def get_why_coco_resort_info():
    return (
        "Coco Resort, built in 2021, offers a Mexican-style experience with apartments and villas, freshwater pools, bar, rooftop restaurant, kids' playground, barbecue area, and free wifi. "
        "Perfectly located in a calm place, within driving distance from a city with markets, natural attractions, and the sea."
    )

def get_amenities_info():
    return (
        "Coco Resort amenities include freshwater pools, bar, rooftop restaurant, kids' playground, barbecue area, free wifi, minigolf, climbing wall, botanical gardens, trails surrounded by beautiful botanical gardens, and a soccer field."
    )

def get_restaurant_hours():
    return "The restaurant is open from 9am to 9pm."

def get_restaurant_menu():
    return (
        "Restaurant Menu:\n"
        "Coco Resort: $230\n"
        "Rib Eye Grill: $390\n"
        "Aguachile Verde: $220\n"
        "Ceviche: $220\n"
        "Filete de Atún: $240\n"
        "Espagueti a la Boloñesa: $120\n"
        "Chuletas a la Parrilla: $119\n"
        "Milanesa de Pollo Empanizada: $129\n"
        "Arroz Tipo Thai: $90\n"
        "Camarones a la Crema: $220\n"
        "Milanesa de Puerco Empanizada: $129\n"
        "Crepas: $90\n"
        "Hamburguesa con Papas: $150\n"
        "Pollo a la Parrilla: $129"
    )

def calculate_total_cost(start_date, end_date, price_per_night):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    num_nights = (end - start).days
    return num_nights * price_per_night

def summarize_reservation(user_number):
    reservation = reservations.get(user_number, {})
    if not reservation:
        return "No reservation details found."
    
    total_cost = calculate_total_cost(reservation['start_date'], reservation['end_date'], reservation['price_per_night'])
    reservation['total_cost'] = total_cost
    
    summary = (
        f"Reservation Summary:\n"
        f"Name: {reservation.get('name', 'N/A')}\n"
        f"Number of People: {reservation.get('num_people', 'N/A')}\n"
        f"Dates: {reservation.get('start_date', 'N/A')} to {reservation.get('end_date', 'N/A')}\n"
        f"Room Type: {reservation.get('room_type', 'N/A')}\n"
        f"Price per Night: MXN ${reservation.get('price_per_night', 'N/A')}\n"
        f"Total Cost: MXN ${reservation.get('total_cost', 'N/A')}"
    )
    return summary

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip().lower()
    user_number = request.values.get('From', '')

    # Default message if no response from OpenAI
    response_msg = "I'm here to assist you with your booking at Coco Resort. How can I help you today?"

    if user_number not in conversations:
        conversations[user_number] = []
        reservations[user_number] = {}

    conversations[user_number].append({"role": "user", "content": incoming_msg})

    try:
        # Check if the message is about accommodation, location, amenities, restaurant hours, or why choose Coco Resort
        if "accommodation" in incoming_msg or "room" in incoming_msg or "villa" in incoming_msg:
            if "1 bedroom" in incoming_msg:
                response_msg = get_accommodation_info("1 bedroom, 1 bathroom apartment")
                reservations[user_number]['room_type'] = "1 bedroom, 1 bathroom apartment"
                reservations[user_number]['price_per_night'] = accommodations["1 bedroom, 1 bathroom apartment"]['price']
            elif "2 bedroom" in incoming_msg:
                response_msg = get_accommodation_info("2 bedroom, 2 bathroom villa")
                reservations[user_number]['room_type'] = "2 bedroom, 2 bathroom villa"
                reservations[user_number]['price_per_night'] = accommodations["2 bedroom, 2 bathroom villa"]['price']
            elif "3 bedroom" in incoming_msg:
                response_msg = get_accommodation_info("3 bedroom, 3 bathroom villa")
                reservations[user_number]['room_type'] = "3 bedroom, 3 bathroom villa"
                reservations[user_number]['price_per_night'] = accommodations["3 bedroom, 3 bathroom villa"]['price']
            elif "6 bedroom" in incoming_msg:
                response_msg = get_accommodation_info("6 bedroom, 4 bathroom villa")
                reservations[user_number]['room_type'] = "6 bedroom, 4 bathroom villa"
                reservations[user_number]['price_per_night'] = accommodations["6 bedroom, 4 bathroom villa"]['price']
            else:
                response_msg = "Specify the type of accommodation you're interested in. We offer various rooms and villas."
        elif "location" in incoming_msg or "how to get" in incoming_msg:
            response_msg = get_location_info()
        elif "amenities" in incoming_msg:
            response_msg = get_amenities_info()
        elif "restaurant hours" in incoming_msg or "restaurant" in incoming_msg:
            response_msg = get_restaurant_hours()
        elif "menu" in incoming_msg or "restaurant menu" in incoming_msg:
            response_msg = get_restaurant_menu()
        elif "why coco resort" in incoming_msg or "why choose coco resort" in incoming_msg:
            response_msg = get_why_coco_resort_info()
        elif "finalize reservation" in incoming_msg or "reservation summary" in incoming_msg:
            # Finalize the reservation and provide a summary
            response_msg = summarize_reservation(user_number)
        else:
            # OpenAI API call with conversation history
            messages = [
                {"role": "system", "content": "You are a charming and elegant customer service assistant for Coco Resort. Your job is to answer questions about bookings, accommodations, and services in a charismatic and persuasive manner."}
            ] + conversations[user_number]

            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150
            )

            # Get response content and count tokens
            response_content = response.choices[0].message.content.strip()
            response_tokens = len(encoding.encode(response_content))
            print(f"Response message tokens: {response_tokens}")

            response_msg = response_content
            conversations[user_number].append({"role": "assistant", "content": response_content})
            
            # Extract relevant information for the reservation
            if "name:" in response_content.lower():
                reservations[user_number]['name'] = response_content.split("name:")[1].strip()
            if "number of people:" in response_content.lower():
                reservations[user_number]['num_people'] = int(response_content.split("number of people:")[1].strip())
            if "dates:" in response_content.lower():
                dates = response_content.split("dates:")[1].strip().split(" to ")
                reservations[user_number]['start_date'] = dates[0]
                reservations[user_number]['end_date'] = dates[1]
            if "price per night:" in response_content.lower():
                price_per_night = response_content.split("price per night:")[1].strip()
                reservations[user_number]['price_per_night'] = int(price_per_night)
            if "total cost:" in response_content.lower():
                total_cost = response_content.split("total cost:")[1].strip()
                reservations[user_number]['total_cost'] = total_cost
    except Exception as e:
        response_msg = f"I'm terribly sorry, but I couldn't process your request. Error: {str(e)}"

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)


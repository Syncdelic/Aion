import csv
import re
import datetime
from dateutil import parser

def clean_text(text):
    """Cleans and normalizes the text for processing."""
    return ' '.join(text.split())

def extract_details_from_response(response_content):
    """Extracts reservation details from the response content."""
    details = {}
    lines = response_content.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            details[key.strip()] = value.strip()
    return details

def is_leap_year(year):
    """Checks if a given year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def extract_dates(date_range):
    date_patterns = [
        r"del? (\d{1,2} de \w+ de \d{4}) al? (\d{1,2} de \w+ de \d{4})",
        r"from (\w+ \d{1,2}, \d{4}) to (\w+ \d{1,2}, \d{4})",
        r"(\d{1,2}/\d{1,2}/\d{4}) - (\d{1,2}/\d{1,2}/\d{4})",
        r"(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})",
        r"(\d{2} \w+ \d{4}) - (\d{2} \w+ \d{4})",
        r"(\d{1,2}\w+ \w+ \d{4}) to (\d{1,2}\w+ \w+ \d{4})",
        r"(\d{1,2} de \w+ de \d{4}) al (\d{1,2} de \w+ de \d{4})",
    ]
    months_spanish = {
        "enero": "January", "febrero": "February", "marzo": "March", 
        "abril": "April", "mayo": "May", "junio": "June", 
        "julio": "July", "agosto": "August", "septiembre": "September", 
        "octubre": "October", "noviembre": "November", "diciembre": "December"
    }

    for pattern in date_patterns:
        match = re.search(pattern, date_range, re.IGNORECASE)
        if match:
            start_date_str, end_date_str = match.groups()
            print(f"Match found: {start_date_str} to {end_date_str}")  # Debug print
            try:
                if "de" in start_date_str.lower():  # Spanish date
                    for spanish, english in months_spanish.items():
                        start_date_str = start_date_str.replace(f"de {spanish} de", f"{english}")
                        end_date_str = end_date_str.replace(f"de {spanish} de", f"{english}")
                    print(f"Converted Spanish dates: {start_date_str} to {end_date_str}")  # Debug print
                start_date = parser.parse(start_date_str).strftime("%Y-%m-%d")
                end_date = parser.parse(end_date_str).strftime("%Y-%m-%d")
                print(f"Parsed dates: {start_date} to {end_date}")  # Debug print
                
                # Check for leap year in start and end dates
                start_date_obj = parser.parse(start_date_str)
                end_date_obj = parser.parse(end_date_str)
                if start_date_obj.month == 2 and start_date_obj.day == 29 and not is_leap_year(start_date_obj.year):
                    raise ValueError("Invalid start date: not a leap year.")
                if end_date_obj.month == 2 and end_date_obj.day == 29 and not is_leap_year(end_date_obj.year):
                    raise ValueError("Invalid end date: not a leap year.")
                
                return start_date, end_date
            except (ValueError, parser.ParserError) as e:
                print(f"Error parsing dates: {e}")  # Debug print
                raise ValueError("Invalid date format")
    print("No match found for date patterns")  # Debug print
    raise ValueError("Invalid date format")

def load_reservations(file_path):
    """Loads reservations from a CSV file."""
    reservations = []
    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                reservations.append(row)
    except FileNotFoundError:
        print(f"No existing file found at {file_path}. Starting a new reservations list.")
    except Exception as e:
        print(f"Error loading reservations: {e}")
    return reservations

def save_reservations(file_path, reservations):
    """Saves reservations to a CSV file."""
    try:
        with open(file_path, mode='w', newline='') as file:
            fieldnames = ['customer_id', 'customer_name', 'customer_contact', 'num_people', 'start_date', 'end_date', 'room_type', 'price_per_night', 'total_cost']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for reservation in reservations:
                writer.writerow(reservation)
    except Exception as e:
        print(f"Error saving reservations: {e}")

def convert_reservation_to_dict(reservation):
    """Converts a Reservation object to a dictionary for CSV storage."""
    return {
        'customer_id': reservation.customer.customer_id,
        'customer_name': reservation.customer.name,
        'customer_contact': reservation.customer.contact,
        'num_people': reservation.num_people,
        'start_date': reservation.start_date.strftime("%Y-%m-%d"),
        'end_date': reservation.end_date.strftime("%Y-%m-%d"),
        'room_type': reservation.room.type,
        'price_per_night': reservation.room.price,
        'total_cost': reservation.room.price * (reservation.end_date - reservation.start_date).days
    }

def add_reservation(file_path, reservation):
    """Adds a single reservation to the CSV file."""
    reservations = load_reservations(file_path)
    reservations.append(convert_reservation_to_dict(reservation))
    save_reservations(file_path, reservations)


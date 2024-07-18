import datetime

class Hotel:
    def __init__(self, name, address):
        if not name or not address:
            raise ValueError("Hotel name and address cannot be empty.")
        self.name = name
        self.address = address
        self.rooms = []

    def add_room(self, room):
        self.rooms.append(room)
        print(f"Room {room.number} added to hotel {self.name}")

class Room:
    def __init__(self, number, room_type, price):
        if price < 0:
            raise ValueError("Price cannot be negative.")
        self.number = number
        self.type = room_type
        self.price = price
        self.is_available = True

    def set_availability(self, availability):
        self.is_available = availability
        print(f"Room {self.number} availability set to {self.is_available}")

class Customer:
    def __init__(self, customer_id, name, contact):
        if not name or not contact:
            raise ValueError("Customer name and contact cannot be empty.")
        self.customer_id = customer_id
        self.name = name
        self.contact = contact
        self.reservations = []

    def make_reservation(self, reservation):
        for res in self.reservations:
            if res.room.number == reservation.room.number and res.overlaps(reservation):
                raise ValueError(f"Room {reservation.room.number} is not available.")
        self.reservations.append(reservation)
        reservation.room.set_availability(False)
        print(f"Reservation {reservation.reservation_id} made by {self.name} for room {reservation.room.number}")

    def cancel_reservation(self, reservation):
        if reservation in self.reservations:
            self.reservations.remove(reservation)
            reservation.room.set_availability(True)
            print(f"Reservation {reservation.reservation_id} canceled by {self.name}")

class Reservation:
    def __init__(self, reservation_id, room, customer, start_date, end_date, num_people):
        try:
            self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date format should be YYYY-MM-DD.")
        self.num_people = num_people
        self.reservation_id = reservation_id
        self.room = room
        self.customer = customer

    def overlaps(self, other):
        return self.start_date <= other.end_date and self.end_date >= other.start_date


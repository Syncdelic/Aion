import os
import unittest
import threading
from hotel_sys import *
from reservation_utils import *

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.hotel = Hotel("Coco Resort", "123 Beach Avenue")
        self.rooms = [Room(101, "1 Room, 1 Bathroom Apartment", 1100),
                      Room(102, "2 Rooms, 2 Bathrooms Villa", 2100),
                      Room(103, "3 Rooms, 3 Bathrooms Villa", 3100),
                      Room(104, "4 Rooms, 4 Bathrooms Villa", 4100)]
        for room in self.rooms:
            self.hotel.add_room(room)

        self.customer = Customer(1, "Aldo Rea", "12345")
        self.test_file = "test_reservations.csv"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_integration_reserve_room(self):
        start_date, end_date = extract_dates("Del 20 de julio de 2024 al 25 de julio de 2024")
        reservation = Reservation(1, self.rooms[2], self.customer, start_date, end_date, 2)
        self.customer.make_reservation(reservation)
        add_reservation(self.test_file, reservation)
        reservations = load_reservations(self.test_file)
        self.assertEqual(reservations[0]['customer_name'], "Aldo Rea")
        self.assertEqual(reservations[0]['customer_contact'], "12345")

    def test_integration_invalid_date_format(self):
        with self.assertRaises(ValueError):
            extract_dates("20-07-2024 to 25-07-2024")

    def test_integration_concurrent_reservations(self):
        def make_reservation(customer, room, start_date, end_date):
            reservation = Reservation(3, room, customer, start_date, end_date, 2)
            try:
                customer.make_reservation(reservation)
                add_reservation("test_reservations.csv", reservation)
            except ValueError:
                pass

        start_date, end_date = extract_dates("Del 20 de julio de 2024 al 25 de julio de 2024")
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_reservation, args=(self.customer, self.rooms[2], start_date, end_date))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        reservations = load_reservations("test_reservations.csv")
        self.assertEqual(len(reservations), 1)  # Only one reservation should succeed

if __name__ == "__main__":
    unittest.main()


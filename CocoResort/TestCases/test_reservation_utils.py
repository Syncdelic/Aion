import unittest
import os
from reservation_utils import *
from hotel_sys import *

class TestReservationUtils(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_reservations.csv"
        self.sample_customer = Customer(1, "Aldo Rea", "12345")
        self.sample_room = Room(101, "1 Room, 1 Bathroom Apartment", 1100)
        self.sample_reservation = Reservation(1, self.sample_room, self.sample_customer, "2024-07-20", "2024-07-25", 2)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_clean_text(self):
        self.assertEqual(clean_text("  hello \nworld \r "), "hello world")

    def test_extract_dates_spanish(self):
        dates = "Del 20 de julio de 2024 al 25 de julio de 2024"
        start_date, end_date = extract_dates(dates)
        self.assertEqual(start_date, '2024-07-20')
        self.assertEqual(end_date, '2024-07-25')

    def test_extract_dates_english(self):
        dates = "From July 20, 2024 to July 25, 2024"
        start_date, end_date = extract_dates(dates)
        self.assertEqual(start_date, '2024-07-20')
        self.assertEqual(end_date, '2024-07-25')

    def test_load_and_save_reservations(self):
        reservations = [convert_reservation_to_dict(self.sample_reservation)]
        save_reservations(self.test_file, reservations)
        loaded_reservations = load_reservations(self.test_file)
        self.assertEqual(loaded_reservations[0]['customer_name'], "Aldo Rea")

    def test_add_reservation(self):
        add_reservation(self.test_file, self.sample_reservation)
        loaded_reservations = load_reservations(self.test_file)
        self.assertEqual(loaded_reservations[0]['customer_name'], "Aldo Rea")
        self.assertEqual(loaded_reservations[0]['customer_contact'], "12345")

    def test_date_extraction_edge_cases(self):
        dates = "29 de febrero de 2024 al 5 de marzo de 2024"
        start_date, end_date = extract_dates(dates)
        self.assertEqual(start_date, '2024-02-29')
        self.assertEqual(end_date, '2024-03-05')

if __name__ == "__main__":
    unittest.main()


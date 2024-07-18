import unittest
from hotel_sys import Hotel, Room, Customer, Reservation
from threading import Thread

class TestHotelSys(unittest.TestCase):

    def setUp(self):
        self.hotel = Hotel("Coco Resort", "123 Beach Ave")
        self.rooms = [
            Room(101, "1 Room, 1 Bathroom Apartment", 1100),
            Room(102, "2 Rooms, 2 Bathrooms Villa", 2200),
            Room(103, "3 Rooms, 3 Bathrooms Villa", 3300),
            Room(104, "4 Rooms, 4 Bathrooms Villa", 4400),
        ]
        for room in self.rooms:
            self.hotel.add_room(room)
        self.customer = Customer(1, "Aldo Rea", "555-1234")

    def test_add_customer(self):
        self.assertEqual(self.customer.name, "Aldo Rea")
        self.assertEqual(self.customer.contact, "555-1234")

    def test_add_hotel(self):
        self.assertEqual(self.hotel.name, "Coco Resort")
        self.assertEqual(self.hotel.address, "123 Beach Ave")

    def test_add_invalid_customer(self):
        with self.assertRaises(ValueError):
            Customer(2, "", "555-5678")

    def test_add_invalid_hotel(self):
        with self.assertRaises(ValueError):
            Hotel("", "456 Ocean Blvd")

    def test_cancel_reservation(self):
        reservation = Reservation(1, self.rooms[0], self.customer, "2024-07-20", "2024-07-25", 2)
        self.customer.make_reservation(reservation)
        self.customer.cancel_reservation(reservation)
        self.assertTrue(self.rooms[0].is_available)

    def test_concurrent_reservations(self):
        def make_reservation(customer, room, start_date, end_date, num_people):
            reservation = Reservation(3, room, customer, start_date, end_date, num_people)
            try:
                customer.make_reservation(reservation)
            except ValueError as e:
                print(e)

        threads = []
        for _ in range(10):
            thread = Thread(target=make_reservation, args=(self.customer, self.rooms[2], "2024-07-20", "2024-07-25", 2))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(self.customer.reservations), 1)  # Only one reservation should succeed

    def test_invalid_date_format(self):
        with self.assertRaises(ValueError):
            Reservation(1, self.rooms[0], self.customer, "20-07-2024", "25-07-2024", 2)

    def test_modify_reservation(self):
        reservation = Reservation(1, self.rooms[0], self.customer, "2024-07-20", "2024-07-25", 2)
        self.customer.make_reservation(reservation)
        self.customer.cancel_reservation(reservation)
        new_reservation = Reservation(2, self.rooms[0], self.customer, "2024-07-26", "2024-07-30", 3)
        self.customer.make_reservation(new_reservation)
        self.assertIn(new_reservation, self.customer.reservations)

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            Room(105, "5 Rooms, 5 Bathrooms Villa", -5000)

    def test_no_room_available(self):
        reservation1 = Reservation(1, self.rooms[2], self.customer, "2024-07-20", "2024-07-25", 2)
        reservation2 = Reservation(2, self.rooms[2], self.customer, "2024-07-20", "2024-07-25", 2)
        self.customer.make_reservation(reservation1)
        with self.assertRaises(ValueError):
            self.customer.make_reservation(reservation2)

    def test_reserve_different_room_same_dates(self):
        reservation1 = Reservation(1, self.rooms[2], self.customer, "2024-07-20", "2024-07-25", 2)
        reservation2 = Reservation(2, self.rooms[3], self.customer, "2024-07-20", "2024-07-25", 2)
        self.customer.make_reservation(reservation1)
        self.customer.make_reservation(reservation2)
        self.assertIn(reservation2, self.customer.reservations)

    def test_reserve_room(self):
        reservation = Reservation(1, self.rooms[2], self.customer, "2024-07-20", "2024-07-25", 2)
        self.customer.make_reservation(reservation)
        self.assertIn(reservation, self.customer.reservations)

    def test_reserve_room_different_dates(self):
        reservation1 = Reservation(1, self.rooms[2], self.customer, "2024-07-20", "2024-07-25", 2)
        reservation2 = Reservation(2, self.rooms[2], self.customer, "2024-07-26", "2024-07-30", 2)
        self.customer.make_reservation(reservation1)
        self.customer.cancel_reservation(reservation1)
        self.customer.make_reservation(reservation2)
        self.assertIn(reservation2, self.customer.reservations)

if __name__ == "__main__":
    unittest.main()


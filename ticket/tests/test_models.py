from datetime import datetime

from django.utils.timezone import make_aware
from django.test import TestCase
from django_dynamic_fixture import G, F

from ticket.models import Event, TicketType, Order


class TicketTypeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = G(Event)

    def test_avaialble_tickets(self):
        ticket_type = G(TicketType, name="Test", quantity=5, event=self.event)
        all_tickets = list(ticket_type.tickets.all())

        five_available_tickets = set(ticket_type.available_tickets())

        # book one ticket
        ticket = all_tickets[0]
        ticket.order = G(Order, ticket_type=ticket_type, quantity=1)
        ticket.save()

        four_available_tickets = set(ticket_type.available_tickets())

        self.assertCountEqual(five_available_tickets, all_tickets)
        self.assertCountEqual(four_available_tickets, set(all_tickets) - {ticket})

    def test_save(self):
        """Verifying that the save method creates Ticket(s) upon TicketType creation"""

        ticket_type_1 = G(TicketType, name="Without quantity", event=self.event)
        ticket_type_5 = G(TicketType, name="Test", quantity=5, event=self.event)

        one_ticket = ticket_type_1.tickets.count()
        five_tickets = ticket_type_5.tickets.count()

        self.assertEqual(one_ticket, 1)
        self.assertEqual(five_tickets, 5)


class OrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = G(Event)

    def test_book_tickets(self):
        order = G(Order, ticket_type=F(quantity=5), quantity=3)

        pre_booking_ticket_count = order.tickets.count()
        order.book_tickets()
        post_booking_ticket_count = order.tickets.count()

        with self.assertRaisesRegexp(Exception, r"Order already fulfilled"):
            order.book_tickets()

        self.assertEqual(pre_booking_ticket_count, 0)
        self.assertEqual(post_booking_ticket_count, 3)

    def test_cancel_tickets(self):
        ticket_type: TicketType = G(TicketType, name="Test", quantity=5, event=self.event)
        outdated_order: Order = G(Order, ticket_type=ticket_type, quantity=2,
                                  created_at=make_aware(datetime(2022, 2, 1, 0, 28, 0)))

        with self.assertRaisesRegexp(Exception, r"You can only cancel orders within 30 minutes of purchase"):
            outdated_order.book_tickets()
            outdated_order.cancel_tickets()

        order: Order = G(Order, ticket_type=ticket_type, quantity=2)

        pre_booking_event_ticket_count = ticket_type.available_tickets().count()
        order.book_tickets()
        order.cancel_tickets()
        post_cancel_event_ticket_count = ticket_type.available_tickets().count()

        self.assertEqual(order.cancelled, True)
        self.assertEqual(pre_booking_event_ticket_count, post_cancel_event_ticket_count)

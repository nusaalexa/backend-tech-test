from django.core.management import BaseCommand
from django.db.models import Sum

from ticket.models import Order


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--e', '--event_name', type=str, help="Name of the event. REQUIRED if called with type 1")
        parser.add_argument('--t', '--type', type=int, help="Type of Analytics")

    def handle(self, *args, **kwargs):
        if kwargs['t'] == 1 and kwargs['e']:
            event_name = kwargs['e']
            total_orders_qs = Order.objects.filter(ticket_type__event__name=event_name)
            cancelled_orders_qs = total_orders_qs.filter(cancelled=True)

            total_orders = total_orders_qs.count()
            cancelled_orders = cancelled_orders_qs.count()

            try:
                return "Total number of orders for {}: {} \nTotal number of cancelled orders {:.1f}%".format(
                    event_name, total_orders, (cancelled_orders / total_orders) * 100)
            except ZeroDivisionError:
                return "No cancelled orders or no orders"

        if kwargs['t'] == 2:
            test = Order.objects.filter(cancelled=True).values("cancelled_at__date").annotate(
                total_cancelled=Sum("quantity")).order_by('-total_cancelled')[0]
            return "Date with most cancellations: {}".format(test['cancelled_at__date'])

        return "Invalid params"

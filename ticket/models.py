from django.db import models, transaction
from django.conf import settings
from django.utils import timezone

from .exceptions import Unauthorized, Unavailable


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name


class TicketType(models.Model):
    name = models.CharField(max_length=255)
    event = models.ForeignKey(Event, related_name="ticket_types", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, editable=False)

    quantity.help_text = "The number of actual tickets available upon creation"

    def available_tickets(self):
        return self.tickets.filter(order__isnull=True)

    def save(self, *args, **kwargs):
        new = not self.pk
        super().save(*args, **kwargs)
        if new:
            self.tickets.bulk_create([Ticket(ticket_type=self)] * self.quantity)

    def __str__(self):
        return '{}: {}'.format(self.event.name, self.name)


class Ticket(models.Model):
    ticket_type = models.ForeignKey(TicketType, related_name="tickets", on_delete=models.CASCADE)
    order = models.ForeignKey(
        "ticket.Order", related_name="tickets", default=None, null=True, on_delete=models.SET_NULL
    )


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.PROTECT)
    ticket_type = models.ForeignKey(TicketType, related_name="orders", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    fulfilled = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    def book_tickets(self):
        if self.fulfilled:
            raise Exception("Order already fulfilled")
        qs = self.ticket_type.available_tickets().select_for_update(skip_locked=True)[: self.quantity]

        try:
            with transaction.atomic():
                updated_count = self.ticket_type.tickets.filter(id__in=qs).update(order=self)
                if updated_count != self.quantity:
                    raise Exception
        except Exception:
            return
        self.fulfilled = True
        self.save(update_fields=["fulfilled"])

    def cancel_tickets(self, pk=None):
        if self.cancelled:
            raise Unavailable("Order already cancelled.")

        if not self.fulfilled:
            raise Unavailable("Order not fulfilled yet. Try again later.")

        time_difference = (timezone.now() - self.created_at).total_seconds() / 60
        if time_difference >= 30:
            raise Unauthorized("You can only cancel orders within 30 minutes of purchase")

        self.ticket_type.tickets.filter(order__id=(pk or self.pk)).update(order=None)

        self.cancelled = True
        self.cancelled_at = timezone.now()
        self.save(update_fields=["cancelled", "cancelled_at"])

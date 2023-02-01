from django.contrib import admin
from ticket.models import Ticket, Event, TicketType, Order

# Register your models here.
admin.site.register(Ticket)
admin.site.register(Event)
admin.site.register(TicketType)
admin.site.register(Order)

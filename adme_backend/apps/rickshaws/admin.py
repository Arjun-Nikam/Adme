from django.contrib import admin
from .models import Driver, HardwareUnit, Rickshaw, GpsPing, UptimeLog

admin.site.register([Driver, HardwareUnit, Rickshaw, GpsPing, UptimeLog])

from django.contrib import admin
from .models import AdMedia, AuditLog

admin.site.register(AuditLog)
admin.site.register(AdMedia)

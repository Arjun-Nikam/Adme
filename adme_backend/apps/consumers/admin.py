from django.contrib import admin
from .models import Consumer, MerchantLoyaltyPoints, Redemption

admin.site.register([Consumer, MerchantLoyaltyPoints, Redemption])

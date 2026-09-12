from django.contrib import admin
from .models import Category, Plan, Merchant, AreaMapping, Campaign, Offer, CampaignMetric, Report

admin.site.register([Category, Plan, Merchant, AreaMapping, Campaign, Offer, CampaignMetric, Report])

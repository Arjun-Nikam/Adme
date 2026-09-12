from django.urls import path

from .views import (
    AdvertiserDetailView,
    AdvertiserDirectoryView,
    LiveFleetView,
    PlatformOverviewView,
)

urlpatterns = [
    path(
        "platform-overview/",
        PlatformOverviewView.as_view(),
        name="platform-overview",
    ),
    path("advertisers/", AdvertiserDirectoryView.as_view(), name="advertiser-directory"),
    path("advertisers/<int:pk>/", AdvertiserDetailView.as_view(), name="advertiser-detail"),
    path("live-fleet/", LiveFleetView.as_view(), name="live-fleet"),
]

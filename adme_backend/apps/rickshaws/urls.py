from rest_framework.routers import DefaultRouter
from .views import DriverViewSet, HardwareUnitViewSet, RickshawViewSet, GpsPingViewSet, UptimeLogViewSet

router = DefaultRouter()
router.register("drivers", DriverViewSet, basename="driver")
router.register("hardware", HardwareUnitViewSet, basename="hardware")
router.register("rickshaws", RickshawViewSet, basename="rickshaw")
router.register("gps-pings", GpsPingViewSet, basename="gps-ping")
router.register("uptime-logs", UptimeLogViewSet, basename="uptime-log")

urlpatterns = router.urls

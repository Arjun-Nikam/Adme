from rest_framework.routers import DefaultRouter
from .views import ConsumerViewSet, MerchantLoyaltyPointsViewSet, RedemptionViewSet

router = DefaultRouter()
router.register("consumers", ConsumerViewSet, basename="consumer")
router.register("loyalty-points", MerchantLoyaltyPointsViewSet, basename="loyalty-points")
router.register("redemptions", RedemptionViewSet, basename="redemption")

urlpatterns = router.urls

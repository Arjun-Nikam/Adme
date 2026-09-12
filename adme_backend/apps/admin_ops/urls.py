from rest_framework.routers import DefaultRouter
from .views import AdMediaViewSet, AuditLogViewSet, MerchantVerificationViewSet

router = DefaultRouter()
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("merchant-verifications", MerchantVerificationViewSet, basename="merchant-verification")
router.register("media", AdMediaViewSet, basename="ad-media")

urlpatterns = router.urls

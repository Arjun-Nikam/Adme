from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, PlanViewSet, MerchantViewSet, AreaMappingViewSet,
    CampaignViewSet, OfferViewSet, CampaignMetricViewSet, ReportViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("plans", PlanViewSet, basename="plan")
router.register("merchants", MerchantViewSet, basename="merchant")
router.register("area-mappings", AreaMappingViewSet, basename="area-mapping")
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("offers", OfferViewSet, basename="offer")
router.register("campaign-metrics", CampaignMetricViewSet, basename="campaign-metric")
router.register("reports", ReportViewSet, basename="report")

urlpatterns = router.urls

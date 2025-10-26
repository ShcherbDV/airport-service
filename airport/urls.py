from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirportViewSet,
    AirplaneTypeViewSet,
    CrewViewSet,
    AirplaneViewSet,
    RouteViewSet,
    FlightViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("crews", CrewViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("routes", RouteViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)
urlpatterns = [path("", include(router.urls))]

app_name = "airport"

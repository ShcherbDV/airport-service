from datetime import datetime

from django.db.models import F, Count
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

from airport.models import Airport, AirplaneType, Crew, Airplane, Order, Route, Flight
from airport.serializers import AirportSerializer, AirplaneTypeSerializer, CrewSerializer, AirplaneSerializer, \
    OrderSerializer, OrderListSerializer, RouteSerializer, FlightSerializer, FlightDetailSerializer, \
    FlightListSerializer


class AirportViewSet(GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class AirplaneTypeViewSet(GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class CrewViewSet(GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirplaneViewSet(GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer


class RouteViewSet(GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects.all()
        .select_related("route", "airplane")
        .annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        route_id_str = self.request.query_params.get("route")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=date)

        if route_id_str:
            queryset = queryset.filter(route_id=int(route_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.prefetch_related(
        "tickets__flight__route", "tickets__flight__airplane"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


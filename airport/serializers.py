from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import AirplaneType, Airport, Airplane, Crew, Route, Flight, Ticket, Order


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = serializers.SerializerMethodField(read_only=True)
    airplane_type_id = serializers.PrimaryKeyRelatedField(
        queryset=AirplaneType.objects.all(),
        write_only=True,
        source="airplane_type",
        label="Airplane Type",
    )

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type_id", "airplane_type")

    def get_airplane_type(self, obj):
        return obj.airplane_type.name if obj.airplane_type_id else None


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField(read_only=True)
    source_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(),
        write_only=True,
        source="source",
        label="Source"
    )
    destination = serializers.SerializerMethodField(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(),
        write_only=True,
        source="destination",
        label="Destination"
    )
    class Meta:
        model = Route
        fields = ("id", "source", "source_id", "destination", "destination_id", "distance")

    def get_source(self, obj):
        return obj.source.name if obj.source_id else None

    def get_destination(self, obj):
        return obj.destination.name if obj.destination_id else None


class FlightSerializer(serializers.ModelSerializer):
    route_id = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all(),
        source="route",
        label="Route"
    )
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(),
        source="airplane",
        label="Airplane"
    )
    class Meta:
        model = Flight
        fields = ("id", "departure_time", "arrival_time", "route_id", "airplane_id")


class FlightListSerializer(serializers.ModelSerializer):
    airplane = AirplaneSerializer(read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)
    route = RouteSerializer(read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "departure_time", "arrival_time", "route", "airplane", "tickets_available")


class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteSerializer(many=False, read_only=True)
    airplane = AirplaneSerializer(many=False, read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "departure_time", "arrival_time", "route", "airplane")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

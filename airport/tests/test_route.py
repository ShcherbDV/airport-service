from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Airport, Route
from airport.serializers import RouteSerializer

ROUTE_URL = reverse("airport:route-list")
FLIGHT_URL = reverse("airport:flight-list")


def sample_airport(**params):
    defaults = {
        "name": "WAW",
        "closest_big_city": "Warsaw",
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)

def sample_route(**params):
    airport1 = sample_airport()
    airport2 = sample_airport(name="ORY", closest_big_city="Paris")
    defaults = {
        "source": airport1,
        "destination": airport2,
        "distance": 1371,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        sample_route()
        sample_route()

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.order_by("id")
        serializer = RouteSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        airport1 = sample_airport()
        airport2 = sample_airport()
        payload = {
            "source_id": airport1.id,
            "destination_id": airport2.id,
            "distance": 1,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "testpass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        airport1 = sample_airport()
        airport2 = sample_airport()
        payload = {
            "source_id": airport1.id,
            "destination_id": airport2.id,
            "distance": 1,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        route = Route.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(route, key))

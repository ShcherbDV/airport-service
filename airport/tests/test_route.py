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

    def test_filter_movies_by_actors(self):
        actor1 = Actor.objects.create(first_name="Actor 1", last_name="Last 1")
        actor2 = Actor.objects.create(first_name="Actor 2", last_name="Last 2")

        movie1 = sample_movie(title="Movie 1")
        movie2 = sample_movie(title="Movie 2")

        movie1.actors.add(actor1)
        movie2.actors.add(actor2)

        movie3 = sample_movie(title="Movie without actors")

        res = self.client.get(
            MOVIE_URL, {"actors": f"{actor1.id},{actor2.id}"}
        )

        serializer1 = MovieListSerializer(movie1)
        serializer2 = MovieListSerializer(movie2)
        serializer3 = MovieListSerializer(movie3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_movies_by_title(self):
        movie1 = sample_movie(title="Movie")
        movie2 = sample_movie(title="Another Movie")
        movie3 = sample_movie(title="No match")

        res = self.client.get(MOVIE_URL, {"title": "movie"})

        serializer1 = MovieListSerializer(movie1)
        serializer2 = MovieListSerializer(movie2)
        serializer3 = MovieListSerializer(movie3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

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
            "admin@admin.com", "testpass", is_staff=True,
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

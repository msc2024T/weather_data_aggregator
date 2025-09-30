from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, Mock
from rest_framework import status
from rest_framework.test import APITestCase
from .serializers import WeatherRequestSerializer, CityListSerializer, WeatherDataSerializer
from .models import WeatherRequest, WeatherData
from .tasks import get_weather
import json


class WeatherRequestSerializerTest(TestCase):

    def setUp(self):
        self.weather_request = WeatherRequest.objects.create(
            requester_ip="192.168.1.1",
            status="PENDING",
            city_count=2
        )

    def test_valid_serializer_data(self):
        """Test WeatherRequestSerializer with valid data"""
        serializer = WeatherRequestSerializer(self.weather_request)
        data = serializer.data

        self.assertEqual(data['requester_ip'], "192.168.1.1")
        self.assertEqual(data['status'], "PENDING")
        self.assertEqual(data['city_count'], 2)
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('data', data)

    def test_serializer_with_weather_data(self):
        """Test serializer includes nested weather data"""

        WeatherData.objects.create(
            request=self.weather_request,
            city="London",
            temperature=20.5,
            wind_kph=15.2,
            humidity=65
        )

        serializer = WeatherRequestSerializer(self.weather_request)
        data = serializer.data

        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['city'], "London")
        self.assertEqual(data['data'][0]['temperature'], 20.5)


class CityListSerializerTest(TestCase):

    def test_valid_city_list(self):
        """Test CityListSerializer with valid cities"""
        data = {"cities": ["London", "Paris", "Tokyo"]}
        serializer = CityListSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['cities']), 3)

    def test_empty_city_list(self):
        """Test CityListSerializer with empty list"""
        data = {"cities": []}
        serializer = CityListSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('cities', serializer.errors)

    def test_too_many_cities(self):
        """Test CityListSerializer with more than 10 cities"""
        cities = [f"City{i}" for i in range(15)]
        data = {"cities": cities}
        serializer = CityListSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('cities', serializer.errors)

    def test_invalid_city_format(self):
        """Test CityListSerializer with invalid city format (empty/whitespace)"""
        data = {"cities": ["", "   ", "ValidCity"]}
        serializer = CityListSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('cities', serializer.errors)

    def test_valid_city_names_only(self):
        """Test CityListSerializer with only valid non-empty cities"""
        data = {"cities": ["London", "Paris", "New York"]}
        serializer = CityListSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['cities']), 3)

    def test_city_names_with_whitespace_trimming(self):
        """Test CityListSerializer trims whitespace from city names"""
        data = {"cities": [" London ", "  Paris  ", "Tokyo"]}
        serializer = CityListSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        cities = serializer.validated_data['cities']
        self.assertEqual(cities, ["London", "Paris", "Tokyo"])


class WeatherDataModelTest(TestCase):

    def setUp(self):
        self.weather_request = WeatherRequest.objects.create(
            requester_ip="192.168.1.1",
            status="PENDING",
            city_count=1
        )

    def test_weather_data_creation(self):
        """Test creating WeatherData object"""
        weather_data = WeatherData.objects.create(
            request=self.weather_request,
            city="London",
            temperature=22.5,
            wind_kph=12.0,
            humidity=70,
            last_updated=timezone.now()
        )

        self.assertEqual(weather_data.city, "London")
        self.assertEqual(weather_data.temperature, 22.5)
        self.assertEqual(weather_data.wind_kph, 12.0)
        self.assertEqual(weather_data.humidity, 70)
        self.assertEqual(weather_data.request, self.weather_request)

    def test_weather_request_relationship(self):
        """Test relationship between WeatherRequest and WeatherData"""
        WeatherData.objects.create(
            request=self.weather_request,
            city="Paris",
            temperature=18.0,
            wind_kph=8.5,
            humidity=60
        )

        self.assertEqual(self.weather_request.data.count(), 1)
        self.assertEqual(self.weather_request.data.first().city, "Paris")


class WeatherAPIViewTest(APITestCase):

    def setUp(self):
        self.client = Client()
        self.request_weather_url = reverse('core:request_weather')

    def test_post_valid_cities(self):
        """Test POST request with valid cities"""
        data = {"cities": ["London", "Paris"]}

        with patch('core.views.get_weather.delay') as mock_delay:
            mock_delay.return_value = Mock(id="test-task-id")

            response = self.client.post(
                self.request_weather_url,
                data=json.dumps(data),
                content_type='application/json'
            )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('request_id', response.json())
        self.assertIn('task_id', response.json())
        self.assertEqual(response.json()['cities'], ["London", "Paris"])
        self.assertEqual(response.json()['status'], 'PENDING')

    def test_post_invalid_cities(self):
        """Test POST request with invalid cities"""
        data = {"cities": []}  # Empty list

        response = self.client.post(
            self.request_weather_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())

    def test_post_missing_cities(self):
        """Test POST request without cities field"""
        data = {"invalid_field": "test"}

        response = self.client.post(
            self.request_weather_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_weather_request_detail(self):
        """Test GET request for weather request details"""

        weather_request = WeatherRequest.objects.create(
            requester_ip="127.0.0.1",
            status="SUCCESS",
            city_count=1
        )

        # Create associated weather data
        WeatherData.objects.create(
            request=weather_request,
            city="London",
            temperature=20.0,
            wind_kph=10.0,
            humidity=65
        )

        url = reverse('core:weather_request_detail', kwargs={
                      'request_id': weather_request.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], weather_request.id)
        self.assertEqual(response.json()['status'], 'SUCCESS')
        self.assertEqual(len(response.json()['data']), 1)

    def test_get_nonexistent_weather_request(self):
        """Test GET request for non-existent weather request"""
        url = reverse('core:weather_request_detail',
                      kwargs={'request_id': 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())


class WeatherTaskTest(TestCase):

    def setUp(self):
        self.weather_request = WeatherRequest.objects.create(
            requester_ip="192.168.1.1",
            status="PENDING",
            city_count=1
        )

    @patch('core.tasks.requests.get')
    def test_successful_weather_task(self, mock_get):
        """Test successful weather data fetching task"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "location": {"name": "London"},
            "current": {
                "temp_c": 20.0,
                "wind_kph": 15.0,
                "humidity": 65,
                "last_updated": "2025-09-30 12:00"
            }
        }
        mock_get.return_value = mock_response

        result = get_weather(self.weather_request.id, "London")

        self.assertEqual(result['final_status'], 'SUCCESS')
        self.assertEqual(result['successful_saves'], 1)

        # Check if weather data was saved
        weather_data = WeatherData.objects.filter(
            request=self.weather_request).first()
        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data.city, "London")
        self.assertEqual(weather_data.temperature, 20.0)

    @patch('core.tasks.requests.get')
    def test_failed_weather_task(self, mock_get):
        """Test failed weather data fetching task"""
        # Mock API failure
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "City not found"
        mock_get.return_value = mock_response

        result = get_weather(self.weather_request.id, "InvalidCity")

        self.assertEqual(result['final_status'], 'FAILED')
        self.assertEqual(result['successful_saves'], 0)

        # Check if request status was updated
        self.weather_request.refresh_from_db()
        self.assertEqual(self.weather_request.status, 'FAILED')

    def test_nonexistent_request_id(self):
        """Test task with non-existent request ID"""
        result = get_weather(9999, "London")

        self.assertIn('error', result)
        self.assertIn('not found', result['error'])


class WeatherRequestListViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('core:weather_request_list')

    def test_get_weather_requests_by_ip(self):
        """Test getting weather requests filtered by IP"""

        WeatherRequest.objects.create(
            requester_ip="192.168.1.1",
            status="SUCCESS",
            city_count=1
        )
        WeatherRequest.objects.create(
            requester_ip="192.168.1.2",
            status="PENDING",
            city_count=2
        )

        with patch('core.views.RequestWeatherView.get_client_ip', return_value="192.168.1.1"):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(
            response.json()['results'][0]['requester_ip'], "192.168.1.1")

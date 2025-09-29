from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .serializers import WeatherRequestSerializer, CityListSerializer
from .models import WeatherRequest, WeatherData
from .tasks import get_weather
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RequestWeatherView(APIView):
    @swagger_auto_schema(
        request_body=CityListSerializer,
        responses={201: "Weather request created"}
    )
    def post(self, request):

        serializer = CityListSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        cities = serializer.validated_data['cities']

        client_ip = self.get_client_ip(request)

        weather_request = WeatherRequest.objects.create(
            requester_ip=client_ip,
            city_count=len(cities),
            status='PENDING'
        )

        try:
            # Pass request_id as first argument to the task
            task_result = get_weather.delay(weather_request.id, *cities)

            return Response({
                'message': 'Weather request submitted successfully',
                'request_id': weather_request.id,
                'task_id': str(task_result.id),
                'cities': cities,
                'status': 'PENDING'
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:

            weather_request.status = 'FAILED'
            weather_request.save()

            return Response({
                'error': 'Failed to process weather request',
                'details': str(e),
                'request_id': weather_request.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_client_ip(request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class WeatherRequestDetailView(APIView):
    @swagger_auto_schema(
        operation_description="Get detailed weather request with all weather data",
        responses={
            200: WeatherRequestSerializer,
            404: openapi.Response(
                description="Weather request not found",
                examples={
                    "application/json": {
                        "error": "Weather request not found"
                    }
                }
            )
        }
    )
    def get(self, request, request_id):
        try:

            weather_request = WeatherRequest.objects.prefetch_related(
                'data').get(id=request_id)
            serializer = WeatherRequestSerializer(weather_request)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except WeatherRequest.DoesNotExist:
            return Response(
                {'error': 'Weather request not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class WeatherRequestListView(APIView):
    @swagger_auto_schema(
        operation_description="List all weather requests for the current user (filtered by IP)",
        responses={200: WeatherRequestSerializer(many=True)}
    )
    def get(self, request):
        # Get client IP address
        ip = RequestWeatherView.get_client_ip(request)

        # Filter requests by client IP and prefetch related data
        queryset = WeatherRequest.objects.filter(
            requester_ip=ip
        ).prefetch_related('data').order_by('-created_at')

        serializer = WeatherRequestSerializer(queryset, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

from rest_framework import serializers
from .models import WeatherRequest, WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = '__all__'


class WeatherRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = WeatherRequest
        fields = '__all__'


class CityListSerializer(serializers.Serializer):

    cities = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=10,
        help_text="List of city names to get weather for"
    )

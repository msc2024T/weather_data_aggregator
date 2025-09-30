from rest_framework import serializers
from .models import WeatherRequest, WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = ['id', 'city', 'temperature',
                  'wind_kph', 'humidity', 'last_updated']


class WeatherRequestSerializer(serializers.ModelSerializer):
    data = WeatherDataSerializer(many=True, read_only=True)

    class Meta:
        model = WeatherRequest
        fields = ['id', 'requester_ip', 'status', 'city_count',
                  'created_at', 'updated_at', 'data']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CityListSerializer(serializers.Serializer):
    """Serializer for validating city list input"""
    cities = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=10,
        help_text="List of city names to get weather for"
    )

    def validate_cities(self, value):
        """Custom validation for cities list"""
        validated_cities = []
        for city in value:
            # Strip whitespace and check if city name is not empty
            clean_city = city.strip()
            if not clean_city:
                raise serializers.ValidationError(
                    "City names cannot be empty or contain only whitespace"
                )
            validated_cities.append(clean_city)
        return validated_cities

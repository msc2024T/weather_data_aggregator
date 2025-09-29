from django.db import models


class WeatherRequest(models.Model):
    requester_ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("SUCCESS", "Success"),
            ("PARTIAL", "Partial Success"),
            ("FAILED", "Failed")
        ],
        default="PENDING"
    )
    city_count = models.PositiveIntegerField(
        default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WeatherData(models.Model):
    request = models.ForeignKey(
        WeatherRequest, on_delete=models.CASCADE, related_name="data")
    city = models.CharField(max_length=100, null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)  # temp_c
    wind_kph = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

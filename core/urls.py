from django.urls import path
from .views import RequestWeatherView, WeatherRequestDetailView, WeatherRequestListView

app_name = 'core'

urlpatterns = [
    path('weather/request/', RequestWeatherView.as_view(), name='request_weather'),
    path('weather/request/<int:request_id>/',
         WeatherRequestDetailView.as_view(), name='weather_request_detail'),
    path('weather/requests/', WeatherRequestListView.as_view(),
         name='weather_request_list'),
]

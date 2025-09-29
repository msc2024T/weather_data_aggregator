from celery import shared_task
from django.conf import settings
import requests


@shared_task
def get_weather(*args):
    api_key = settings.WEATHER_API_KEY
    result = []

    for city in args:
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result.append(response.json())

        except requests.RequestException as e:
            return {"error": str(e)}

    return result

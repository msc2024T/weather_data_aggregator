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
            response = requests.get(url, timeout=10)  # Add timeout

            if response.status_code == 200:
                weather_data = response.json()
                result.append(weather_data)
            else:
                # Handle HTTP errors (404, 401, etc.)
                result.append({
                    'city': city,
                    'error': f'HTTP {response.status_code}: {response.text}'
                })

        except requests.RequestException as e:
            # Handle network/connection errors for this specific city
            result.append({
                'city': city,
                'error': f'Request failed: {str(e)}'
            })
        except Exception as e:
            # Handle any other unexpected errors
            result.append({
                'city': city,
                'error': f'Unexpected error: {str(e)}'
            })

    return result

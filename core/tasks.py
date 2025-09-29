from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests
from .models import WeatherRequest, WeatherData
from datetime import datetime


@shared_task
def get_weather(request_id, *cities):

    api_key = settings.WEATHER_API_KEY
    result = []
    successful_saves = 0

    try:

        weather_request = WeatherRequest.objects.get(id=request_id)

        for city in cities:
            url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
            try:
                response = requests.get(url, timeout=10)
                print(response)

                if response.status_code == 200:
                    weather_data = response.json()

                    current = weather_data.get('current', {})

                    # Parse last_updated datetime
                    last_updated_str = current.get('last_updated')
                    last_updated = None
                    if last_updated_str:
                        try:
                            last_updated = datetime.strptime(
                                last_updated_str, '%Y-%m-%d %H:%M')
                        except ValueError:
                            last_updated = timezone.now()

                    weather_obj = WeatherData.objects.create(
                        request=weather_request,
                        city=city,
                        temperature=current.get('temp_c'),
                        wind_kph=current.get('wind_kph'),
                        humidity=current.get('humidity'),
                        last_updated=last_updated or timezone.now()
                    )

                    successful_saves += 1
                    result.append({
                        'city': city,
                        'status': 'success',
                        'data_id': weather_obj.id
                    })
                else:
                    # Handle HTTP errors
                    result.append({
                        'city': city,
                        'status': 'error',
                        'error': f'HTTP {response.status_code}: {response.text}'
                    })

            except requests.RequestException as e:
                result.append({
                    'city': city,
                    'status': 'error',
                    'error': f'Request failed: {str(e)}'
                })
            except Exception as e:
                result.append({
                    'city': city,
                    'status': 'error',
                    'error': f'Unexpected error: {str(e)}'
                })

        # Update WeatherRequest status based on results
        if successful_saves > 0:
            if successful_saves == len(cities):
                weather_request.status = 'SUCCESS'
            else:
                weather_request.status = 'PARTIAL'
        else:
            weather_request.status = 'FAILED'

        weather_request.save()

        return {
            'request_id': request_id,
            'total_cities': len(cities),
            'successful_saves': successful_saves,
            'final_status': weather_request.status,
            'results': result
        }

    except WeatherRequest.DoesNotExist:
        return {
            'error': f'WeatherRequest with id {request_id} not found',
            'request_id': request_id
        }
    except Exception as e:
        # Update request status to FAILED if it exists
        try:
            weather_request = WeatherRequest.objects.get(id=request_id)
            weather_request.status = 'FAILED'
            weather_request.save()
        except:
            pass

        return {
            'error': f'Task failed: {str(e)}',
            'request_id': request_id
        }

"""Weather-related tools for the weather agent"""

from pydantic_ai import RunContext
from tools.location_tools import WeatherDeps


async def get_weather(ctx: RunContext[WeatherDeps], latitude: float, longitude: float) -> dict:
    """Get current weather for given coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Dictionary with current weather data including temperature, conditions, etc.
    """
    try:
        # Using Open-Meteo API (free, no API key required)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m',
            'temperature_unit': 'fahrenheit',
            'wind_speed_unit': 'mph',
            'precipitation_unit': 'inch'
        }

        response = await ctx.deps.http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        current = data['current']

        # Weather code mapping (simplified)
        weather_codes = {
            0: 'Clear sky',
            1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Foggy', 48: 'Depositing rime fog',
            51: 'Light drizzle', 53: 'Moderate drizzle', 55: 'Dense drizzle',
            61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
            71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
            95: 'Thunderstorm'
        }

        weather_desc = weather_codes.get(current['weather_code'], 'Unknown')

        return {
            'temperature': current['temperature_2m'],
            'feels_like': current['apparent_temperature'],
            'humidity': current['relative_humidity_2m'],
            'wind_speed': current['wind_speed_10m'],
            'precipitation': current['precipitation'],
            'conditions': weather_desc,
            'units': {
                'temperature': '°F',
                'wind_speed': 'mph',
                'precipitation': 'inches'
            }
        }
    except Exception as e:
        return {'error': f'Failed to get weather: {str(e)}'}

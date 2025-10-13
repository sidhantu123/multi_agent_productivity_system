"""Location-related tools for the weather agent"""

from pydantic_ai import RunContext
from dataclasses import dataclass
import httpx


@dataclass
class WeatherDeps:
    """Dependencies for weather agent tools"""
    http_client: httpx.AsyncClient


async def get_user_location(ctx: RunContext[WeatherDeps]) -> dict:
    """Get the user's approximate location based on IP address.

    Returns:
        Dictionary with city, region, country, latitude, and longitude
    """
    try:
        response = await ctx.deps.http_client.get('http://ip-api.com/json/')
        response.raise_for_status()
        data = response.json()

        return {
            'city': data.get('city', 'Unknown'),
            'region': data.get('regionName', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'latitude': data.get('lat'),
            'longitude': data.get('lon')
        }
    except Exception as e:
        return {'error': f'Failed to get location: {str(e)}'}


async def get_lat_long(ctx: RunContext[WeatherDeps], city: str, country: str = "US") -> dict:
    """Get latitude and longitude for a city name.

    Args:
        city: Name of the city
        country: Country code (default: US)

    Returns:
        Dictionary with latitude, longitude, and location name
    """
    try:
        # Using OpenMeteo geocoding API (free, no API key required)
        url = f"https://geocoding-api.open-meteo.com/v1/search"
        params = {
            'name': city,
            'count': 1,
            'language': 'en',
            'format': 'json'
        }

        response = await ctx.deps.http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get('results'):
            result = data['results'][0]
            return {
                'latitude': result['latitude'],
                'longitude': result['longitude'],
                'name': result['name'],
                'country': result.get('country', ''),
                'admin1': result.get('admin1', '')  # State/region
            }
        else:
            return {'error': f'Could not find coordinates for {city}'}
    except Exception as e:
        return {'error': f'Failed to geocode: {str(e)}'}


async def convert_address_to_lat_long(ctx: RunContext[WeatherDeps], address: str) -> dict:
    """Convert a full address to latitude and longitude coordinates.

    Args:
        address: Full address string (e.g., "1600 Amphitheatre Parkway, Mountain View, CA")

    Returns:
        Dictionary with latitude, longitude, and formatted address
    """
    try:
        # Using Nominatim (OpenStreetMap) - free, no API key required
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'PydanticAI-Weather-Agent/1.0'
        }

        response = await ctx.deps.http_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data:
            result = data[0]
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result['display_name']
            }
        else:
            return {'error': f'Could not find coordinates for address: {address}'}
    except Exception as e:
        return {'error': f'Failed to geocode address: {str(e)}'}

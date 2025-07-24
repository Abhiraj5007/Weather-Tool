# filepath: /weather-tool/weather-tool/weather.py
# Command Line Weather Tool

import requests
import json
import time
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import argparse

class WeatherCache:
    
    def __init__(self, expiry_minutes: int = 5): 
        self.cache = {}
        self.expiry_seconds = expiry_minutes * 60 #Cache will expire in 5 min
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.expiry_seconds:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Dict) -> None:
        # Storing data in cache with timestamp for checking
        self.cache[key] = (data, time.time())
    
    def clear_expired(self) -> None:
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.expiry_seconds
        ]
        for key in expired_keys:
            del self.cache[key]

class WeatherTool:
    # Now this is main weather tool
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.cache = WeatherCache()
        self.session = requests.Session()
    
    def validate_input(self, location: str) -> Tuple[bool, str, str]:
        
        location = location.strip()
        
        if re.match(r'^\d{6}$', location):
            return True, "pincode", location

        if re.match(r'^[a-zA-Z\s\-\.\']+$', location) and len(location) > 0:
            normalized = location.lower().strip()
            city_variations = {
                'new delhi': 'New Delhi',
                'delhi': 'Delhi',
                'mumbai': 'Mumbai',
                'bangalore': 'Bengaluru',
                'kolkata': 'Kolkata',
                'chennai': 'Chennai',
                'hyderabad': 'Hyderabad',
                'pune': 'Pune'
            }
            
            if normalized in city_variations:
                return True, "city", city_variations[normalized]
            else:
                return True, "city", location.title()
        
        return False, "", ""
    
    def build_api_url(self, location: str, location_type: str, endpoint: str) -> str:
        
        if location_type == "pincode":
            query = f"zip={location},IN"
        else:
            query = f"q={location},IN"
        
        return f"{self.base_url}/{endpoint}?{query}&appid={self.api_key}&units=metric"
    
    def fetch_weather_data(self, location: str, location_type: str) -> Optional[Dict]:
        
        cache_key = f"{location_type}:{location}"
        
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print("Using cached data...")
            return cached_data
        
        # Error handling
        try:
            # Fetch current weather
            current_url = self.build_api_url(location, location_type, "weather")
            current_response = self.session.get(current_url, timeout=10)
            
            if current_response.status_code == 404:
                print("Location not found. Please check the city name or pincode.")
                return None
            elif current_response.status_code == 401:
                print("Invalid API key. Please check your OpenWeatherMap API key.")
                return None
            elif current_response.status_code != 200:
                print(f"API Error: {current_response.status_code}")
                return None
            
            current_data = current_response.json()
            
            forecast_url = self.build_api_url(location, location_type, "forecast")
            forecast_response = self.session.get(forecast_url, timeout=10)
            
            if forecast_response.status_code != 200:
                print("Could not fetch forecast data, showing current weather only.")
                forecast_data = None
            else:
                forecast_data = forecast_response.json()
            
            # Combine data
            weather_data = {
                'current': current_data,
                'forecast': forecast_data,
                'fetched_at': datetime.now().isoformat()
            }
            
            # Cache the data
            self.cache.set(cache_key, weather_data)
            
            return weather_data
            
        except requests.exceptions.Timeout:
            print("Request timeout. Please check your internet connection.")
            return None
        except requests.exceptions.ConnectionError:
            print("Connection error. Please check your internet connection.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return None
        except json.JSONDecodeError:
            print("Invalid response from weather service.")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None
    
    def format_current_weather(self, data: Dict) -> str:
        weather = data['current']
        
        location_name = weather.get('name', 'Unknown')
        country = weather.get('sys', {}).get('country', '')
        temp = weather.get('main', {}).get('temp', 0)
        feels_like = weather.get('main', {}).get('feels_like', 0)
        humidity = weather.get('main', {}).get('humidity', 0)
        pressure = weather.get('main', {}).get('pressure', 0)
        visibility = weather.get('visibility', 0) / 1000  # Convert to km
        wind_speed = weather.get('wind', {}).get('speed', 0)
        wind_deg = weather.get('wind', {}).get('deg', 0)
        
        weather_desc = weather.get('weather', [{}])[0]
        main_weather = weather_desc.get('main', 'Unknown')
        description = weather_desc.get('description', 'Unknown').title()
        
        # Get sunrise/sunset
        sunrise = datetime.fromtimestamp(weather.get('sys', {}).get('sunrise', 0))
        sunset = datetime.fromtimestamp(weather.get('sys', {}).get('sunset', 0))
        
        output = f"""
        
Current weather is as follows: 

Location: {location_name}, {country}
Temperature: {temp}°C (Feels like {feels_like}°C)
Condition: {description}
Humidity: {humidity}%
Pressure: {pressure} hPa
Visibility: {visibility:.1f} km
Wind: {wind_speed} m/s at {wind_deg} Degree
Sunrise: {sunrise.strftime("%H:%M")}
Sunset: {sunset.strftime("%H:%M")}
"""
        return output
    
    def format_forecast(self, data: Dict) -> str:
        """Format next day forecast"""
        if not data.get('forecast'):
            return "Forecast data not available"
        
        forecast_list = data['forecast'].get('list', [])
        if not forecast_list:
            return "No forecast data available"
        
        # Get tomorrow's forecasts (next 24 hours from now)
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        tomorrow_forecasts = []
        for item in forecast_list:
            forecast_time = datetime.fromtimestamp(item['dt'])
            if tomorrow_start <= forecast_time < tomorrow_end:
                tomorrow_forecasts.append(item)
        
        if not tomorrow_forecasts:
            # If no tomorrow data, get next available forecasts
            tomorrow_forecasts = forecast_list[:8]  # Next 24 hours (3-hour intervals)
        
        output = f"""
        
Here is the details for tomorrow's weather:

"""
        
        for forecast in tomorrow_forecasts[:4]:  # Show 4 time periods
            time_str = datetime.fromtimestamp(forecast['dt']).strftime("%H:%M")
            temp = forecast['main']['temp']
            description = forecast['weather'][0]['description'].title()
            humidity = forecast['main']['humidity']
            wind_speed = forecast['wind']['speed']
            
            output += f"""
  {time_str}: {temp}°C - {description}
   Humidity: {humidity}% | Wind: {wind_speed} m/s
"""
        
        return output
    
    def display_weather(self, location: str) -> bool:
        # Method for displaying weather report
        # Input Validation
        is_valid, location_type, normalized_location = self.validate_input(location)
        
        if not is_valid:
            print("Invalid input. Please enter a valid Indian city name or 6-digit pincode.")
            return False
        
        print(f"Fetching weather data for {normalized_location}...")
        
        # Fetch weather data
        weather_data = self.fetch_weather_data(normalized_location, location_type)
        
        if not weather_data:
            return False
        
        # Display current weather
        print(self.format_current_weather(weather_data))
        
        # Display forecast
        print(self.format_forecast(weather_data))
        
        # Show cache info
        fetched_time = datetime.fromisoformat(weather_data['fetched_at'])
        print(f"Data fetched at: {fetched_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return True

def main():
    # Function to run weather tool
    print("Welcome to Command Line Weather Tool for India!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Get API key
    api_key = input("Enter your OpenWeatherMap API key: ").strip()
    
    if not api_key:
        print("API key is required. Get one from https://openweathermap.org/api")
        return
    
    # Initialize weather tool
    weather_tool = WeatherTool(api_key)
    
    print("\n You can enter:")
    print("   • City names: Delhi, Mumbai, Bangalore, etc.")
    print("   • Pincodes: 110001, 400001, etc.")
    print("   • Type 'quit' or 'exit' to stop")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Main loop
    while True:
        try:
            location = input("\n Enter city name or pincode: ").strip()
            
            if location.lower() in ['quit', 'exit', 'q']:
                print(" Thank you for using Weather Tool!")
                break
            
            if not location:
                print("  Please enter a valid location.")
                continue
            
            success = weather_tool.display_weather(location)
            
            if success:
                weather_tool.cache.clear_expired()
                
                continue_choice = input("\n Check another location? (y/n): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    print("Thank you for using Weather Tool!")
                    break
            
        except KeyboardInterrupt:
            print("\n\n Weather Tool was interrupted.")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    main()
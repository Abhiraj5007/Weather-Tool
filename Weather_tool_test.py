import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests

# Import the classes from your weather tool
from weather import WeatherCache, WeatherTool


class TestWeatherCache:
    # Test cases for WeatherCache class
    
    def test_cache_initialization(self):
        # Test if cache initializes correctly
        cache = WeatherCache(expiry_minutes=10)
        assert cache.expiry_seconds == 600  # 10 minutes = 600 seconds
        assert cache.cache == {}
    
    def test_cache_set_and_get(self):
        # Test setting and getting data from cache
        cache = WeatherCache()
        test_data = {"temperature": 25, "humidity": 60}
        
        # Set data in cache
        cache.set("test_key", test_data)
        
        # Get data from cache
        retrieved_data = cache.get("test_key")
        assert retrieved_data == test_data
    
    def test_cache_expiry(self):
        # Test if cache expires correctly
        cache = WeatherCache(expiry_minutes=1)  # Very short expiry for testing
        test_data = {"temperature": 25}
        
        # Set data
        cache.set("test_key", test_data)
        
        # Should get data immediately
        assert cache.get("test_key") == test_data
        
        # Wait for expiry
        time.sleep(1)
        
        # Should return None after expiry
        assert cache.get("test_key") is None
    
    def test_cache_clear_expired(self):
        # Test clearing expired cache entries
        cache = WeatherCache(expiry_minutes=1)
        
        # Add some data
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        
        # Wait for expiry
        time.sleep(1)
        
        # Clear expired entries
        cache.clear_expired()
        
        # Cache should be empty
        assert len(cache.cache) == 0


class TestWeatherTool:
    # Test cases for WeatherTool class
    
    @pytest.fixture
    def weather_tool(self):
        # Create a WeatherTool instance for testing
        return WeatherTool("test_api_key")
    
    def test_weather_tool_initialization(self, weather_tool):
        # Test if WeatherTool initializes correctly
        assert weather_tool.api_key == "test_api_key"
        assert weather_tool.base_url == "http://api.openweathermap.org/data/2.5"
        assert isinstance(weather_tool.cache, WeatherCache)
        assert isinstance(weather_tool.session, requests.Session)
    
    def test_validate_input_pincode(self, weather_tool):
        is_valid, location_type, normalized = weather_tool.validate_input("110001")
        assert is_valid == True
        assert location_type == "pincode"
        assert normalized == "110001"
        
        is_valid, _, _ = weather_tool.validate_input("1100")
        assert is_valid == False
        
        is_valid, _, _ = weather_tool.validate_input("1100011")
        assert is_valid == False
    
    def test_validate_input_city(self, weather_tool):
        test_cases = [
            ("delhi", "city", "Delhi"),
            ("new delhi", "city", "New Delhi"),
            ("mumbai", "city", "Mumbai"),
            ("bangalore", "city", "Bengaluru"),
            ("random city", "city", "Random City")
        ]
        
        for input_city, expected_type, expected_name in test_cases:
            is_valid, location_type, normalized = weather_tool.validate_input(input_city)
            assert is_valid == True
            assert location_type == expected_type
            assert normalized == expected_name
    
    def test_validate_input_invalid(self, weather_tool):
        invalid_inputs = ["123abc", "!@#$%", "", "   "]
        
        for invalid_input in invalid_inputs:
            is_valid, _, _ = weather_tool.validate_input(invalid_input)
            assert is_valid == False
    
    def test_build_api_url_city(self, weather_tool):
        url = weather_tool.build_api_url("Delhi", "city", "weather")
        expected = "http://api.openweathermap.org/data/2.5/weather?q=Delhi,IN&appid=test_api_key&units=metric"
        assert url == expected
    
    def test_build_api_url_pincode(self, weather_tool):
        url = weather_tool.build_api_url("110001", "pincode", "forecast")
        expected = "http://api.openweathermap.org/data/2.5/forecast?zip=110001,IN&appid=test_api_key&units=metric"
        assert url == expected
    
    @patch('requests.Session.get')
    def test_fetch_weather_data_success(self, mock_get, weather_tool):
        # Mock response data
        current_data = {
            "name": "Delhi",
            "main": {"temp": 25, "humidity": 60},
            "weather": [{"main": "Clear", "description": "clear sky"}]
        }
        forecast_data = {
            "list": [
                {"dt": 1234567890, "main": {"temp": 26}, "weather": [{"description": "sunny"}]}
            ]
        }
        
        # Mock responses
        mock_current_response = Mock()
        mock_current_response.status_code = 200
        mock_current_response.json.return_value = current_data
        
        mock_forecast_response = Mock()
        mock_forecast_response.status_code = 200
        mock_forecast_response.json.return_value = forecast_data
        
        mock_get.side_effect = [mock_current_response, mock_forecast_response]
        
        # Test the method
        result = weather_tool.fetch_weather_data("Delhi", "city")
        
        assert result is not None
        assert result["current"] == current_data
        assert result["forecast"] == forecast_data
        assert "fetched_at" in result
    
    @patch('requests.Session.get')
    def test_fetch_weather_data_not_found(self, mock_get, weather_tool):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = weather_tool.fetch_weather_data("InvalidCity", "city")
        assert result is None
    
    @patch('requests.Session.get')
    def test_fetch_weather_data_invalid_api_key(self, mock_get, weather_tool):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = weather_tool.fetch_weather_data("Delhi", "city")
        assert result is None
    
    @patch('requests.Session.get')
    def test_fetch_weather_data_timeout(self, mock_get, weather_tool):
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = weather_tool.fetch_weather_data("Delhi", "city")
        assert result is None
    
    @patch('requests.Session.get')
    def test_fetch_weather_data_connection_error(self, mock_get, weather_tool):
        # Test weather data fetching connection error
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = weather_tool.fetch_weather_data("Delhi", "city")
        assert result is None
    
    def test_format_current_weather(self, weather_tool):
        # Test current weather formatting
        # Sample weather data
        weather_data = {
            "current": {
                "name": "Delhi",
                "sys": {"country": "IN", "sunrise": 1234567890, "sunset": 1234567890},
                "main": {
                    "temp": 25.5,
                    "feels_like": 27.2,
                    "humidity": 65,
                    "pressure": 1013
                },
                "weather": [{"main": "Clear", "description": "clear sky"}],
                "visibility": 10000,
                "wind": {"speed": 3.5, "deg": 180}
            }
        }
        
        result = weather_tool.format_current_weather(weather_data)
        
        assert "Delhi" in result
        assert "25.5°C" in result
        assert "27.2°C" in result
        assert "65%" in result
        assert "1013 hPa" in result
        assert "Clear Sky" in result
    
    def test_format_forecast(self, weather_tool):
        # Test forecast formatting
        # Sample forecast data
        tomorrow = datetime.now() + timedelta(days=1)
        forecast_time = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
        
        weather_data = {
            "forecast": {
                "list": [
                    {
                        "dt": int(forecast_time.timestamp()),
                        "main": {"temp": 28, "humidity": 70},
                        "weather": [{"description": "partly cloudy"}],
                        "wind": {"speed": 4.2}
                    }
                ]
            }
        }
        
        result = weather_tool.format_forecast(weather_data)
        
        assert "tomorrow's weather" in result
        assert "28°C" in result
        assert "70%" in result
        assert "4.2 m/s" in result
    
    def test_format_forecast_no_data(self, weather_tool):
        # Test forecast formatting when no data available
        weather_data = {"forecast": None}
        result = weather_tool.format_forecast(weather_data)
        assert "not available" in result
    
    @patch.object(WeatherTool, 'fetch_weather_data')
    def test_display_weather_success(self, mock_fetch, weather_tool):
        # Test successful weather display
        # Mock weather data
        mock_data = {
            "current": {
                "name": "Delhi",
                "sys": {"country": "IN", "sunrise": 1234567890, "sunset": 1234567890},
                "main": {"temp": 25, "feels_like": 27, "humidity": 65, "pressure": 1013},
                "weather": [{"main": "Clear", "description": "clear sky"}],
                "visibility": 10000,
                "wind": {"speed": 3.5, "deg": 180}
            },
            "forecast": {"list": []},
            "fetched_at": datetime.now().isoformat()
        }
        
        mock_fetch.return_value = mock_data
        
        result = weather_tool.display_weather("Delhi")
        assert result == True
    
    @patch.object(WeatherTool, 'fetch_weather_data')
    def test_display_weather_invalid_input(self, mock_fetch, weather_tool):
        # Test weather display with invalid input
        result = weather_tool.display_weather("!@#$%")
        assert result == False
        mock_fetch.assert_not_called()
    
    @patch.object(WeatherTool, 'fetch_weather_data')
    def test_display_weather_no_data(self, mock_fetch, weather_tool):
        # Test weather display when no data is fetched
        mock_fetch.return_value = None
        
        result = weather_tool.display_weather("Delhi")
        assert result == False


# Integration tests
class TestWeatherToolIntegration:
    # Integration tests for the weather tool
    
    @pytest.fixture
    def weather_tool(self):
        return WeatherTool("test_api_key")
    
    def test_cache_integration(self, weather_tool):
        # Test that caching works correctly with the weather tool
        # Mock the first API call
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"name": "Delhi", "main": {"temp": 25}}
            mock_get.return_value = mock_response
            
            # First call should hit the API
            result1 = weather_tool.fetch_weather_data("Delhi", "city")
            assert mock_get.call_count == 2  # Current + forecast
            
            # Second call should use cache
            result2 = weather_tool.fetch_weather_data("Delhi", "city")
            assert mock_get.call_count == 2  # No additional calls
            
            # Results should be the same
            assert result1 == result2


# Fixtures for common test data
@pytest.fixture
def sample_weather_response():
    # Sample weather API response
    return {
        "name": "Delhi",
        "sys": {"country": "IN", "sunrise": 1234567890, "sunset": 1234567890},
        "main": {
            "temp": 25.5,
            "feels_like": 27.2,
            "humidity": 65,
            "pressure": 1013
        },
        "weather": [{"main": "Clear", "description": "clear sky"}],
        "visibility": 10000,
        "wind": {"speed": 3.5, "deg": 180}
    }


@pytest.fixture
def sample_forecast_response():
    # Sample forecast API response
    return {
        "list": [
            {
                "dt": int((datetime.now() + timedelta(days=1)).timestamp()),
                "main": {"temp": 28, "humidity": 70},
                "weather": [{"description": "partly cloudy"}],
                "wind": {"speed": 4.2}
            }
        ]
    }


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
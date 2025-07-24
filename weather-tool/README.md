# Command Line Weather Tool

This project is a command line weather tool that allows users to fetch current weather information and forecasts for cities in India using the OpenWeatherMap API. The tool supports both city names and Indian pincodes as input.

## Features

- Fetch current weather data and 5-day forecasts.
- Caching mechanism to reduce API calls and improve performance.
- Input validation for city names and pincodes.
- User-friendly output formatting for easy reading.

## Requirements

- Python 3.x
- `requests` library (install via `pip install requests`)

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd weather-tool
   ```

2. Install the required libraries:
   ```
   pip install requests
   ```

3. Obtain an API key from [OpenWeatherMap](https://openweathermap.org/api).

## Usage

1. Run the tool:
   ```
   python weather.py
   ```

2. Enter your OpenWeatherMap API key when prompted.

3. Input a city name (e.g., "Delhi") or a 6-digit pincode (e.g., "110001") to fetch the weather data.

4. To exit the tool, type `quit` or `exit`.

## Example

```
Welcome to Command Line Weather Tool for India!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter your OpenWeatherMap API key: <your_api_key>

You can enter:
   • City names: Delhi, Mumbai, Bangalore, etc.
   • Pincodes: 110001, 400001, etc.
   • Type 'quit' or 'exit' to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enter city name or pincode: Delhi
Fetching weather data for New Delhi...
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
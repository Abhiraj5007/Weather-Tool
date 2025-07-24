# Weather Tool

A simple **Command Line Weather Tool** for India, built with Python.  
Get current weather and next-day forecast for any Indian city or 6-digit pincode using the [OpenWeatherMap API](https://openweathermap.org/api).

---

## Features

- Current weather details (temperature, humidity, wind, etc.)
- Tomorrow's forecast (in 3-hour intervals)
- Supports Indian city names and 6-digit pincodes
- Caching for faster repeated queries
- Error handling for invalid input, API errors, and network issues

---

## Requirements

- Python 3.7+
- `requests` library

Install dependencies:
```sh
pip install requests
```

---

## Usage

1. **Get your free API key** from [OpenWeatherMap](https://openweathermap.org/api).
2. **Run the tool:**
   ```sh
   python weather.py
   ```
3. **Enter your API key** when prompted.
4. **Enter a city name** (e.g. `Delhi`, `Mumbai`) **or a 6-digit pincode** (e.g. `110001`).

---

## Example

```
Welcome to Command Line Weather Tool for India!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enter your OpenWeatherMap API key: <your-api-key>

You can enter:
   • City names: Delhi, Mumbai, Bangalore, etc.
   • Pincodes: 110001, 400001, etc.
   • Type 'quit' or 'exit' to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enter city name or pincode: Delhi

Fetching weather data for Delhi...

Current weather is as follows: 
Location: Delhi, IN
Temperature: 34°C (Feels like 36°C)
Condition: Clear Sky
Humidity: 45%
...
```

---

## Testing

Run unit tests (if available):

```sh
pytest Weather_tool_test.py
```

---

## Notes

- Only works for Indian cities and pincodes.
- API key is required for every session.
- Cached data expires after 5 minutes by default.

---

## License

This project is for educational purposes.

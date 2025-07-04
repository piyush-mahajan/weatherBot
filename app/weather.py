import httpx
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_weather(city: str) -> str:
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Fetching weather for city: {city}")
            response = await client.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            )
            response.raise_for_status()
            data = response.json()
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            logger.info(f"Weather data for {city}: {weather}, {temp}°C")
            return f"Weather in {city}: {weather}, Temperature: {temp}°C"
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather for {city}: {str(e)}")
            return f"Error: Could not fetch weather for {city}. Please check the city name."
        except Exception as e:
            logger.error(f"Error fetching weather for {city}: {str(e)}")
            return f"Error: {str(e)}"
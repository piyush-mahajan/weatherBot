# PrabhatWeatherBot

A Telegram bot ([@PrabhatWeatherBot](https://t.me/PrabhatWeatherBot)) that provides weather updates for multiple cities, with subscription-based periodic updates and an admin panel for user management. Built with FastAPI, MongoDB Atlas, and the OpenWeatherMap API, it supports subscribing, querying weather for cities, retrieving weather history, and unsubscribing. The bot is deployed on Render with a webhook for real-time Telegram updates, using ngrok for local testing.

## Features

- **Subscribe/Unsubscribe**: Users can subscribe to receive periodic weather updates or unsubscribe to stop them.
- **Multiple City Support**: Subscribed users can query weather for multiple cities (e.g., Mumbai, Pune, Delhi) without needing to unsubscribe.
- **Weather History**: The "Get Weather" button retrieves weather data for all previously queried cities.
- **Periodic Updates**: Subscribed users receive weather updates for all saved cities every 6 hours.
- **Admin Panel**: A web interface (`/admin`) allows managing users (view, block/unblock, delete) and updating API keys.
- **MongoDB Integration**: Stores user data, including subscription status and city history.
- **Logging**: Comprehensive logs for debugging and monitoring.

## Tech Stack

- **Backend**: FastAPI (Python) for the API and webhook handling.
- **Telegram Bot**: `python-telegram-bot` v20.8 for Telegram interactions.
- **Database**: MongoDB Atlas for storing user data and city history.
- **Weather API**: OpenWeatherMap for real-time weather data.
- **Deployment**: Render for hosting, ngrok for local webhook testing.
- **Dependencies**: Managed with `uv` for efficient package management.

## Prerequisites

- Python 3.8+
- MongoDB Atlas account with a database named `weather_bot`.
- OpenWeatherMap API key ([sign up](https://openweathermap.org/api)).
- Telegram Bot Token (create via [BotFather](https://t.me/BotFather)).
- ngrok for local webhook testing ([download](https://ngrok.com/)).
- Render account for deployment ([sign up](https://render.com/)).

## Setup Instructions

### Clone the Repository

```bash
git clone https://github.com/yourusername/telegram-weather-bot.git
cd telegram-weather-bot
```

### Install Dependencies

1. Install `uv` for dependency management:

   ```bash
   pip install uv
   ```

2. Install project dependencies:

   ```bash
   uv pip install -r requirements.txt
   ```

### Configure Environment Variables

Create a `.env` file in the project root:

```plaintext
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/weather_bot?retryWrites=true&w=majority
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
WEBHOOK_URL=https://your-ngrok-or-render-url/telegram-webhook
```

Replace placeholders with your actual credentials:
- `TELEGRAM_BOT_TOKEN`: From BotFather.
- `OPENWEATHERMAP_API_KEY`: From OpenWeatherMap.
- `MONGO_URI`: From MongoDB Atlas (ensure IP whitelist includes `0.0.0.0/0` for testing).
- `WEBHOOK_URL`: ngrok URL (local) or Render URL (deployed).

### Run Locally

1. Start the FastAPI server:

   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Set up ngrok for webhook testing:

   ```bash
   uv run ngrok http 8000
   ```

   Copy the ngrok URL (e.g., `https://9443-2402-8100-2453-fbef-68c7-771c-e4a0-fd17.ngrok-free.app`) and update `WEBHOOK_URL` in `.env`.

3. Set the Telegram webhook:

   ```bash
   curl -F "url=$WEBHOOK_URL" https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook
   ```

### Test the Bot

1. Open Telegram and start a chat with [@PrabhatWeatherBot](https://t.me/PrabhatWeatherBot).
2. Send `/start` to see the welcome message with buttons (Subscribe, Unsubscribe, Get Weather).
3. Test features:
   - Click "Subscribe" and send a city (e.g., "Mumbai") to get weather.
   - Send another city (e.g., "Pune") to add to history and get weather.
   - Click "Get Weather" to see weather for all queried cities.
   - Click "Unsubscribe" to stop updates.
4. Check server logs in the terminal for debugging.

### Test Admin Panel

1. Visit `http://localhost:8000/admin`.
2. Log in with `ADMIN_USERNAME` (admin) and `ADMIN_PASSWORD`.
3. Verify:
   - View user data (chat ID, city history, subscription status, block status).
   - Block/unblock or delete users.
   - Update Telegram and OpenWeatherMap API keys.

## Deployment on Render

### Prepare the Repository

1. Ensure `.gitignore` includes:

   ```plaintext
   .env
   .venv/
   __pycache__/
   *.pyc
   ```

2. Update `requirements.txt`:

   ```bash
   uv pip freeze > requirements.txt
   ```

3. Push changes to GitHub:

   ```bash
   git add .
   git commit -m "Prepared for Render deployment"
   git push origin main
   ```

### Create a Render Web Service

1. Log in to [Render](https://render.com/).
2. Create a new Web Service, selecting your GitHub repository.
3. Configure:
   - **Environment**: Python
   - **Build Command**: `uv pip install -r requirements.txt`
   - **Start Command**: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     ```plaintext
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token
     OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
     MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/weather_bot?retryWrites=true&w=majority
     ADMIN_USERNAME=admin
     ADMIN_PASSWORD=your_secure_password
     WEBHOOK_URL=https://your-service.onrender.com/telegram-webhook
     ```
4. Deploy and note the Render URL (e.g., `https://your-service.onrender.com`).

5. Set Telegram webhook:

   ```bash
   curl -F "url=https://your-service.onrender.com/telegram-webhook" https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook
   ```

## Usage

### Bot Commands

- `/start`: Displays a welcome message with buttons (Subscribe, Unsubscribe, Get Weather).
- **Subscribe**: Enables sending city names to get weather updates and adds cities to history.
- **Unsubscribe**: Stops periodic weather updates but retains city history for future subscriptions.
- **Get Weather**: Retrieves weather for all cities in the user's history.
- **Send a city name** (e.g., "Mumbai", "Pune") while subscribed to get immediate weather updates.

### Admin Panel

- Access at `http://localhost:8000/admin` (local) or `https://your-service.onrender.com/admin` (deployed).
- Log in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
- Features:
  - View user list (chat ID, city history, subscription status, block status).
  - Block/unblock or delete users.
  - Update Telegram and OpenWeatherMap API keys.

## Database Schema

The `weather_bot` database in MongoDB Atlas has a `users` collection with the following schema:

```json
{
  "chat_id": "string",
  "city_history": ["string"],
  "is_subscribed": boolean,
  "is_blocked": boolean
}
```

- `chat_id`: Telegram chat ID (e.g., "1816533248").
- `city_history`: List of cities the user has queried (e.g., ["Mumbai", "Pune"]).
- `is_subscribed`: Whether the user is subscribed to periodic updates.
- `is_blocked`: Whether the user is blocked from receiving updates.

## Troubleshooting

### Bot Not Responding

- Check server logs (uvicorn terminal) for errors.
- Verify ngrok logs (`http://127.0.0.1:4040`) for webhook requests.
- Ensure `TELEGRAM_BOT_TOKEN` and `WEBHOOK_URL` are correct:
  ```bash
  curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo
  ```

### Invalid Weather Data

- Verify `OPENWEATHERMAP_API_KEY`:
  ```bash
  curl "http://api.openweathermap.org/data/2.5/weather?q=Mumbai&appid=$OPENWEATHERMAP_API_KEY&units=metric"
  ```
- Ensure city names are valid (e.g., "Mumbai", not "mumbay").

### MongoDB Issues

- Confirm `MONGO_URI` credentials and IP whitelist (`0.0.0.0/0` for testing).
- Check the `users` collection in MongoDB Atlas for correct data.

### Admin Panel Errors

- Ensure correct URL (`http://localhost:8000/admin` or deployed URL).
- Check logs for database or authentication errors.



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For issues or questions, contact [piyush Mahajan] on GitHub or interact with [@PrabhatWeatherBot](https://t.me/PrabhatWeatherBot) on Telegram.